"""
Prebuilt fake FHIR R4 bundles for local testing and demos.

These are synthetic examples for development only and do not represent
real patient records.
"""

from __future__ import annotations


def _patient_resource(patient_id: str, given: str, family: str, gender: str, birth_date: str) -> dict:
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"given": [given], "family": family}],
        "gender": gender,
        "birthDate": birth_date,
    }


def _condition_resource(text: str) -> dict:
    return {
        "resourceType": "Condition",
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {"text": text},
    }


def _medication_request_resource(text: str) -> dict:
    return {
        "resourceType": "MedicationRequest",
        "medicationCodeableConcept": {"text": text},
    }


def _bundle(*resources: dict) -> dict:
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": res} for res in resources],
    }


FHIR_SAMPLE_CASES = {
    "high_risk_ckd_nsaid_block": {
        "description": "Stage 3 CKD patient where NSAID should hard BLOCK.",
        "proposed_medication": "Ibuprofen",
        "bundle": _bundle(
            _patient_resource("patient-001", "Jane", "Doe", "female", "1965-04-12"),
            _condition_resource("Stage 3 Chronic Kidney Disease"),
            _condition_resource("Hypertension"),
            _medication_request_resource("Lisinopril 10mg"),
            _medication_request_resource("Furosemide 40mg"),
        ),
    },
    "warn_bleeding_risk": {
        "description": "Warfarin patient where aspirin should WARN for bleeding risk.",
        "proposed_medication": "Aspirin",
        "bundle": _bundle(
            _patient_resource("patient-002", "Robert", "Khan", "male", "1958-09-03"),
            _condition_resource("Atrial Fibrillation"),
            _condition_resource("History of GI Bleed"),
            _medication_request_resource("Warfarin 5mg"),
        ),
    },
    "allow_low_risk_baseline": {
        "description": "Lower-risk baseline case expected to be ALLOW/WARN by FDA signal only.",
        "proposed_medication": "Acetaminophen",
        "bundle": _bundle(
            _patient_resource("patient-003", "Maya", "Singh", "female", "1990-11-21"),
            _condition_resource("Seasonal Allergic Rhinitis"),
            _medication_request_resource("Cetirizine 10mg"),
        ),
    },
}


def get_sample_case(case_name: str) -> dict:
    """
    Return a named test case containing `proposed_medication` and `bundle`.
    """
    if case_name not in FHIR_SAMPLE_CASES:
        valid = ", ".join(sorted(FHIR_SAMPLE_CASES.keys()))
        raise KeyError(f"Unknown sample case '{case_name}'. Valid cases: {valid}")
    return FHIR_SAMPLE_CASES[case_name]

