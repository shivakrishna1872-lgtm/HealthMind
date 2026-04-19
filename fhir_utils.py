"""
FHIR R4 bundle parsing utilities for HealthMind.
Extracts patient name, conditions, medications, and allergies
from a standard FHIR R4 Bundle resource.
"""

from __future__ import annotations


def extract_patient_context(bundle: dict) -> dict:
    """
    Parse a FHIR R4 Bundle and return a flat context dict:
    {
        "patient_id": str,
        "name": str,
        "age": int | None,
        "gender": str | None,
        "conditions": [str, ...],
        "medications": [str, ...],
        "allergies": [str, ...],
    }
    """
    if bundle.get("resourceType") == "Bundle":
        entries = bundle.get("entry", [])
        resources = [e.get("resource", {}) for e in entries]
    else:
        resources = [bundle]

    patient_id = "unknown"
    name = "Unknown Patient"
    gender = None
    age = None
    conditions: list[str] = []
    medications: list[str] = []
    allergies: list[str] = []

    for res in resources:
        rtype = res.get("resourceType", "")

        if rtype == "Patient":
            patient_id = res.get("id", patient_id)
            gender = res.get("gender")
            names = res.get("name", [])
            if names:
                n = names[0]
                given = " ".join(n.get("given", []))
                family = n.get("family", "")
                name = f"{given} {family}".strip()
            dob = res.get("birthDate")
            if dob:
                from datetime import date
                try:
                    birth_year = int(dob[:4])
                    age = date.today().year - birth_year
                except Exception:
                    pass

        elif rtype == "Condition":
            status = res.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")
            if status in ("active", ""):
                coding = res.get("code", {}).get("coding", [])
                text = res.get("code", {}).get("text", "")
                label = text or (coding[0].get("display", "") if coding else "")
                if label:
                    conditions.append(label)

        elif rtype in ("MedicationRequest", "MedicationStatement"):
            med = res.get("medicationCodeableConcept", {})
            text = med.get("text", "")
            coding = med.get("coding", [])
            label = text or (coding[0].get("display", "") if coding else "")
            if label:
                medications.append(label)

        elif rtype == "AllergyIntolerance":
            sub = res.get("code", {})
            text = sub.get("text", "")
            coding = sub.get("coding", [])
            label = text or (coding[0].get("display", "") if coding else "")
            if label:
                allergies.append(label)

    return {
        "patient_id": patient_id,
        "name": name,
        "age": age,
        "gender": gender,
        "conditions": conditions,
        "medications": medications,
        "allergies": allergies,
    }


def build_sample_fhir_bundle(
    patient_name: str = "Jane Doe",
    conditions: list[str] | None = None,
    medications: list[str] | None = None,
) -> dict:
    """
    Helper to build a minimal FHIR R4 Bundle for testing.
    """
    conditions = conditions or ["Stage 3 Chronic Kidney Disease"]
    medications = medications or ["Lisinopril", "Furosemide"]

    entries = [
        {
            "resource": {
                "resourceType": "Patient",
                "id": "patient-001",
                "name": [{"given": [patient_name.split()[0]], "family": patient_name.split()[-1]}],
                "gender": "female",
                "birthDate": "1965-04-12",
            }
        }
    ]

    for c in conditions:
        entries.append({
            "resource": {
                "resourceType": "Condition",
                "clinicalStatus": {"coding": [{"code": "active"}]},
                "code": {"text": c},
            }
        })

    for m in medications:
        entries.append({
            "resource": {
                "resourceType": "MedicationRequest",
                "medicationCodeableConcept": {"text": m},
            }
        })

    return {"resourceType": "Bundle", "type": "collection", "entry": entries}