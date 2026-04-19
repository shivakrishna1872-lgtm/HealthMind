"""
HealthMind Safety Buffer
Core safety logic for prescription evaluation.

Implements:
  - FDA interaction severity scoring
  - Specialized condition-drug rules (CKD + NSAID, etc.)
  - SHARP-compliant recommendation formatting
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Status = Literal["BLOCK", "WARN", "ALLOW"]
Priority = Literal["high", "medium", "low"]


# ─── Specialized safety rules ─────────────────────────────────────────────────
# Each rule is (condition_keyword, drug_keyword, status, priority, reason)

SAFETY_RULES: list[tuple[str, str, Status, Priority, str]] = [
    (
        "stage 3 chronic kidney disease",
        "nsaid",
        "BLOCK",
        "high",
        "NSAIDs are contraindicated in Stage 3 CKD. They reduce renal blood flow and "
        "can precipitate acute kidney injury or accelerate CKD progression.",
    ),
    (
        "chronic kidney disease",
        "nsaid",
        "BLOCK",
        "high",
        "NSAIDs are contraindicated in patients with CKD due to nephrotoxicity risk.",
    ),
    (
        "chronic kidney disease",
        "metformin",
        "WARN",
        "medium",
        "Metformin requires dose adjustment or may be contraindicated depending on eGFR. "
        "Check current renal function before prescribing.",
    ),
    (
        "warfarin",          # current medication keyword
        "aspirin",
        "WARN",
        "high",
        "Concurrent aspirin and warfarin significantly increases bleeding risk. "
        "Monitor INR closely if co-prescribed.",
    ),
    (
        "heart failure",
        "nsaid",
        "BLOCK",
        "high",
        "NSAIDs cause sodium and water retention and can worsen heart failure.",
    ),
    (
        "peptic ulcer",
        "nsaid",
        "WARN",
        "high",
        "NSAIDs increase risk of GI bleeding in patients with peptic ulcer disease. "
        "Consider a PPI or alternative analgesic.",
    ),
    (
        "pregnancy",
        "nsaid",
        "BLOCK",
        "high",
        "NSAIDs (especially in the third trimester) are associated with premature ductus "
        "arteriosus closure and oligohydramnios.",
    ),
    (
        "renal failure",
        "nsaid",
        "BLOCK",
        "high",
        "NSAIDs are contraindicated in renal failure.",
    ),
]


@dataclass
class SafetyResult:
    status: Status
    priority: Priority
    reason: str
    sharp_recommendation: str
    triggered_rules: list[str] = field(default_factory=list)


class SafetyBuffer:
    """
    Evaluates a proposed medication against a patient's context and
    openFDA interaction findings. Returns a SafetyResult with a
    SHARP-compliant physician recommendation.

    The physician (Human-in-the-Loop) makes the final clinical decision.
    """

    def __init__(self, proposed_medication: str, patient_context: dict):
        self.proposed = proposed_medication.lower().strip()
        self.conditions: list[str] = [c.lower() for c in patient_context.get("conditions", [])]
        self.medications: list[str] = [m.lower() for m in patient_context.get("medications", [])]
        self.patient_name: str = patient_context.get("name", "the patient")
        self.patient_id: str = patient_context.get("patient_id", "unknown")

    def _check_rules(self) -> list[tuple[Status, Priority, str]]:
        """Apply specialized condition-drug and drug-drug rules."""
        hits: list[tuple[Status, Priority, str]] = []
        all_context = self.conditions + self.medications

        for cond_kw, drug_kw, status, priority, reason in SAFETY_RULES:
            cond_match = any(cond_kw in ctx for ctx in all_context)
            drug_match = drug_kw in self.proposed or any(drug_kw in m for m in self.medications)
            if cond_match and (drug_kw in self.proposed):
                hits.append((status, priority, reason))

        return hits

    def _score_fda_interactions(
        self, interaction_results: list[dict]
    ) -> tuple[Status, Priority, str]:
        """Derive a status from openFDA interaction findings."""
        total_reports = sum(r.get("total_fda_reports", 0) for r in interaction_results)
        serious_count = sum(
            1
            for r in interaction_results
            for i in r.get("sample_interactions", [])
            if i.get("serious")
        )

        if total_reports > 100 or serious_count >= 3:
            return (
                "WARN",
                "high",
                f"openFDA reports {total_reports} adverse event reports for this drug combination, "
                f"including {serious_count} marked serious.",
            )
        if total_reports > 20:
            return (
                "WARN",
                "medium",
                f"openFDA reports {total_reports} adverse events for this combination. "
                "Review before prescribing.",
            )
        return (
            "ALLOW",
            "low",
            f"openFDA shows {total_reports} adverse reports — no major signals detected.",
        )

    def _build_sharp_recommendation(
        self, status: Status, priority: Priority, reason: str
    ) -> str:
        """
        Format a SHARP-compliant recommendation string for the physician.
        SHARP recommendations are structured for EMR integration.
        """
        status_label = {
            "BLOCK": "CONTRAINDICATION DETECTED — DO NOT PRESCRIBE without specialist review",
            "WARN": "CAUTION — Review required before prescribing",
            "ALLOW": "No major contraindications detected",
        }[status]

        return (
            f"[SHARP SAFETY RECOMMENDATION]\n"
            f"Patient: {self.patient_name} (ID: {self.patient_id})\n"
            f"Proposed medication: {self.proposed.upper()}\n"
            f"Safety status: {status} ({priority.upper()} priority)\n"
            f"Assessment: {status_label}\n"
            f"Clinical rationale: {reason}\n"
            f"\n"
            f"IMPORTANT: This recommendation is AI-generated and requires physician "
            f"review and approval (Human-in-the-Loop). The prescribing physician retains "
            f"full clinical responsibility for the final decision."
        )

    def evaluate(self, interaction_results: list[dict]) -> SafetyResult:
        """
        Run the full safety evaluation pipeline.
        Rule-based blocks take precedence over FDA scoring.
        """
        rule_hits = self._check_rules()
        fda_status, fda_priority, fda_reason = self._score_fda_interactions(interaction_results)

        # Determine final status: BLOCK > WARN > ALLOW
        triggered: list[str] = []
        final_status: Status = fda_status
        final_priority: Priority = fda_priority
        final_reason = fda_reason

        for r_status, r_priority, r_reason in rule_hits:
            triggered.append(r_reason)
            if r_status == "BLOCK":
                final_status = "BLOCK"
                final_priority = "high"
                final_reason = r_reason
                break
            elif r_status == "WARN" and final_status == "ALLOW":
                final_status = "WARN"
                final_priority = r_priority
                final_reason = r_reason

        sharp = self._build_sharp_recommendation(final_status, final_priority, final_reason)

        return SafetyResult(
            status=final_status,
            priority=final_priority,
            reason=final_reason,
            sharp_recommendation=sharp,
            triggered_rules=triggered,
        )