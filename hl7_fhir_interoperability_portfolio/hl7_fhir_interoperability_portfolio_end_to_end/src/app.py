"""FastAPI HTTP adapter for the HL7 v2 processing pipeline."""
import json, os, uuid
from typing import Any, Dict
import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from .interop.pipeline import process_message
from .interop.store import MessageStore
from .interop.hl7 import parse_hl7, HL7Error
from .interop.fhir import map_to_fhir

app = FastAPI(title="HL7 v2 → FHIR R4 Demo", version="1.0.0",
              description="Synthetic-data portfolio demo; limited HL7/FHIR subset.")
store = MessageStore(os.getenv("INTEROP_DB_PATH", "interop_messages.db"))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/messages")
def messages():
    rows = store.recent()
    for row in rows:
        if row.get("resources_json"):
            row["resources"] = json.loads(row.pop("resources_json"))
        else:
            row.pop("resources_json", None)
    return {"items": rows}

@app.get("/messages/{control_id}")
def message_status(control_id: str):
    row = store.get(control_id)
    if not row:
        raise HTTPException(status_code=404, detail="Message control ID not found.")
    if row.get("resources_json"):
        row["resources"] = json.loads(row.pop("resources_json"))
    else:
        row.pop("resources_json", None)
    return row

@app.post("/hl7")
async def ingest_hl7(request: Request, x_message_id: str | None = Header(default=None)):
    raw = (await request.body()).decode("utf-8", errors="replace")
    result = process_message(raw, store)
    if result["status"] == "REJECTED" and result["control_id"] is None:
        # Malformed messages without a readable MSH control ID are returned but cannot be keyed in the audit table.
        return result
    return result

@app.post("/hl7/forward")
async def ingest_and_forward(request: Request):
    """Map an HL7 message and submit generated resources as a FHIR transaction Bundle."""
    base = os.getenv("FHIR_BASE_URL", "").rstrip("/")
    if not base:
        raise HTTPException(status_code=503, detail="FHIR_BASE_URL is not configured.")
    raw = (await request.body()).decode("utf-8", errors="replace")
    try:
        parsed = parse_hl7(raw)
        resources = map_to_fhir(parsed)
    except HL7Error as exc:
        return {"status": "REJECTED", "error": str(exc), "resources": []}
    entries = []
    # Bundle-local UUID references allow the server to resolve the Patient link
    # atomically even when it assigns its own logical resource ID.
    patient_full_url = "urn:uuid:" + str(uuid.uuid4())
    for resource in resources:
        entry = {"resource": resource, "request": {"method": "POST", "url": resource["resourceType"]}}
        if resource["resourceType"] == "Patient":
            entry["fullUrl"] = patient_full_url
            identifier = resource.get("identifier", [{}])[0]
            system = identifier.get("system", "")
            value = identifier.get("value", "")
            entry["request"] = {"method": "POST", "url": f"Patient?identifier={system}|{value}"}
        else:
            if resource.get("subject", {}).get("reference", "").startswith("Patient/"):
                resource["subject"]["reference"] = patient_full_url
        entries.append(entry)
    bundle = {"resourceType": "Bundle", "type": "transaction", "entry": entries}
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(base, json=bundle, headers={"Accept": "application/fhir+json"})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"FHIR server request failed: {type(exc).__name__}")
    try:
        outcome = response.json()
    except ValueError:
        outcome = {"raw_response": response.text[:1000]}
    return {"status": "FORWARDED", "control_id": parsed.control_id,
            "fhir_base_url": base, "submitted_bundle": bundle, "server_response": outcome}
