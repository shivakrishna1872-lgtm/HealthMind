"""
document_validator.py — Clinical Document Validator for HealthMind.

Classifies incoming text as one of:
  - FHIR        : structured FHIR R4 JSON bundle
  - clinical_note: patient-specific conditions, meds, or history
  - lab_report   : measurable lab values (creatinine, GFR, WBC, etc.)
  - essay        : general / educational writing
  - article      : informational / research content
  - unknown      : cannot be classified with confidence

Safety rule: false acceptance is worse than false rejection.
When in doubt, reject.
"""

from __future__ import annotations

import json
import re
from typing import Any


class DocumentValidator:
    """
    Deterministic, heuristic-based clinical document validator.

    Uses pattern matching (not LLM) so the gate is fast, reproducible,
    and does not hallucinate structure in ambiguous inputs.
    """

    # ── FHIR detection ────────────────────────────────────────────────
    FHIR_REQUIRED_KEYS = {"resourceType", "entry"}
    FHIR_RESOURCE_TYPES = {
        "Bundle", "Patient", "Condition", "MedicationRequest",
        "MedicationStatement", "AllergyIntolerance", "Observation",
    }

    # ── Clinical note markers ─────────────────────────────────────────
    # Patient-specific identifiers
    PATIENT_AGE_PATTERN = re.compile(
        r"\b(\d{1,3})\s*[-–]?\s*(?:year|yr|y/?o|y\.o\.)\s*[-–]?\s*(?:old)?\b",
        re.IGNORECASE,
    )
    PATIENT_GENDER_PATTERN = re.compile(
        r"\b(?:male|female|man|woman|boy|girl|M|F)\b", re.IGNORECASE
    )
    PATIENT_REFERENCE_PATTERN = re.compile(
        r"\b(?:patient|pt|client|subject)\s+(?:is|was|has|had|presents?|reports?|denies?|complains?)\b",
        re.IGNORECASE,
    )
    PROPOSED_MED_PATTERN = re.compile(
        r"\b(?:proposed|prescribe[ds]?|order(?:ed|ing)?|start(?:ed|ing)?|initiat(?:e[ds]?|ing)|administer(?:ed|ing)?)\s+(?:medication|med|drug|rx)?\s*:?\s*\w+",
        re.IGNORECASE,
    )

    # Medication / dosage patterns
    DOSAGE_PATTERN = re.compile(
        r"\b\d+\.?\d*\s*(?:mg|mcg|g|ml|mL|units?|IU|µg|meq)\b", re.IGNORECASE
    )
    MEDICATION_KEYWORDS = [
        "lisinopril", "metformin", "ibuprofen", "naproxen", "aspirin",
        "warfarin", "furosemide", "atorvastatin", "omeprazole",
        "amlodipine", "metoprolol", "losartan", "hydrochlorothiazide",
        "prednisone", "gabapentin", "insulin", "acetaminophen",
        "diclofenac", "celecoxib", "meloxicam", "ketorolac",
        "amoxicillin", "azithromycin", "ciprofloxacin", "levothyroxine",
        "albuterol", "pantoprazole", "clopidogrel", "simvastatin",
    ]

    # Clinical condition markers
    CONDITION_KEYWORDS = [
        "ckd", "chronic kidney disease", "hypertension", "diabetes",
        "heart failure", "copd", "asthma", "peptic ulcer", "renal failure",
        "atrial fibrillation", "dvt", "pe", "pneumonia", "sepsis",
        "anemia", "hepatitis", "cirrhosis", "stroke", "mi",
        "myocardial infarction", "pregnancy", "gerd",
    ]

    # ── Lab report markers ────────────────────────────────────────────
    LAB_VALUE_PATTERN = re.compile(
        r"\b(?:creatinine|gfr|egfr|bun|wbc|rbc|hgb|hematocrit|hba1c|"
        r"a1c|platelets?|sodium|potassium|chloride|bicarbonate|glucose|"
        r"alt|ast|alp|bilirubin|albumin|inr|ptt|pt|troponin|bnp|"
        r"tsh|t3|t4|ldl|hdl|triglycerides|hemoglobin|calcium|magnesium|"
        r"phosphorus|uric\s*acid|lactate|pco2|po2|ph|spo2)\s*"
        r"[:=]?\s*\d+\.?\d*",
        re.IGNORECASE,
    )
    LAB_UNIT_PATTERN = re.compile(
        r"\d+\.?\d*\s*(?:mg/dL|mmol/L|mEq/L|g/dL|%|U/L|IU/L|"
        r"mL/min|mL/min/1\.73\s*m2|cells/µL|×10\^?\d|ng/mL|pg/mL|µg/dL)",
        re.IGNORECASE,
    )

    # ── Rejection anti-patterns (essay / article signals) ─────────────
    ESSAY_SIGNALS = re.compile(
        r"\b(?:this\s+essay|in\s+conclusion|in\s+summary|"
        r"the\s+purpose\s+of\s+this|the\s+aim\s+of\s+this|"
        r"this\s+paper\s+discusses|this\s+report\s+examines|"
        r"(?:we|I)\s+will\s+discuss|to\s+summarize|"
        r"the\s+following\s+essay|introduction\s*:|thesis\s+statement)\b",
        re.IGNORECASE,
    )
    ARTICLE_SIGNALS = re.compile(
        r"\b(?:studies?\s+show|research\s+(?:indicates?|suggests?|has\s+shown)|"
        r"according\s+to\s+(?:a\s+)?(?:recent\s+)?(?:study|research|review)|"
        r"meta-analysis|systematic\s+review|randomized\s+controlled\s+trial|"
        r"peer[\s-]?reviewed|published\s+in|journal\s+of|doi\s*:|"
        r"et\s+al\.|literature\s+review|evidence\s+suggests?|"
        r"clinical\s+trial\s+data\s+(?:show|demonstrate|indicate))\b",
        re.IGNORECASE,
    )
    EDUCATIONAL_SIGNALS = re.compile(
        r"\b(?:it\s+is\s+important\s+to\s+(?:note|understand|recognize)|"
        r"one\s+should\s+(?:consider|be\s+aware)|"
        r"generally\s+speaking|as\s+a\s+rule|"
        r"for\s+(?:educational|informational)\s+purposes|"
        r"common\s+(?:causes?|symptoms?|treatments?)\s+(?:of|for|include))\b",
        re.IGNORECASE,
    )

    # ── Thresholds ────────────────────────────────────────────────────
    MIN_ACCEPT_CONFIDENCE = 60  # below this → reject even if markers found
    ESSAY_LENGTH_THRESHOLD = 500  # words — long text with no clinical markers → essay

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def validate(self, input_text: str) -> dict[str, Any]:
        """
        Classify and validate an input document.

        Returns strict JSON:
        {
          "document_type": "FHIR | clinical_note | lab_report | essay | article | unknown",
          "is_valid": bool,
          "confidence": int (0-100),
          "reason": str,
          "action": "accept | reject"
        }
        """
        if not input_text or not input_text.strip():
            return self._result("unknown", False, 99,
                                "Empty input — no clinical data present", "reject")

        text = input_text.strip()

        # ── 1. Try FHIR detection first (structured data) ─────────
        fhir_result = self._try_fhir(text)
        if fhir_result is not None:
            return fhir_result

        # ── 2. Check for rejection anti-patterns ──────────────────
        rejection = self._check_rejection_patterns(text)
        if rejection is not None:
            return rejection

        # ── 3. Score clinical signal vs. noise ────────────────────
        clinical_score = self._score_clinical_signals(text)
        lab_score = self._score_lab_signals(text)
        noise_score = self._score_noise_signals(text)

        # ── 4. Classify based on scores ───────────────────────────
        return self._classify(text, clinical_score, lab_score, noise_score)

    # ──────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────

    def _try_fhir(self, text: str) -> dict[str, Any] | None:
        """Attempt to parse text as a FHIR R4 Bundle."""
        # Quick pre-check to avoid expensive JSON parsing on plaintext
        if not (text.lstrip().startswith("{") or text.lstrip().startswith("[")):
            return None

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            # Could be single-quoted JSON — try basic fix
            try:
                fixed = text.replace("'", '"')
                data = json.loads(fixed)
            except (json.JSONDecodeError, ValueError):
                return None

        if not isinstance(data, dict):
            return None

        resource_type = data.get("resourceType", "")

        if resource_type in self.FHIR_RESOURCE_TYPES:
            entries = data.get("entry", [])
            if resource_type == "Bundle" and isinstance(entries, list) and len(entries) > 0:
                # Verify at least one entry has a resource with a known type
                has_clinical = any(
                    entry.get("resource", {}).get("resourceType", "") in self.FHIR_RESOURCE_TYPES
                    for entry in entries
                    if isinstance(entry, dict)
                )
                if has_clinical:
                    return self._result("FHIR", True, 99,
                                        "Valid FHIR R4 Bundle with clinical resources", "accept")
                else:
                    return self._result("FHIR", True, 85,
                                        "FHIR Bundle detected but no recognized clinical resource types in entries",
                                        "accept")
            elif resource_type != "Bundle":
                # Standalone FHIR resource (e.g., Patient, Condition)
                return self._result("FHIR", True, 90,
                                    f"Standalone FHIR {resource_type} resource detected", "accept")
            else:
                # Bundle with no entries
                return self._result("FHIR", False, 75,
                                    "FHIR Bundle structure detected but contains no entries",
                                    "reject")

        return None

    def _check_rejection_patterns(self, text: str) -> dict[str, Any] | None:
        """Check for strong essay / article anti-patterns."""
        essay_matches = self.ESSAY_SIGNALS.findall(text)
        article_matches = self.ARTICLE_SIGNALS.findall(text)
        educational_matches = self.EDUCATIONAL_SIGNALS.findall(text)

        essay_hits = len(essay_matches)
        article_hits = len(article_matches)
        educational_hits = len(educational_matches)
        total_noise = essay_hits + article_hits + educational_hits

        # Strong essay signal (single match at start or multiple matches)
        if essay_hits >= 2 or (essay_hits == 1 and text.strip().lower().startswith(tuple(m.lower() for m in essay_matches))):
            return self._result("essay", False, min(98, 85 + essay_hits * 10),
                                "Essay-style introductory phrase or markers detected; no patient-specific data",
                                "reject")

        # Strong article signal (single match at start or multiple matches)
        if article_hits >= 2 or (article_hits == 1 and text.strip().lower().startswith(tuple(m.lower() for m in article_matches))):
            return self._result("article", False, min(98, 85 + article_hits * 10),
                                "Academic/research reporting style detected; no patient-specific context",
                                "reject")

        # Combined educational noise
        if total_noise >= 3:
            doc_type = "essay" if essay_hits >= article_hits else "article"
            return self._result(doc_type, False, min(95, 80 + total_noise * 4),
                                "Educational/informational content without patient-specific data",
                                "reject")

        return None

    def _score_clinical_signals(self, text: str) -> int:
        """Score text for clinical note markers (0-100)."""
        score = 0

        if self.PATIENT_AGE_PATTERN.search(text):
            score += 25
        if self.PATIENT_GENDER_PATTERN.search(text):
            score += 10
        if self.PATIENT_REFERENCE_PATTERN.search(text):
            score += 25
        if self.PROPOSED_MED_PATTERN.search(text):
            score += 15
        if self.DOSAGE_PATTERN.search(text):
            score += 10

        # Medication name matches
        text_lower = text.lower()
        med_hits = sum(1 for kw in self.MEDICATION_KEYWORDS if kw in text_lower)
        score += min(15, med_hits * 5)

        # Condition matches
        condition_hits = sum(1 for kw in self.CONDITION_KEYWORDS if kw in text_lower)
        score += min(15, condition_hits * 5)

        return min(100, score)

    def _score_lab_signals(self, text: str) -> int:
        """Score text for lab report markers (0-100)."""
        score = 0
        lab_hits = len(self.LAB_VALUE_PATTERN.findall(text))
        unit_hits = len(self.LAB_UNIT_PATTERN.findall(text))

        score += min(60, lab_hits * 20)
        score += min(40, unit_hits * 15)

        return min(100, score)

    def _score_noise_signals(self, text: str) -> int:
        """Score text for non-clinical noise (0-100). Higher = more noise."""
        score = 0

        essay_hits = len(self.ESSAY_SIGNALS.findall(text))
        article_hits = len(self.ARTICLE_SIGNALS.findall(text))
        educational_hits = len(self.EDUCATIONAL_SIGNALS.findall(text))

        score += essay_hits * 20
        score += article_hits * 15
        score += educational_hits * 10

        # Long text with no patient references → likely essay
        word_count = len(text.split())
        if word_count > self.ESSAY_LENGTH_THRESHOLD:
            if not self.PATIENT_REFERENCE_PATTERN.search(text):
                score += 30

        return min(100, score)

    def _classify(
        self, text: str,
        clinical_score: int, lab_score: int, noise_score: int,
    ) -> dict[str, Any]:
        """Make final classification based on signal scores."""
        word_count = len(text.split())

        # ── Lab report: strong lab signal dominates ───────────────
        if lab_score >= 40 and lab_score > noise_score:
            confidence = min(98, 60 + lab_score // 3)
            if self.PATIENT_REFERENCE_PATTERN.search(text) or clinical_score >= 20:
                return self._result("lab_report", True, confidence,
                                    "Contains lab values with patient-specific context", "accept")
            elif lab_score >= 60:
                return self._result("lab_report", True, max(65, confidence - 15),
                                    "Contains measurable lab values consistent with a lab report", "accept")

        # ── Clinical note: strong clinical signal ─────────────────
        if clinical_score >= self.MIN_ACCEPT_CONFIDENCE and clinical_score > noise_score:
            confidence = min(98, clinical_score)
            return self._result("clinical_note", True, confidence,
                                "Contains patient-specific clinical data (conditions, medications, or history)",
                                "accept")

        # ── Moderate clinical signal, low noise ───────────────────
        if clinical_score >= 35 and noise_score <= 15:
            confidence = min(85, 50 + clinical_score // 2)
            return self._result("clinical_note", True, confidence,
                                "Contains clinical markers with patient-specific context", "accept")

        # ── High noise, low clinical → reject ─────────────────────
        if noise_score >= 30 and clinical_score < 35:
            doc_type = "essay" if len(self.ESSAY_SIGNALS.findall(text)) > 0 else "article"
            confidence = min(95, 70 + noise_score // 4)
            return self._result(doc_type, False, confidence,
                                "General or educational content without patient-specific clinical data",
                                "reject")

        # ── Short input (< 5 words) — could be a medication name ──
        if word_count < 5:
            # Check if it's a recognizable medication
            text_lower = text.lower().strip().rstrip(".")
            if any(kw in text_lower for kw in self.MEDICATION_KEYWORDS):
                return self._result("clinical_note", True, 70,
                                    "Short input recognized as a medication name", "accept")
            # Check if it looks like a dosage
            if self.DOSAGE_PATTERN.search(text):
                return self._result("clinical_note", True, 65,
                                    "Short input contains a medication dosage pattern", "accept")
            # Very short, no recognizable markers
            return self._result("unknown", False, 80,
                                "Input too short to contain actionable clinical data", "reject")

        # ── Long text with no clinical markers → likely essay ─────
        if word_count > self.ESSAY_LENGTH_THRESHOLD and clinical_score < 20:
            return self._result("essay", False, 85,
                                "Extended text with no patient-specific clinical identifiers",
                                "reject")

        # ── Ambiguous — default to REJECT (safety rule) ───────────
        if clinical_score < self.MIN_ACCEPT_CONFIDENCE:
            return self._result("unknown", False, 60,
                                "Insufficient patient-specific clinical data to classify as valid input; "
                                "defaulting to reject per safety policy",
                                "reject")

        # Fallback (should not reach here normally)
        return self._result("unknown", False, 50,
                            "Unable to classify with sufficient confidence; "
                            "defaulting to reject per safety policy",
                            "reject")

    @staticmethod
    def _result(
        document_type: str,
        is_valid: bool,
        confidence: int,
        reason: str,
        action: str,
    ) -> dict[str, Any]:
        """Build a standardized result dict."""
        return {
            "document_type": document_type,
            "is_valid": is_valid,
            "confidence": confidence,
            "reason": reason,
            "action": action,
        }
