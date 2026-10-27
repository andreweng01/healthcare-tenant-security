# Architecture and reliability decisions

1. Receive HL7 v2 through a configured IRIS interoperability business service (MLLP for TCP interfaces when agreed).
2. Parse the message with IRIS HL7 message APIs and the correct schema/profile.
3. Inspect MSH-3 (sending application), MSH-9 (message type/trigger/structure), and MSH-10 (message control ID).
4. Route supported `ADT^A01` and `ORU^R01` messages to appropriate processing paths.
5. Persist message identity and processing state at a defined transaction boundary.
6. Return ACK/NACK according to the trading-partner interface agreement.
7. Classify failures as transient, malformed/unsupported, or business validation failures.
8. Retry transient failures with bounded attempts/backoff; quarantine permanent failures; make replay auditable.

Production notes:
- The Python ledger is in-memory and not durable.
- The Python parser is intentionally limited and must not replace a real HL7 parser.
- Message identity must be scoped to the sending system/interface; correction/replay semantics must be agreed.
- Do not log full payloads or unnecessary patient identifiers.
