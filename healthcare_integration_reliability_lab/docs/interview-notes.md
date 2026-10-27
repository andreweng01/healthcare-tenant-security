# Interview notes

- `ADT^A01` commonly signals an admission; `PID` identifies the patient and `PV1` carries visit information.
- `ORU^R01` commonly carries observation/results; `OBR` identifies the requested/ordered test and `OBX` carries an observation.
- `MSH-10` is the message control ID; scope deduplication with sender/interface context and define replay/correction rules.
- MLLP frames HL7 v2 over TCP; it does not itself guarantee exactly-once business processing.
- Retry transient errors only, bound attempts, quarantine permanent failures, and audit replays.
- Use IRIS HL7 parsing/routing/transformation tools in an actual production rather than ad-hoc string parsing.
- Honest project framing: "I built a personal interoperability lab to explore HL7 v2 message validation and reliability patterns. The Python reference tests cover the intended behavior; IRIS-specific compilation and production tests are recorded separately."
