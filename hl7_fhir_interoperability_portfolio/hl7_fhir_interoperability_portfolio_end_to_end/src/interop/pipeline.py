"""End-to-end processing orchestration."""
from typing import Any, Dict
from .hl7 import HL7Error, parse_hl7
from .fhir import map_to_fhir
from .store import MessageStore

def process_message(raw: str, store: MessageStore) -> Dict[str, Any]:
    parsed = None
    # Parse first so the control ID can be used for idempotency/audit.
    try:
        parsed = parse_hl7(raw)
    except HL7Error as exc:
        return {"status": "REJECTED", "control_id": None, "message_type": None,
                "error": str(exc), "resources": []}

    previous = store.get(parsed.control_id)
    if previous:
        return {"status": "DUPLICATE", "control_id": parsed.control_id,
                "message_type": parsed.message_type,
                "error": None, "resources": [],
                "original_status": previous["status"]}

    try:
        resources = map_to_fhir(parsed)
        inserted = store.record(parsed.control_id, parsed.message_type, "PROCESSED", resources=resources)
        if not inserted:
            previous = store.get(parsed.control_id)
            return {"status": "DUPLICATE", "control_id": parsed.control_id,
                    "message_type": parsed.message_type, "error": None, "resources": [],
                    "original_status": previous["status"] if previous else "UNKNOWN"}
        return {"status": "PROCESSED", "control_id": parsed.control_id,
                "message_type": parsed.message_type, "error": None, "resources": resources}
    except HL7Error as exc:
        store.record(parsed.control_id, parsed.message_type, "REJECTED", error=str(exc))
        return {"status": "REJECTED", "control_id": parsed.control_id,
                "message_type": parsed.message_type, "error": str(exc), "resources": []}
