"""Educational HL7 v2 to FHIR R4 mapping pipeline."""
from datetime import datetime
from typing import Any, Dict, List

from .hl7 import HL7Message, HL7ParseError, field, parse_message
from .fhir import validate_resource


class MappingError(ValueError):
    pass


def _required(value: str, label: str) -> str:
    value = (value or "").strip()
    if not value:
        raise MappingError(f"Required HL7 field is missing: {label}")
    return value


def _date_yyyymmdd(value: str) -> str | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:8], "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def _map_gender(value: str) -> str | None:
    return {"M": "male", "F": "female", "O": "other", "U": "unknown"}.get(value.upper())


def _message_type(message: HL7Message) -> str:
    msh = message.first("MSH")
    return field(msh, 9, 1) + "^" + field(msh, 9, 2)


def _patient(message: HL7Message) -> Dict[str, Any]:
    pid = message.first("PID")
    patient_id = _required(field(pid, 3, 1), "PID-3 patient identifier")
    patient: Dict[str, Any] = {
        "resourceType": "Patient",
        "identifier": [{"system": "urn:example:hl7-patient-id", "value": patient_id}],
    }
    family = field(pid, 5, 1)
    given = field(pid, 5, 2)
    if family or given:
        name: Dict[str, Any] = {}
        if family:
            name["family"] = family
        if given:
            name["given"] = [given]
        patient["name"] = [name]
    birth_date = _date_yyyymmdd(field(pid, 7))
    if birth_date:
        patient["birthDate"] = birth_date
    gender = _map_gender(field(pid, 8))
    if gender:
        patient["gender"] = gender
    validate_resource(patient)
    return patient


def _encounter(message: HL7Message, patient_id: str) -> Dict[str, Any]:
    pv1 = message.first("PV1")
    patient_class = field(pv1, 2).upper()
    class_codes = {"I": ("IMP", "inpatient encounter"), "O": ("AMB", "ambulatory"), "E": ("EMER", "emergency")}
    code, display = class_codes.get(patient_class, ("OTH", "other encounter"))
    visit_number = field(pv1, 19)
    encounter: Dict[str, Any] = {
        "resourceType": "Encounter",
        "status": "in-progress",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": code, "display": display},
        "subject": {"reference": f"Patient/{patient_id}"},
    }
    if visit_number:
        encounter["identifier"] = [{"system": "urn:example:hl7-visit-number", "value": visit_number}]
    validate_resource(encounter)
    return encounter


def _observation(message: HL7Message, patient_id: str) -> Dict[str, Any]:
    obx = message.first("OBX")
    code = _required(field(obx, 3, 1), "OBX-3 observation code")
    display = field(obx, 3, 2)
    value = _required(field(obx, 5), "OBX-5 observation value")
    units = field(obx, 6)
    observation: Dict[str, Any] = {
        "resourceType": "Observation",
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {
            "coding": [{"system": "urn:example:hl7-observation-code", "code": code}],
            "text": display or code,
        },
        "valueString": value,
    }
    if units:
        # This lab preserves the value as a string and units as text; numeric Quantity conversion is a future extension.
        observation["note"] = [{"text": f"Source units: {units}"}]
    effective = field(obx, 14)
    if effective:
        try:
            observation["effectiveDateTime"] = datetime.strptime(effective[:14], "%Y%m%d%H%M%S").isoformat()
        except ValueError:
            pass
    validate_resource(observation)
    return observation


def process_hl7(raw: str) -> Dict[str, Any]:
    message = parse_message(raw)
    msh = message.first("MSH")
    message_control_id = _required(field(msh, 10), "MSH-10 message control ID")
    message_type = _message_type(message)

    if message_type == "ADT^A01":
        patient = _patient(message)
        encounter = _encounter(message, patient["identifier"][0]["value"])
        return {
            "messageControlId": message_control_id,
            "messageType": message_type,
            "resources": [patient, encounter],
        }

    if message_type == "ORU^R01":
        patient = _patient(message)
        observation = _observation(message, patient["identifier"][0]["value"])
        return {
            "messageControlId": message_control_id,
            "messageType": message_type,
            "resources": [patient, observation],
        }

    raise MappingError(f"Unsupported message type: {message_type}")
