"""
fhir_utils.py — FHIR R4 Bundle parser for HealthMind.

Parses FHIR R4 Bundle entries for:
  - Patient
  - Condition
  - MedicationRequest
  - MedicationStatement
  - AllergyIntolerance

Returns a flat dict with patient_id, name, age, gender, conditions[], medications[], allergies[].
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any


def _calculate_age(birth_date_str: str) -> int | None:
    """Calculate age from an ISO date string (YYYY-MM-DD)."""
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
    except (ValueError, TypeError):
        return None


def _extract_patient(resource: dict[str, Any]) -> dict[str, Any]:
    """Extract patient demographics from a FHIR Patient resource."""
    patient_id = resource.get("id", "unknown")
    gender = resource.get("gender", "unknown")
    birth_date = resource.get("birthDate", "")
    age = _calculate_age(birth_date) if birth_date else None

    name_parts: list[str] = []
    for name_entry in resource.get("name", []):
        given = name_entry.get("given", [])
        family = name_entry.get("family", "")
        full = " ".join(given) + (" " + family if family else "")
        if full.strip():
            name_parts.append(full.strip())

    return {
        "patient_id": patient_id,
        "name": name_parts[0] if name_parts else "Unknown",
        "age": age,
        "gender": gender,
        "birth_date": birth_date,
    }


def _extract_condition(resource: dict[str, Any]) -> str | None:
    """Extract human-readable condition name from a FHIR Condition resource."""
    code = resource.get("code", {})
    coding_list = code.get("coding", [])
    if coding_list:
        display = coding_list[0].get("display")
        if display:
            return display
    text = code.get("text")
    if text:
        return text
    return None


def _extract_medication(resource: dict[str, Any]) -> str | None:
    """Extract medication name from a FHIR MedicationRequest or MedicationStatement."""
    med_codeable = resource.get("medicationCodeableConcept", {})
    coding_list = med_codeable.get("coding", [])
    if coding_list:
        display = coding_list[0].get("display")
        if display:
            return display
    text = med_codeable.get("text")
    if text:
        return text
    return None


def _extract_allergy(resource: dict[str, Any]) -> str | None:
    """Extract allergy substance from a FHIR AllergyIntolerance resource."""
    code = resource.get("code", {})
    coding_list = code.get("coding", [])
    if coding_list:
        display = coding_list[0].get("display")
        if display:
            return display
    text = code.get("text")
    if text:
        return text
    return None


def parse_fhir_bundle(bundle: dict[str, Any] | str) -> dict[str, Any]:
    """
    Parse a FHIR R4 Bundle and return a flat patient-context dict.

    Parameters
    ----------
    bundle : dict or str
        A FHIR R4 Bundle (as dict or JSON string).

    Returns
    -------
    dict with keys:
        patient_id, name, age, gender, conditions, medications, allergies
    """
    if isinstance(bundle, str):
        bundle = json.loads(bundle)

    result: dict[str, Any] = {
        "patient_id": "unknown",
        "name": "Unknown",
        "age": None,
        "gender": "unknown",
        "birth_date": "",
        "conditions": [],
        "medications": [],
        "allergies": [],
    }

    entries = bundle.get("entry", [])
    for entry in entries:
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType", "")

        if resource_type == "Patient":
            patient_info = _extract_patient(resource)
            result.update(patient_info)

        elif resource_type == "Condition":
            condition = _extract_condition(resource)
            if condition:
                result["conditions"].append(condition)

        elif resource_type in ("MedicationRequest", "MedicationStatement"):
            medication = _extract_medication(resource)
            if medication:
                result["medications"].append(medication)

        elif resource_type == "AllergyIntolerance":
            allergy = _extract_allergy(resource)
            if allergy:
                result["allergies"].append(allergy)

    return result


def build_sample_fhir_bundle() -> dict[str, Any]:
    """
    Build a sample FHIR R4 Bundle for testing.

    Patient: Jane Doe, DOB 1965-04-12
    Conditions: Stage 3 Chronic Kidney Disease, Hypertension
    Medications: Lisinopril 10 mg, Furosemide 40 mg
    """
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-jane-doe-001",
                    "name": [
                        {
                            "use": "official",
                            "given": ["Jane"],
                            "family": "Doe",
                        }
                    ],
                    "gender": "female",
                    "birthDate": "1965-04-12",
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "condition-ckd-001",
                    "subject": {"reference": "Patient/patient-jane-doe-001"},
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "433144002",
                                "display": "Stage 3 Chronic Kidney Disease",
                            }
                        ],
                        "text": "Stage 3 Chronic Kidney Disease",
                    },
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                            }
                        ]
                    },
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "condition-htn-001",
                    "subject": {"reference": "Patient/patient-jane-doe-001"},
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "38341003",
                                "display": "Hypertension",
                            }
                        ],
                        "text": "Hypertension",
                    },
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                            }
                        ]
                    },
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "medrx-lisinopril-001",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/patient-jane-doe-001"},
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "314076",
                                "display": "Lisinopril 10 MG",
                            }
                        ],
                        "text": "Lisinopril 10 MG",
                    },
                    "dosageInstruction": [
                        {
                            "text": "Take 1 tablet by mouth once daily",
                            "timing": {
                                "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                            },
                            "doseAndRate": [
                                {
                                    "doseQuantity": {
                                        "value": 10,
                                        "unit": "mg",
                                    }
                                }
                            ],
                        }
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "medrx-furosemide-001",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": "Patient/patient-jane-doe-001"},
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "310429",
                                "display": "Furosemide 40 MG",
                            }
                        ],
                        "text": "Furosemide 40 MG",
                    },
                    "dosageInstruction": [
                        {
                            "text": "Take 1 tablet by mouth once daily",
                            "timing": {
                                "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                            },
                            "doseAndRate": [
                                {
                                    "doseQuantity": {
                                        "value": 40,
                                        "unit": "mg",
                                    }
                                }
                            ],
                        }
                    ],
                }
            },
        ],
    }