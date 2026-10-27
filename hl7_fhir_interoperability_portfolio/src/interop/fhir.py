"""Lightweight checks for the subset of FHIR R4 resources emitted by this project."""
from typing import Any, Dict, List


class FHIRValidationError(ValueError):
    pass


def validate_resource(resource: Dict[str, Any]) -> None:
    if not isinstance(resource, dict):
        raise FHIRValidationError("FHIR resource must be a JSON object")
    resource_type = resource.get("resourceType")
    if resource_type == "Patient":
        if not resource.get("identifier"):
            raise FHIRValidationError("Patient.identifier is required by this lab")
    elif resource_type == "Encounter":
        if not resource.get("status") or not resource.get("class"):
            raise FHIRValidationError("Encounter.status and Encounter.class are required by this lab")
    elif resource_type == "Observation":
        if not resource.get("status") or not resource.get("code"):
            raise FHIRValidationError("Observation.status and Observation.code are required by this lab")
    else:
        raise FHIRValidationError(f"Unsupported resourceType: {resource_type!r}")
