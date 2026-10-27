"""Minimal HL7 v2 parser for educational examples; not a full HL7 conformance parser."""
from dataclasses import dataclass
from typing import Dict, List


class HL7ParseError(ValueError):
    """Raised when a message cannot be parsed safely."""


@dataclass(frozen=True)
class Segment:
    name: str
    fields: List[str]


@dataclass(frozen=True)
class HL7Message:
    segments: List[Segment]

    def first(self, name: str) -> Segment:
        for segment in self.segments:
            if segment.name == name:
                return segment
        raise HL7ParseError(f"Required segment {name} is missing")

    def all(self, name: str) -> List[Segment]:
        return [s for s in self.segments if s.name == name]


def parse_message(raw: str) -> HL7Message:
    if not isinstance(raw, str) or not raw.strip():
        raise HL7ParseError("Message is empty")

    # HL7 v2 segments are normally separated by CR. Accept LF/CRLF for copied examples.
    normalized = raw.replace("\r\n", "\r").replace("\n", "\r")
    lines = [line.strip() for line in normalized.split("\r") if line.strip()]
    if not lines:
        raise HL7ParseError("Message contains no segments")
    if not lines[0].startswith("MSH|"):
        raise HL7ParseError("First segment must be MSH")

    segments: List[Segment] = []
    for line in lines:
        fields = line.split("|")
        name = fields[0]
        if len(name) != 3 or not name.isalnum():
            raise HL7ParseError(f"Invalid segment identifier: {name!r}")
        # MSH is special: MSH-1 is the field separator and MSH-2 is encoding chars.
        # For a convenient field lookup, fields[1] is MSH-2, fields[8] is MSH-9, etc.
        segments.append(Segment(name=name, fields=fields))

    return HL7Message(segments)


def field(segment: Segment, hl7_field_number: int, component: int = 1) -> str:
    """Return a 1-based HL7 field, optionally selecting a 1-based component."""
    if segment.name == "MSH":
        # MSH-1 is the separator itself; split('|') places it between fields[0] and fields[1].
        if hl7_field_number == 1:
            return "|"
        index = hl7_field_number - 1
    else:
        index = hl7_field_number
    if index >= len(segment.fields) or index < 0:
        return ""
    value = segment.fields[index]
    components = value.split("^")
    if component < 1 or component > len(components):
        return ""
    return components[component - 1]
