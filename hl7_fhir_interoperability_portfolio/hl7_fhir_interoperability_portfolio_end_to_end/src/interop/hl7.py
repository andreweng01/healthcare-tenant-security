"""Minimal parser for a deliberately limited HL7 v2 subset."""
from dataclasses import dataclass
from typing import Dict, List

class HL7Error(ValueError):
    """Raised when an HL7 message is malformed or lacks required fields."""

@dataclass
class ParsedMessage:
    message_type: str
    control_id: str
    version: str
    segments: Dict[str, List[List[str]]]

def parse_hl7(raw: str) -> ParsedMessage:
    if not isinstance(raw, str) or not raw.strip():
        raise HL7Error("Message body is empty.")
    # Accept standard CR segment delimiters and pasted LF-delimited fixtures.
    lines = [line.strip("\n") for line in raw.strip().replace("\r\n", "\r").split("\r") if line.strip()]
    if len(lines) == 1 and "\n" in lines[0]:
        lines = [line for line in lines[0].split("\n") if line.strip()]
    if not lines or not lines[0].startswith("MSH"):
        raise HL7Error("The first segment must be MSH.")
    msh = lines[0]
    if len(msh) < 4:
        raise HL7Error("MSH segment is too short.")
    field_sep = msh[3]
    msh_fields = msh.split(field_sep)
    if len(msh_fields) < 12:
        raise HL7Error("MSH must contain fields through MSH-11/12.")
    # In an MSH split, MSH-1 is the separator and MSH-2 is encoding characters.
    msg_type = msh_fields[8] if len(msh_fields) > 8 else ""
    control_id = msh_fields[9] if len(msh_fields) > 9 else ""
    version = msh_fields[11] if len(msh_fields) > 11 else ""
    if not msg_type or not control_id:
        raise HL7Error("MSH-9 message type and MSH-10 control ID are required.")
    segments: Dict[str, List[List[str]]] = {}
    for line in lines:
        seg_name = line[:3]
        if len(seg_name) != 3 or not seg_name[:2].isalpha() or not seg_name[2].isalnum():
            raise HL7Error(f"Invalid segment line: {seg_name!r}.")
        parts = line.split(field_sep)
        if seg_name == "MSH":
            # Normalize MSH indexing so parts[1] corresponds to MSH-2.
            parts = [parts[0], field_sep] + parts[1:]
        segments.setdefault(seg_name, []).append(parts)
    return ParsedMessage(msg_type, control_id, version, segments)

def field(message: ParsedMessage, segment: str, occurrence: int, field_number: int) -> str:
    rows = message.segments.get(segment, [])
    if occurrence >= len(rows):
        return ""
    row = rows[occurrence]
    # MSH was normalized differently; callers use non-MSH segments.
    return row[field_number] if field_number < len(row) else ""

def component(value: str, number: int) -> str:
    parts = value.split("^")
    return parts[number - 1] if 1 <= number <= len(parts) else ""
