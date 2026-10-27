from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass(frozen=True)
class ParsedMessage:
    source_system: str
    message_type: str
    control_id: str
    raw: str

@dataclass
class LedgerEntry:
    status: str
    attempts: int = 0
    last_error: str = ""

def parse_minimal(raw: str) -> ParsedMessage:
    """Limited teaching parser; not a complete HL7 v2 parser."""
    raw = raw.replace("\r\n", "\r").strip("\r\n")
    segments = [s for s in raw.split("\r") if s]
    if not segments or not segments[0].startswith("MSH|"):
        raise ValueError("Missing MSH segment")
    fields = segments[0].split("|")
    if len(fields) < 10:
        raise ValueError("MSH segment has too few fields")
    source, msg_type, control_id = fields[2], fields[8], fields[9]
    if not source or not msg_type or not control_id:
        raise ValueError("Missing required MSH-3, MSH-9, or MSH-10")
    if msg_type == "ADT^A01^ADT_A01":
        required = {"PID", "PV1"}
    elif msg_type == "ORU^R01^ORU_R01":
        required = {"PID", "OBR", "OBX"}
    else:
        raise ValueError("Unsupported message type: " + msg_type)
    present = {s.split("|", 1)[0] for s in segments}
    missing = required - present
    if missing:
        raise ValueError("Missing required segments: " + ",".join(sorted(missing)))
    return ParsedMessage(source, msg_type, control_id, raw)

class MessageLedger:
    """In-memory behavior demo; production requires durable transactional storage."""
    def __init__(self):
        self.entries: Dict[Tuple[str, str], LedgerEntry] = {}

    def begin(self, message: ParsedMessage) -> str:
        key = (message.source_system, message.control_id)
        if key in self.entries:
            return "DUPLICATE"
        self.entries[key] = LedgerEntry("PROCESSING", attempts=1)
        return "ACCEPTED"

    def mark_success(self, message: ParsedMessage):
        self.entries[(message.source_system, message.control_id)].status = "PROCESSED"

    def mark_failure(self, message: ParsedMessage, error_code: str):
        entry = self.entries[(message.source_system, message.control_id)]
        entry.status, entry.last_error = "FAILED", error_code

    def get(self, source: str, control_id: str):
        return self.entries.get((source, control_id))

def retry_decision(error_kind: str, attempts: int, max_attempts: int = 3) -> str:
    if error_kind in {"MALFORMED", "UNSUPPORTED", "BUSINESS_VALIDATION"}:
        return "REJECT"
    if error_kind == "TRANSIENT":
        return "RETRY" if attempts < max_attempts else "DEAD_LETTER"
    return "DEAD_LETTER"
