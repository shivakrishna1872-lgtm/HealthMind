"""
safety_buffer.py — SafetyBuffer clinical rule engine for HealthMind.

Implements hard-coded clinical safety rules that evaluate proposed medications
against a patient's existing conditions and current medications.

Rule precedence: BLOCK > WARN > ALLOW
"""

from __future__ import annotations

from typing import Any


class SafetyBuffer:
    """
    Clinical safety rule engine.

    Evaluates proposed medications against patient conditions and current
    medications to determine if the prescription should be BLOCKED, receive
    a WARNING, or be ALLOWED.
    """

    CONDITION_DRUG_RULES: list[dict[str, str]] = [
        {
            "condition_keyword": "stage 3 chronic kidney disease",
            "drug_keyword": "nsaid",
            "status": "BLOCK",
            "priority": "high",
            "reason": "NSAIDs are contraindicated in Stage 3 CKD due to risk of "
                       "acute kidney injury and accelerated renal function decline.",
        },
        {
            "condition_keyword": "chronic kidney disease",
            "drug_keyword": "nsaid",
            "status": "BLOCK",
            "priority": "high",
            "reason": "NSAIDs are contraindicated in Chronic Kidney Disease due to "
                       "nephrotoxicity and risk of further renal impairment.",
        },
        {
            "condition_keyword": "chronic kidney disease",
            "drug_keyword": "metformin",
            "status": "WARN",
            "priority": "medium",
            "reason": "Metformin requires dose adjustment or monitoring in CKD patients "
                       "due to increased risk of lactic acidosis with reduced renal clearance.",
        },
        {
            "condition_keyword": "heart failure",
            "drug_keyword": "nsaid",
            "status": "BLOCK",
            "priority": "high",
            "reason": "NSAIDs are contraindicated in heart failure — they cause sodium "
                       "and fluid retention, worsening cardiac function and increasing "
                       "hospitalization risk.",
        },
        {
            "condition_keyword": "peptic ulcer",
            "drug_keyword": "nsaid",
            "status": "WARN",
            "priority": "high",
            "reason": "NSAIDs increase the risk of gastrointestinal bleeding and "
                       "ulcer perforation in patients with peptic ulcer disease.",
        },
        {
            "condition_keyword": "pregnancy",
            "drug_keyword": "nsaid",
            "status": "BLOCK",
            "priority": "high",
            "reason": "NSAIDs are contraindicated in pregnancy, especially in the third "
                       "trimester, due to risk of premature closure of the ductus arteriosus "
                       "and oligohydramnios.",
        },
        {
            "condition_keyword": "renal failure",
            "drug_keyword": "nsaid",
            "status": "BLOCK",
            "priority": "high",
            "reason": "NSAIDs are contraindicated in renal failure — they reduce renal "
                       "blood flow and can precipitate acute-on-chronic kidney injury.",
        },
    ]

    MEDICATION_INTERACTION_RULES: list[dict[str, str]] = [
        {
            "current_med_keyword": "warfarin",
            "proposed_keyword": "aspirin",
            "status": "WARN",
            "priority": "high",
            "reason": "Concurrent use of warfarin and aspirin significantly increases "
                       "bleeding risk. If clinically necessary, INR monitoring frequency "
                       "should be increased and gastroprotective therapy considered.",
        },
    ]

    NSAID_KEYWORDS: list[str] = [
        "ibuprofen", "naproxen", "diclofenac", "celecoxib", "meloxicam",
        "indomethacin", "piroxicam", "ketorolac", "aspirin", "nsaid",
        "advil", "motrin", "aleve", "voltaren", "celebrex", "mobic",
    ]

    STATUS_PRECEDENCE: dict[str, int] = {
        "BLOCK": 3,
        "WARN": 2,
        "ALLOW": 1,
    }

    def __init__(
        self,
        patient_name: str,
        proposed_medication: str,
        conditions: list[str],
        current_medications: list[str],
        allergies: list[str] | None = None,
    ) -> None:
        self.patient_name = patient_name
        self.proposed_medication = proposed_medication
        self.conditions = conditions
        self.current_medications = current_medications
        self.allergies = allergies or []

    def _is_nsaid(self, drug_name: str) -> bool:
        """Check if a drug name matches any known NSAID keyword."""
        drug_lower = drug_name.lower()
        return any(keyword in drug_lower for keyword in self.NSAID_KEYWORDS)

    def _check_condition_rules(self) -> list[dict[str, str]]:
        """Evaluate condition-based rules against the proposed medication."""
        triggered: list[dict[str, str]] = []
        proposed_lower = self.proposed_medication.lower()

        for rule in self.CONDITION_DRUG_RULES:
            condition_kw = rule["condition_keyword"]
            drug_kw = rule["drug_keyword"]

            condition_match = any(
                condition_kw in c.lower() for c in self.conditions
            )
            if not condition_match:
                continue

            if drug_kw == "nsaid":
                drug_match = self._is_nsaid(proposed_lower)
            else:
                drug_match = drug_kw in proposed_lower

            if drug_match:
                triggered.append(rule)

        return triggered

    def _check_medication_interaction_rules(self) -> list[dict[str, str]]:
        """Evaluate medication interaction rules."""
        triggered: list[dict[str, str]] = []
        proposed_lower = self.proposed_medication.lower()

        for rule in self.MEDICATION_INTERACTION_RULES:
            current_kw = rule["current_med_keyword"]
            proposed_kw = rule["proposed_keyword"]

            current_match = any(
                current_kw in med.lower() for med in self.current_medications
            )
            proposed_match = proposed_kw in proposed_lower

            if current_match and proposed_match:
                triggered.append(rule)

        return triggered

    def _check_allergy_rules(self) -> list[dict[str, str]]:
        """Check if the proposed medication matches any known allergy."""
        triggered: list[dict[str, str]] = []
        proposed_lower = self.proposed_medication.lower()

        for allergy in self.allergies:
            if allergy.lower() in proposed_lower or proposed_lower in allergy.lower():
                triggered.append({
                    "status": "BLOCK",
                    "priority": "high",
                    "reason": f"Patient has a documented allergy to {allergy}. "
                              f"Prescribing {self.proposed_medication} is contraindicated.",
                })

        return triggered

    def evaluate(
        self,
        fda_interaction_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Run all safety rules and return the aggregate recommendation.

        Parameters
        ----------
        fda_interaction_results : list[dict], optional
            Results from openFDA drug interaction queries.

        Returns
        -------
        dict with status, priority, reasons, sharp_recommendation, hitl_required, disclaimer
        """
        all_triggered: list[dict[str, str]] = []

        all_triggered.extend(self._check_condition_rules())
        all_triggered.extend(self._check_medication_interaction_rules())
        all_triggered.extend(self._check_allergy_rules())

        fda_flags: list[str] = []
        if fda_interaction_results:
            for interaction in fda_interaction_results:
                if interaction.get("has_interactions") and interaction.get("severity") == "high":
                    fda_flags.append(
                        f"FDA AERS reports indicate significant adverse event reports "
                        f"for {interaction.get('drug_pair', 'unknown pair')}: "
                        f"{interaction.get('total_fda_reports', 0)} reports found."
                    )

        if not all_triggered and not fda_flags:
            status = "ALLOW"
            priority = "low"
            reasons = [
                f"No contraindications found for {self.proposed_medication} "
                f"given the patient's current conditions and medications."
            ]
        else:
            highest_precedence = 0
            for rule in all_triggered:
                rule_prec = self.STATUS_PRECEDENCE.get(rule["status"], 0)
                if rule_prec > highest_precedence:
                    highest_precedence = rule_prec

            if fda_flags and highest_precedence < self.STATUS_PRECEDENCE["WARN"]:
                highest_precedence = self.STATUS_PRECEDENCE["WARN"]

            status = "ALLOW"
            for s, p in self.STATUS_PRECEDENCE.items():
                if p == highest_precedence:
                    status = s
                    break

            priority_map = {"BLOCK": "high", "WARN": "medium", "ALLOW": "low"}
            priority = priority_map.get(status, "low")

            if all_triggered:
                max_triggered = max(
                    all_triggered,
                    key=lambda r: self.STATUS_PRECEDENCE.get(r.get("status", "ALLOW"), 0),
                )
                if max_triggered.get("priority") == "high":
                    priority = "high"

            reasons = [r["reason"] for r in all_triggered] + fda_flags

        sharp = self._build_sharp_recommendation(status, priority, reasons)

        return {
            "status": status,
            "priority": priority,
            "reasons": reasons,
            "sharp_recommendation": sharp,
            "hitl_required": True,
            "disclaimer": (
                "This is an AI-generated safety assessment. A licensed healthcare "
                "provider must review and approve all prescribing decisions. "
                "Human-in-the-Loop (HITL) validation is required before any "
                "medication is administered."
            ),
        }

    def _build_sharp_recommendation(
        self,
        status: str,
        priority: str,
        reasons: list[str],
    ) -> str:
        """Build a SHARP-compliant formatted recommendation string."""
        status_label = {
            "BLOCK": "⛔ BLOCKED — Do NOT prescribe",
            "WARN": "⚠️  WARNING — Prescribe with caution",
            "ALLOW": "✅ ALLOWED — No contraindications detected",
        }.get(status, "UNKNOWN")

        clinical_rationale = "\n".join(f"  • {r}" for r in reasons) if reasons else "  • None"

        conditions_str = ", ".join(self.conditions) if self.conditions else "None documented"
        medications_str = ", ".join(self.current_medications) if self.current_medications else "None documented"
        allergies_str = ", ".join(self.allergies) if self.allergies else "None documented"

        return (
            f"[SHARP SAFETY RECOMMENDATION]\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Patient:              {self.patient_name}\n"
            f"Proposed Medication:  {self.proposed_medication}\n"
            f"Decision:             {status_label}\n"
            f"Priority:             {priority.upper()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"\n"
            f"CLINICAL RATIONALE:\n"
            f"{clinical_rationale}\n"
            f"\n"
            f"PATIENT CONTEXT:\n"
            f"  Conditions:   {conditions_str}\n"
            f"  Medications:  {medications_str}\n"
            f"  Allergies:    {allergies_str}\n"
            f"\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"HITL NOTICE: This recommendation requires review and approval\n"
            f"by a licensed healthcare provider before any action is taken.\n"
            f"AI-generated safety assessments do not replace clinical judgment.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )