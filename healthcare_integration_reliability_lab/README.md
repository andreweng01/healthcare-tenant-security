# Healthcare Integration & Reliability Lab
Portfolio project / learning evidence — not production healthcare software.

This package gives you a structured project for demonstrating knowledge of HL7 v2, InterSystems IRIS/ObjectScript concepts, idempotency, bounded retries, error classification, and recovery. It includes an executable Python reference model and tests plus ObjectScript examples intended for validation in an IRIS for Health environment.

## Honest evidence boundary
- The Python reference tests can be run locally.
- The ObjectScript files are illustrative source and have **not** been compiled or run against IRIS in this package-generation environment.
- This package does not include a configured IRIS interoperability production or prove real MLLP integration. Follow `docs/iris-validation-checklist.md` to complete that validation.
- Windows Server/IIS is a separate lab; see `docs/windows-iis-checklist.md`.
- Use only synthetic data. This is not HIPAA certification or production-ready software.

## Layout
- `objectscript/` — illustrative ObjectScript classes
- `hl7/samples/` — synthetic ADT and ORU messages
- `reference_impl/` — runnable Python behavior reference
- `tests/` — automated tests for the reference model
- `docs/` — architecture, test matrix, interview guide, validation checklists
- `evidence/` — forms to record actual run output

## Run the reference tests
Python 3.10+:
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```
Record the real output in `evidence/test-run-record.md`. Do not claim tests passed until you have run them.

## Recommended next step
Use the official InterSystems HL7 Quickstart as the environment foundation:
https://github.com/intersystems/quickstarts-hl7
It demonstrates an IRIS for Health HL7 production, sample input, routing/transformation trace, and Docker setup. Extend it, then complete the checklist in `docs/iris-validation-checklist.md`.

## Design principles
- Use the IRIS HL7 parser and message classes for real integrations; the reference parser here is intentionally limited.
- Scope message identity to sender/interface context plus `MSH-10`; agree how replay/corrections work.
- Retry transient errors only, with a bounded attempt count and backoff.
- Quarantine malformed/permanent failures rather than retrying forever.
- Make replay operator-controlled and auditable.
- Avoid logging full message bodies or unnecessary patient identifiers.
