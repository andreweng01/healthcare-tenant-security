# Architecture and mapping decisions

## Pipeline
`HL7 text → parser → message-type router → mapping functions → lightweight FHIR checks → JSON resources`

## Safety and design choices
- Parser accepts CR segment separators and also tolerates LF/CRLF copied into test fixtures.
- The parser is deliberately small. It does not implement every HL7 escape sequence, repetition, encoding variation, conformance profile, or full datatype semantics.
- The patient identifier uses an example URI system. Real deployments must use the assigning authority and identifier-system rules agreed by the source and destination systems.
- This demonstration maps a narrow subset of `ADT^A01` and `ORU^R01`.
- `Observation.valueString` is used to avoid silently assuming that every OBX value is numeric. Unit text is retained as a note in this first version.
- The duplicate store is an in-memory teaching example. Production processing needs durable idempotency, transactional persistence, retry limits, dead-letter handling, auditability, monitoring, and privacy/security controls.
- FHIR checks are local subset checks, not official FHIR conformance validation.

## Next improvements
1. Add official FHIR R4 validation using a validator and chosen implementation guide.
2. Convert numeric OBX values to `valueQuantity` only when datatype, units, and terminology are validated.
3. Add OBX repetition and multiple observations.
4. Add durable idempotency and a retry/dead-letter workflow.
5. Add MLLP framing only after defining transport requirements and testing in a safe local environment.
