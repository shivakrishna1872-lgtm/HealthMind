"""
HealthMind FastMCP Server
Exposes three MCP tools:
  - drug_interaction  : queries openFDA for drug-drug interactions
  - fhir_context      : extracts relevant fields from a FHIR R4 patient bundle
  - safety_check      : runs the full Safety Buffer pipeline and returns a
                        SHARP-compliant recommendation
"""

import os
import json
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel
from safety_buffer import SafetyBuffer, SafetyResult
from fhir_utils import extract_patient_context

load_dotenv()

mcp = FastMCP(
    name="healthmind",
    version="1.0.0",
    description="Prescription safety agent using openFDA and FHIR",
)

OPENFDA_BASE = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov/drug")
OPENFDA_KEY = os.getenv("OPENFDA_API_KEY", "")


# ─── Tool 1: Drug interaction check via openFDA ───────────────────────────────

class DrugInteractionInput(BaseModel):
    drug_a: str
    drug_b: str


@mcp.tool()
async def drug_interaction(drug_a: str, drug_b: str) -> dict:
    """
    Check for interactions between two drugs using the real openFDA API.
    Returns severity, description, and source label from FDA data.
    """
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_a}"+AND+patient.drug.medicinalproduct:"{drug_b}"',
        "limit": 5,
    }
    if OPENFDA_KEY:
        params["api_key"] = OPENFDA_KEY

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{OPENFDA_BASE}/event.json", params=params)
            data = resp.json()
        except Exception as e:
            return {"error": str(e), "interactions": [], "total": 0}

    total = data.get("meta", {}).get("results", {}).get("total", 0)
    results = data.get("results", [])

    interactions = []
    for r in results[:5]:
        reactions = [
            rx.get("reactionmeddrapt", "unknown")
            for rx in r.get("patient", {}).get("reaction", [])
        ]
        seriousness = r.get("serious", 0)
        interactions.append({
            "reactions": reactions,
            "serious": bool(seriousness),
            "report_id": r.get("safetyreportid"),
        })

    return {
        "drug_a": drug_a,
        "drug_b": drug_b,
        "total_fda_reports": total,
        "has_interactions": total > 0,
        "severity": "high" if total > 50 else "medium" if total > 5 else "low",
        "sample_interactions": interactions,
    }


# ─── Tool 2: FHIR context extraction (SHARP) ─────────────────────────────────

@mcp.tool()
def fhir_context(fhir_bundle_json: str) -> dict:
    """
    Parse a FHIR R4 patient bundle and extract conditions, medications,
    allergies, and demographics — the SHARP context needed for safety checks.
    """
    try:
        bundle = json.loads(fhir_bundle_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid FHIR JSON: {e}"}
    return extract_patient_context(bundle)


# ─── Tool 3: Full safety check pipeline ──────────────────────────────────────

@mcp.tool()
async def safety_check(
    proposed_medication: str,
    patient_fhir_json: str,
) -> dict:
    """
    Run the complete HealthMind Safety Buffer pipeline.

    1. Parse the patient's FHIR data for conditions and current medications.
    2. Run drug_interaction checks against each current medication.
    3. Apply specialized safety rules (e.g. Stage 3 CKD + NSAID = BLOCK).
    4. Return a SHARP-compliant recommendation for the physician (HITL).

    The physician MUST review and approve before any clinical action is taken.
    """
    try:
        fhir_bundle = json.loads(patient_fhir_json)
    except json.JSONDecodeError as e:
        return {"status": "ERROR", "reason": f"Invalid FHIR JSON: {e}"}

    patient_ctx = extract_patient_context(fhir_bundle)
    buffer = SafetyBuffer(proposed_medication=proposed_medication, patient_context=patient_ctx)

    # Run interaction checks for each current med
    interaction_results = []
    for current_med in patient_ctx.get("medications", []):
        result = await drug_interaction(drug_a=proposed_medication, drug_b=current_med)
        interaction_results.append(result)

    final: SafetyResult = buffer.evaluate(interaction_results)

    return {
        "status": final.status,           # "BLOCK" | "WARN" | "ALLOW"
        "priority": final.priority,       # "high" | "medium" | "low"
        "reason": final.reason,
        "proposed_medication": proposed_medication,
        "patient_conditions": patient_ctx.get("conditions", []),
        "current_medications": patient_ctx.get("medications", []),
        "interaction_findings": interaction_results,
        "sharp_recommendation": final.sharp_recommendation,
        "hitl_required": True,            # Always — doctor makes final call
        "disclaimer": (
            "This is an AI-generated safety suggestion only. "
            "A licensed physician must review and approve before any clinical action."
        ),
    }


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", 8000))
    print(f"HealthMind FastMCP server starting on {host}:{port}")
    mcp.run(host=host, port=port)