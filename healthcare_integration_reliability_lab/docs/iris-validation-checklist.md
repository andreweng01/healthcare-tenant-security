# IRIS validation checklist

- Record IRIS/IRIS for Health version, deployment method, namespace.
- Import and compile `.cls` files; capture actual compiler output.
- Review persistent class and unique index behavior in a disposable namespace.
- Replace illustrative routing decisions with supported IRIS HL7 APIs and production components.
- Configure an inbound HL7 service and MLLP framing if that matches the interface contract.
- Configure routing rules and transformations for ADT and ORU.
- Send both synthetic sample messages and inspect message traces.
- Test malformed/unsupported input and verify ACK/NACK behavior against the interface agreement.
- Test downstream outage, bounded retries, duplicate detection, quarantine, and operator replay.
- Confirm logging avoids unnecessary PHI.
- Save actual screenshots/logs and note failures honestly.
