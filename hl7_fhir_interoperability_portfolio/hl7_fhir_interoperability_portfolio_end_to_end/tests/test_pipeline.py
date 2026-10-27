import pytest
from fastapi.testclient import TestClient
from src.app import app
from src.interop.pipeline import process_message
from src.interop.store import MessageStore
from src.interop.hl7 import parse_hl7, HL7Error
from src.interop.fhir import map_to_fhir

ADT = "MSH|^~\\&|APP|FAC|DEST|FAC|20260115103000||ADT^A01|T-ADT-1|P|2.5\rPID|1||P-1^^^APP^MR||DOE^JANE||19850312|F\rPV1|1|I|||||||||||||||||V-1|||||||||||||||||||||||20260115103000\r"
ORU = "MSH|^~\\&|APP|FAC|DEST|FAC|20260115103000||ORU^R01|T-ORU-1|P|2.5\rPID|1||P-1^^^APP^MR||DOE^JANE||19850312|F\rOBR|1||ORD-1|718-7^Hemoglobin^LN\rOBX|1|NM|718-7^Hemoglobin^LN||13.4|g/dL|12.0-16.0|N|||F|||20260115104000\r"

def test_parse_message_header():
    msg = parse_hl7(ADT)
    assert msg.message_type == "ADT^A01"
    assert msg.control_id == "T-ADT-1"

def test_adt_maps_patient_and_encounter():
    resources = map_to_fhir(parse_hl7(ADT))
    assert [r["resourceType"] for r in resources] == ["Patient", "Encounter"]
    assert resources[1]["subject"]["reference"] == "Patient/P-1"

def test_oru_maps_patient_and_observation():
    resources = map_to_fhir(parse_hl7(ORU))
    assert [r["resourceType"] for r in resources] == ["Patient", "Observation"]
    assert resources[1]["subject"]["reference"] == "Patient/P-1"
    assert resources[1]["valueString"] == "13.4"

def test_rejects_empty_and_missing_msh():
    with pytest.raises(HL7Error):
        parse_hl7("")
    with pytest.raises(HL7Error):
        parse_hl7("PID|1||P-1")

def test_rejects_missing_patient_id():
    bad = ADT.replace("P-1^^^APP^MR", "^^^^")
    result = process_message(bad, MessageStore(":memory:"))
    assert result["status"] == "REJECTED"
    assert "patient identifier" in result["error"]

def test_rejects_unsupported_type():
    msg = ADT.replace("ADT^A01", "ADT^A08")
    result = process_message(msg, MessageStore(":memory:"))
    assert result["status"] == "REJECTED"
    assert "Unsupported message type" in result["error"]

def test_duplicate_control_id_is_idempotent():
    store = MessageStore(":memory:")
    first = process_message(ADT, store)
    second = process_message(ADT, store)
    assert first["status"] == "PROCESSED"
    assert second["status"] == "DUPLICATE"

def test_missing_pv1_rejected():
    bad = ADT.replace("PV1|1|I|||||||||||||||||V-1|||||||||||||||||||||||20260115103000\r", "")
    result = process_message(bad, MessageStore(":memory:"))
    assert result["status"] == "REJECTED"
    assert "PV1 segment" in result["error"]

def test_missing_obx_value_rejected():
    bad = ORU.replace("||13.4|g/dL", "|||g/dL")
    result = process_message(bad, MessageStore(":memory:"))
    assert result["status"] == "REJECTED"
    assert "OBX-5" in result["error"]

def test_http_ingestion_endpoint():
    client = TestClient(app)
    response = client.post("/hl7", content=ADT, headers={"Content-Type": "text/plain"})
    assert response.status_code == 200
    assert response.json()["status"] in {"PROCESSED", "DUPLICATE"}
