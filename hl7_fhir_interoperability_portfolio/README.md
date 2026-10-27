# HL7 v2 → FHIR R4 Interoperability Portfolio

A small, testable learning project demonstrating a **local reference implementation** for mapping synthetic HL7 v2 messages into basic FHIR R4 JSON resources.

## What it demonstrates
- Parse HL7 v2 segments and fields (including standard carriage-return segment delimiters).
- Process `ADT^A01` into a FHIR `Patient` and `Encounter`.
- Process `ORU^R01` into a FHIR `Observation`.
- Validate required fields and return explicit errors for unsupported or malformed messages.
- Test duplicate message-control IDs with an in-memory idempotency store.
- Run automated tests and inspect deterministic JSON output.

## Important scope and limitations
- This is a **portfolio / educational reference implementation**, not a production interface engine.
- Samples contain synthetic data only. Do not add real patient data.
- The FHIR checks here are lightweight structural checks; they are **not** a substitute for the official HL7 FHIR validator, implementation-guide validation, terminology validation, or conformance testing.
- The idempotency store is in memory and does not survive restarts or coordinate across multiple processes.
- This project does not establish experience with InterSystems IRIS, an actual MLLP listener, a hospital EHR, or production clinical workflows.
- No HIPAA compliance or security certification is claimed.

## Requirements
- Python 3.10+
- pytest for tests

## Run locally (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
```

If PowerShell blocks activation, use Command Prompt:
```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pytest -q
```

## Run the examples
```powershell
$env:PYTHONPATH="src"
python -c "from pathlib import Path; from interop.pipeline import process_hl7; print(process_hl7(Path('samples/hl7v2/adt_a01.hl7').read_text()))"
python -c "from pathlib import Path; from interop.pipeline import process_hl7; print(process_hl7(Path('samples/hl7v2/oru_r01.hl7').read_text()))"
```

## Mapping summary
| HL7 v2 source | Meaning | FHIR output |
|---|---|---|
| `MSH-10` | Message control ID | Idempotency key |
| `PID-3` | Patient identifier | `Patient.identifier` |
| `PID-5` | Patient name | `Patient.name` |
| `PID-7` | Birth date | `Patient.birthDate` when valid |
| `PID-8` | Administrative sex | `Patient.gender` when mapped |
| `PV1-2` | Patient class | `Encounter.class` |
| `PV1-19` | Visit number | `Encounter.identifier` |
| `OBX-3` | Observation code | `Observation.code` |
| `OBX-5` | Observation value | `Observation.valueString` |
| `OBX-6` | Units | `Observation.valueQuantity.unit` where present |
| `OBX-14` | Observation timestamp | `Observation.effectiveDateTime` when present |

## Suggested evidence to publish
1. Actual output of `python -m pytest -q`.
2. A screenshot or copied terminal output from running both examples.
3. A short architecture note describing mapping decisions and known limitations.
4. A commit history showing incremental implementation and fixes.

Do not claim tests passed until you run them and record the actual output.
