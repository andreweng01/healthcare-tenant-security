# Architecture and design notes

## Flow

1. HTTP adapter receives a raw HL7 v2 payload.
2. Parser reads MSH and splits the message into segments/fields.
3. Pipeline checks the message control ID for duplicate delivery.
4. Mapper validates required fields and builds minimal FHIR R4-shaped resources.
5. SQLite stores the processing outcome and generated resource JSON.
6. Caller receives `PROCESSED`, `REJECTED`, or `DUPLICATE` with a machine-readable result.
7. Optional `/hl7/forward` sends a FHIR transaction Bundle to a configured FHIR server.

## Supported subset

- `ADT^A01`: PID patient identifier/name plus PV1 visit number/admit time → Patient + Encounter.
- `ORU^R01`: PID patient identifier/name plus first OBX observation → Patient + Observation.
- Segment delimiter: CR preferred; LF accepted for pasted fixtures.
- MSH-10 control ID is the idempotency key.

## Deliberate limits

This is a teaching implementation, not a complete HL7 v2 parser. It does not implement all field repetitions, escape sequences, alternate delimiters, Z-segments, ACK/NACK messages, MLLP framing, patient matching/merge, multiple OBX values, full code-system binding, or official FHIR validation. The `Patient/{id}` reference uses the source patient ID as a logical placeholder; a real FHIR server may assign different IDs, so production integration needs explicit identifier resolution and valid references. For a production system, use a mature interface engine/library, secure transport, authenticated endpoints, robust monitoring, retry/dead-letter strategy, database transactions, and privacy/security controls.
