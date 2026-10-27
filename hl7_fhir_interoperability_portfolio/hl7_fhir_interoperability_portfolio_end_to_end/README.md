# HL7 v2 → FHIR Interoperability Portfolio

A runnable, educational end-to-end integration demo. It accepts HL7 v2 messages over HTTP, parses and validates them, maps ADT^A01 and ORU^R01 messages to FHIR R4 resources, records outcomes in SQLite, and prevents duplicate processing by message control ID.

> **Scope and honesty:** This is a portfolio/demo implementation, not a certified HL7 interface engine or production clinical system. It supports a deliberately small subset of HL7 v2 fields and FHIR R4 structures. It has synthetic examples only. It does not implement MLLP transport, full HL7 conformance, authentication, or a production-grade FHIR server. Do not use real patient data.

## What it demonstrates

- HTTP ingestion endpoint for HL7 v2 messages (`POST /hl7`)
- MSH/PID/PV1 and OBR/OBX parsing for supported message types
- Validation and clear rejection outcomes
- ADT^A01 mapping to FHIR `Patient` + `Encounter`
- ORU^R01 mapping to FHIR `Patient` + `Observation`
- SQLite audit log with message ID, message type, outcome, timestamp, and sanitized error
- Idempotency for repeated message control IDs
- Automated tests for successful processing, malformed input, unsupported message type, required-field failures, and duplicate delivery
- Optional forwarding of generated resources to a FHIR R4 server using a transaction Bundle

## Run on Windows

From this folder, open PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
uvicorn src.app:app --reload
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pytest -q
uvicorn src.app:app --reload
```

Open `http://127.0.0.1:8000/docs` to try the API.

## Try a sample

PowerShell:
```powershell
$body = Get-Content .\samples\adt_a01.hl7 -Raw
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/hl7 -ContentType "text/plain" -Body $body
```

Or use the interactive API docs at `/docs`, `POST /hl7`, with the raw message in the request body.

Expected successful response includes `status: "PROCESSED"` and generated FHIR resources. Send the same message again and the response should be `DUPLICATE`.

## Endpoints

- `GET /health` — basic process health
- `GET /messages` — recent processing records
- `GET /messages/{control_id}` — one message outcome
- `POST /hl7` — accept a raw HL7 v2 message as `text/plain`
- `POST /hl7/forward` — parse/map and, when configured, submit a transaction Bundle to a FHIR server

Set `FHIR_BASE_URL` to a test FHIR R4 base URL to enable forwarding, e.g. `http://localhost:8080/fhir`. If unset, `/hl7/forward` returns a clear configuration error. Do not expose a development server publicly.

## Evidence checklist

After running the tests locally, save the actual terminal output in your project notes. Do not claim tests passed until you have run them yourself. For a stronger portfolio, include a screenshot of passing tests and a sample `/hl7` response, and explain the supported subset and limitations.

## Important limitations

- HTTP transport is not MLLP. Real hospital interfaces often use MLLP; this demo deliberately uses HTTP so it is easy to run locally.
- This parser is not a full HL7 v2 grammar and does not implement all escape sequences, repetitions, components, acknowledgments, or version-specific rules.
- The FHIR mapping is a minimal R4 example. The included validator checks a small set of structural requirements; it is not the official HL7 validator and does not establish US Core/profile conformance.
- SQLite logging is suitable for a local demo, not a high-availability production interface.
- No authentication, authorization, TLS, secrets management, PHI safeguards, or production operational controls are included.
