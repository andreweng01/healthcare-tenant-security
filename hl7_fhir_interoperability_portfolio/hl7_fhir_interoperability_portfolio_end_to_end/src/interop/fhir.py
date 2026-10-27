"""Minimal FHIR R4 resource mapping and structural checks."""
from datetime import datetime
from typing import Any, Dict, List
from .hl7 import HL7Error, ParsedMessage, field, component

def _required(value: str, label: str) -> str:
    if not value.strip():
        raise HL7Error(f"Required field is missing: {label}.")
    return value.strip()

def _date(value: str, label: str) -> str:
    value = _required(value, label)
    try:
        if len(value) >= 14:
            dt = datetime.strptime(value[:14], "%Y%m%d%H%M%S")
        elif len(value) >= 8:
            dt = datetime.strptime(value[:8], "%Y%m%d")
        else:
            raise ValueError
        return dt.isoformat() + ("Z" if len(value) >= 14 else "")
    except ValueError:
        raise HL7Error(f"Invalid date/time in {label}; expected YYYYMMDD or YYYYMMDDHHMMSS.")

def _patient(pid: str, name: str, birth: str = "", sex: str = "") -> Dict[str, Any]:
    family = component(name, 1)
    given = component(name, 2)
    resource: Dict[str, Any] = {
        "resourceType": "Patient",
        "identifier": [{"system": "urn:example:hl7v2:patient-id", "value": pid}],
        "name": [{"family": family, "given": [given] if given else []}],
    }
    if birth:
        resource["birthDate"] = _date(birth, "PID-7")[:10]
    if sex and sex in {"M", "F", "O", "U", "A", "N"}:
        resource["gender"] = {"M":"male","F":"female","O":"other","U":"unknown","A":"other","N":"unknown"}[sex]
    return resource

def map_to_fhir(msg: ParsedMessage) -> List[Dict[str, Any]]:
    pid_seg = msg.segments.get("PID", [])
    if not pid_seg:
        raise HL7Error("Required segment is missing: PID.")
    pid_value = field(msg, "PID", 0, 3)
    patient_id = component(pid_value, 1) if "^" in pid_value else pid_value
    _required(patient_id, "PID-3 patient identifier")
    name = field(msg, "PID", 0, 5)
    _required(name, "PID-5 patient name")
    birth = field(msg, "PID", 0, 7)
    sex = field(msg, "PID", 0, 8)
    patient = _patient(patient_id, name, birth, sex)

    if msg.message_type.startswith("ADT^A01"):
        pv1 = msg.segments.get("PV1", [])
        if not pv1:
            raise HL7Error("ADT^A01 requires a PV1 segment.")
        visit_id = field(msg, "PV1", 0, 19)
        visit_id = (component(visit_id, 1) if "^" in visit_id else visit_id)
        _required(visit_id, "PV1-19 visit number")
        admit = field(msg, "PV1", 0, 44)
        encounter: Dict[str, Any] = {
            "resourceType": "Encounter",
            "status": "in-progress",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP"},
            "identifier": [{"system": "urn:example:hl7v2:visit-id", "value": visit_id}],
            "subject": {"reference": "Patient/" + patient_id},
        }
        if admit:
            encounter["period"] = {"start": _date(admit, "PV1-44")}
        validate_fhir_resource(patient)
        validate_fhir_resource(encounter)
        return [patient, encounter]

    if msg.message_type.startswith("ORU^R01"):
        obx_rows = msg.segments.get("OBX", [])
        if not obx_rows:
            raise HL7Error("ORU^R01 requires at least one OBX segment.")
        obx = obx_rows[0]
        code = field(msg, "OBX", 0, 3)
        value_type = field(msg, "OBX", 0, 2)
        value = field(msg, "OBX", 0, 5)
        _required(code, "OBX-3 observation identifier")
        _required(value_type, "OBX-2 value type")
        _required(value, "OBX-5 observation value")
        observation: Dict[str, Any] = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": component(code, 2) or component(code, 1) or code},
            "subject": {"reference": "Patient/" + patient_id},
            "valueString": value,
        }
        if field(msg, "OBX", 0, 6):
            observation["note"] = [{"text": "HL7 source units: " + field(msg, "OBX", 0, 6)}]
        if field(msg, "OBX", 0, 14):
            observation["effectiveDateTime"] = _date(field(msg, "OBX", 0, 14), "OBX-14")
        validate_fhir_resource(patient)
        validate_fhir_resource(observation)
        return [patient, observation]

    raise HL7Error(f"Unsupported message type: {msg.message_type}. Supported types: ADT^A01 and ORU^R01.")

def validate_fhir_resource(resource: Dict[str, Any]) -> None:
    """Small local guardrail; not a substitute for official FHIR validation."""
    rt = resource.get("resourceType")
    if rt == "Patient":
        if not resource.get("identifier") or not resource.get("name"):
            raise HL7Error("Generated Patient must include identifier and name.")
    elif rt == "Encounter":
        if resource.get("status") not in {"planned","in-progress","on-hold","discharged","completed","cancelled","discontinued","entered-in-error","unknown"}:
            raise HL7Error("Encounter.status is not a recognized R4 value.")
        if not resource.get("subject", {}).get("reference", "").startswith("Patient/"):
            raise HL7Error("Encounter.subject must reference a Patient.")
    elif rt == "Observation":
        if resource.get("status") not in {"registered","preliminary","final","amended","corrected","cancelled","entered-in-error","unknown"}:
            raise HL7Error("Observation.status is not a recognized R4 value.")
        if not resource.get("subject", {}).get("reference", "").startswith("Patient/"):
            raise HL7Error("Observation.subject must reference a Patient.")
        if not resource.get("code") or not (resource.get("valueString") or resource.get("valueQuantity") or resource.get("valueCodeableConcept")):
            raise HL7Error("Observation requires code and a value[x].")
    else:
        raise HL7Error(f"Unsupported generated FHIR resourceType: {rt}.")
