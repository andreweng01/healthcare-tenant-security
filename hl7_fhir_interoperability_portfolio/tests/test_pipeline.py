from pathlib import Path
import json
import pytest

from interop.hl7 import HL7ParseError, parse_message
from interop.pipeline import MappingError, process_hl7
from interop.fhir import FHIRValidationError, validate_resource
from interop.idempotency import DuplicateMessageError, IdempotencyStore

ROOT = Path(__file__).resolve().parents[1]


def sample(name):
    return (ROOT / "samples" / "hl7v2" / name).read_text(encoding="utf-8")


def test_parse_standard_cr_separated_message():
    msg = parse_message(sample("adt_a01.hl7"))
    assert msg.first("MSH").name == "MSH"
    assert msg.first("PID").name == "PID"


def test_adt_maps_to_patient_and_encounter():
    result = process_hl7(sample("adt_a01.hl7"))
    assert result["messageType"] == "ADT^A01"
    patient, encounter = result["resources"]
    assert patient["resourceType"] == "Patient"
    assert patient["identifier"][0]["value"] == "P12345"
    assert patient["birthDate"] == "1985-05-14"
    assert patient["gender"] == "female"
    assert encounter["resourceType"] == "Encounter"
    assert encounter["class"]["code"] == "IMP"


def test_oru_maps_to_patient_and_observation():
    result = process_hl7(sample("oru_r01.hl7"))
    patient, observation = result["resources"]
    assert patient["identifier"][0]["value"] == "P12345"
    assert observation["resourceType"] == "Observation"
    assert observation["status"] == "final"
    assert observation["valueString"] == "13.8"
    assert "g/dL" in observation["note"][0]["text"]


def test_rejects_empty_message():
    with pytest.raises(HL7ParseError):
        parse_message("")


def test_rejects_non_msh_first_segment():
    with pytest.raises(HL7ParseError):
        parse_message("PID|1||P12345")


def test_rejects_missing_patient_identifier():
    raw = "MSH|^~\\&|APP|FAC|DEST|FAC|20261027103000||ADT^A01|X1|P|2.5\rPID|1||||DOE^JANE\rPV1|1|I\r"
    with pytest.raises(ValueError, match="PID-3"):
        process_hl7(raw)


def test_rejects_unsupported_message_type():
    raw = "MSH|^~\\&|APP|FAC|DEST|FAC|20261027103000||ORM^O01|X2|P|2.5\r"
    with pytest.raises(MappingError, match="Unsupported message type"):
        process_hl7(raw)


def test_fhir_patient_requires_identifier():
    with pytest.raises(FHIRValidationError):
        validate_resource({"resourceType": "Patient"})


def test_duplicate_control_id_is_rejected():
    store = IdempotencyStore()
    store.claim("MSG0001")
    with pytest.raises(DuplicateMessageError):
        store.claim("MSG0001")


def test_different_control_ids_are_allowed():
    store = IdempotencyStore()
    store.claim("MSG0001")
    store.claim("MSG0002")
