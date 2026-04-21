"""
server.py — HealthMind FastMCP backend.

Exposes three MCP tools:
  1. drug_interaction(drug_a, drug_b) — queries openFDA AERS
  2. fhir_context(fhir_bundle_json) — parses FHIR R4 bundles
  3. safety_check(proposed_medication, patient_fhir_json) — full pipeline

Also exposes REST endpoints for the mobile app:
  POST /check   — run a safety check
  POST /chat    — simple AI chat relay
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

from fhir_utils import build_sample_fhir_bundle, parse_fhir_bundle
from safety_buffer import SafetyBuffer

load_dotenv()

OPENFDA_BASE_URL = os.getenv("OPENFDA_BASE_URL", "https://api.fda.gov/drug")
OPENFDA_API_KEY = os.getenv("OPENFDA_API_KEY", "")
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP("HealthMind Safety Agent")


# ---------------------------------------------------------------------------
# MCP Tool 1 — Drug Interaction via openFDA AERS
# ---------------------------------------------------------------------------
@mcp.tool()
async def drug_interaction(drug_a: str, drug_b: str) -> dict[str, Any]:
    """
    Query the openFDA Adverse Event Reporting System (AERS) for reports
    involving both drug_a and drug_b simultaneously.

    Returns total_fda_reports, has_interactions, severity, sample_interactions.
    """
    search_query = f'patient.drug.medicinalproduct:"{drug_a}"+AND+patient.drug.medicinalproduct:"{drug_b}"'
    params: dict[str, Any] = {
        "search": search_query,
        "limit": 5,
    }
    if OPENFDA_API_KEY:
        params["api_key"] = OPENFDA_API_KEY

    url = f"{OPENFDA_BASE_URL}/event.json"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)

        if response.status_code == 404:
            return {
                "drug_pair": f"{drug_a} + {drug_b}",
                "total_fda_reports": 0,
                "has_interactions": False,
                "severity": "low",
                "sample_interactions": [],
                "source": "openFDA AERS",
            }

        response.raise_for_status()
        data = response.json()
        meta = data.get("meta", {})
        results = data.get("results", [])
        total = meta.get("results", {}).get("total", 0)

        sample_interactions: list[dict[str, Any]] = []
        for result in results[:5]:
            reactions = result.get("patient", {}).get("reaction", [])
            reaction_terms = [
                r.get("reactionmeddrapt", "Unknown") for r in reactions[:3]
            ]
            seriousness = "serious" if result.get("serious", 0) == 1 else "non-serious"
            sample_interactions.append({
                "reactions": reaction_terms,
                "seriousness": seriousness,
                "receive_date": result.get("receivedate", ""),
            })

        serious_count = sum(
            1 for r in results if r.get("serious", 0) == 1
        )
        if total >= 50 or serious_count >= 3:
            severity = "high"
        elif total >= 10 or serious_count >= 1:
            severity = "medium"
        else:
            severity = "low"

        return {
            "drug_pair": f"{drug_a} + {drug_b}",
            "total_fda_reports": total,
            "has_interactions": total > 0,
            "severity": severity,
            "sample_interactions": sample_interactions,
            "source": "openFDA AERS",
        }

    except httpx.HTTPStatusError as exc:
        return {
            "drug_pair": f"{drug_a} + {drug_b}",
            "total_fda_reports": 0,
            "has_interactions": False,
            "severity": "low",
            "sample_interactions": [],
            "source": "openFDA AERS",
            "error": f"FDA API returned status {exc.response.status_code}",
        }
    except httpx.RequestError as exc:
        return {
            "drug_pair": f"{drug_a} + {drug_b}",
            "total_fda_reports": 0,
            "has_interactions": False,
            "severity": "low",
            "sample_interactions": [],
            "source": "openFDA AERS",
            "error": f"Network error: {str(exc)}",
        }


# ---------------------------------------------------------------------------
# MCP Tool 2 — FHIR Context Parser
# ---------------------------------------------------------------------------
@mcp.tool()
async def fhir_context(fhir_bundle_json: str) -> dict[str, Any]:
    """
    Parse a FHIR R4 Bundle JSON string and extract patient context.

    Returns flat dict with patient_id, name, age, gender, conditions,
    medications, allergies.
    """
    try:
        bundle = json.loads(fhir_bundle_json)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid JSON: {str(exc)}"}

    return parse_fhir_bundle(bundle)


# ---------------------------------------------------------------------------
# MCP Tool 3 — Full Safety Check Pipeline
# ---------------------------------------------------------------------------
@mcp.tool()
async def safety_check(
    proposed_medication: str,
    patient_fhir_json: str,
) -> dict[str, Any]:
    """
    Full prescription safety check pipeline.

    1. Parse the FHIR bundle for patient context
    2. Query openFDA for each current medication + proposed medication
    3. Run the SafetyBuffer rule engine
    4. Return SHARP-compliant recommendation with HITL flag
    """
    patient_ctx = await fhir_context(patient_fhir_json)
    if "error" in patient_ctx:
        return {"error": patient_ctx["error"]}

    interaction_results: list[dict[str, Any]] = []
    for current_med in patient_ctx.get("medications", []):
        med_name = current_med.split(" ")[0] if current_med else current_med
        result = await drug_interaction(med_name, proposed_medication)
        result["drug_pair"] = f"{current_med} + {proposed_medication}"
        interaction_results.append(result)

    buffer = SafetyBuffer(
        patient_name=patient_ctx.get("name", "Unknown"),
        proposed_medication=proposed_medication,
        conditions=patient_ctx.get("conditions", []),
        current_medications=patient_ctx.get("medications", []),
        allergies=patient_ctx.get("allergies", []),
    )

    evaluation = buffer.evaluate(fda_interaction_results=interaction_results)

    return {
        "patient": {
            "name": patient_ctx.get("name"),
            "id": patient_ctx.get("patient_id"),
            "age": patient_ctx.get("age"),
            "gender": patient_ctx.get("gender"),
            "conditions": patient_ctx.get("conditions", []),
            "medications": patient_ctx.get("medications", []),
            "allergies": patient_ctx.get("allergies", []),
        },
        "proposed_medication": proposed_medication,
        "fda_interactions": interaction_results,
        "status": evaluation["status"],
        "priority": evaluation["priority"],
        "reasons": evaluation["reasons"],
        "sharp_recommendation": evaluation["sharp_recommendation"],
        "hitl_required": evaluation["hitl_required"],
        "disclaimer": evaluation["disclaimer"],
    }


# ---------------------------------------------------------------------------
# REST endpoints for mobile app
# ---------------------------------------------------------------------------
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware


async def handle_check(request: Request) -> JSONResponse:
    """POST /check — Run a safety check from the mobile app."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body"}, status_code=400)

    proposed = body.get("proposed_medication", "").strip()
    patient_json = body.get("patient_fhir_json", "")

    if not proposed:
        return JSONResponse(
            {"detail": "proposed_medication is required"}, status_code=400
        )

    if not patient_json:
        sample = build_sample_fhir_bundle()
        patient_json = json.dumps(sample)
    elif isinstance(patient_json, dict):
        patient_json = json.dumps(patient_json)

    result = await safety_check(proposed, patient_json)
    return JSONResponse(result)


async def handle_chat(request: Request) -> JSONResponse:
    """POST /chat — AI chat endpoint for the mobile app."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body"}, status_code=400)

    message = body.get("message", "").strip()
    session_id = body.get("session_id", str(uuid.uuid4()))
    history = body.get("history", [])

    if not message:
        return JSONResponse({"detail": "message is required"}, status_code=400)

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if anthropic_key and anthropic_key != "sk-ant-your-key-here":
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=anthropic_key)

            system_prompt = (
                "You are HealthMind, an AI-powered prescription safety assistant. "
                "You help physicians understand drug interactions, contraindications, "
                "and clinical safety guidelines. You always emphasize that your "
                "responses are informational and require Human-in-the-Loop (HITL) "
                "validation by a licensed healthcare provider. Be concise, accurate, "
                "and cite relevant clinical guidelines when possible."
            )

            messages = []
            for h in history[-20:]:
                role = "user" if h.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": h.get("content", "")})
            messages.append({"role": "user", "content": message})

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )

            reply = response.content[0].text
            return JSONResponse({
                "reply": reply,
                "session_id": session_id,
            })

        except Exception as exc:
            return JSONResponse({
                "reply": _fallback_response(message),
                "session_id": session_id,
                "note": f"Anthropic API error, using fallback: {str(exc)}",
            })
    else:
        return JSONResponse({
            "reply": _fallback_response(message),
            "session_id": session_id,
            "note": "No Anthropic API key configured. Using built-in responses.",
        })


def _fallback_response(message: str) -> str:
    """Provide informative responses when no AI API key is available."""
    msg_lower = message.lower()

    if "nsaid" in msg_lower and ("contraindication" in msg_lower or "risk" in msg_lower):
        return (
            "**Common NSAID Contraindications:**\n\n"
            "• **Chronic Kidney Disease (CKD):** NSAIDs reduce renal blood flow and "
            "can precipitate acute kidney injury, especially in Stage 3+ CKD.\n"
            "• **Heart Failure:** NSAIDs cause sodium and fluid retention, worsening "
            "cardiac output and increasing hospitalization risk.\n"
            "• **Peptic Ulcer Disease:** NSAIDs inhibit COX-1, reducing protective "
            "prostaglandins in the gastric mucosa, increasing bleeding risk.\n"
            "• **Pregnancy (3rd trimester):** Risk of premature ductus arteriosus "
            "closure and oligohydramnios.\n"
            "• **Concurrent Anticoagulants:** Increased bleeding risk with warfarin, "
            "heparin, or DOACs.\n\n"
            "⚕️ *HITL Notice: Always verify contraindications with current clinical "
            "guidelines and patient-specific factors.*"
        )

    if "ckd" in msg_lower or "kidney" in msg_lower:
        return (
            "**Stage 3 CKD Medication Risks:**\n\n"
            "Stage 3 CKD (GFR 30-59 mL/min) requires careful medication management:\n\n"
            "• **NSAIDs:** Contraindicated — nephrotoxic, reduce GFR further.\n"
            "• **Metformin:** Use with caution — risk of lactic acidosis with reduced "
            "clearance. Often dose-adjusted or discontinued below GFR 30.\n"
            "• **ACE Inhibitors/ARBs:** Generally beneficial for renoprotection but "
            "monitor potassium and creatinine closely.\n"
            "• **Contrast Dye:** Increased risk of contrast-induced nephropathy.\n"
            "• **Aminoglycosides:** Nephrotoxic — avoid or monitor levels closely.\n\n"
            "⚕️ *HITL Notice: Dosing decisions in CKD require nephrology consultation "
            "and regular GFR monitoring.*"
        )

    if "hitl" in msg_lower or "human" in msg_lower and "loop" in msg_lower:
        return (
            "**Human-in-the-Loop (HITL) Validation:**\n\n"
            "HITL is a safety paradigm where AI systems provide recommendations but "
            "a qualified human makes the final decision. In HealthMind:\n\n"
            "• **Every recommendation** is flagged `hitl_required: true`\n"
            "• **The AI never auto-prescribes** — it only advises\n"
            "• **The physician reviews** the SHARP recommendation, considers "
            "patient-specific factors, and makes the final call\n"
            "• **Audit trail** maintains a record of AI recommendation + physician "
            "decision for accountability\n\n"
            "This approach balances AI efficiency with clinical safety and aligns "
            "with WHO guidelines on AI in healthcare decision support.\n\n"
            "⚕️ *AI-generated assessments supplement, never replace, clinical judgment.*"
        )

    if "openfda" in msg_lower or "fda" in msg_lower:
        return (
            "**How openFDA Works in HealthMind:**\n\n"
            "HealthMind queries the openFDA Adverse Event Reporting System (AERS):\n\n"
            "1. **Endpoint:** `api.fda.gov/drug/event.json`\n"
            "2. **Query:** Searches for reports where BOTH drugs appear in the same "
            "adverse event report\n"
            "3. **Data:** Returns total report count, seriousness flags, and "
            "reaction terms (MedDRA coded)\n"
            "4. **Severity scoring:** HealthMind classifies based on:\n"
            "   - ≥50 reports OR ≥3 serious → HIGH\n"
            "   - ≥10 reports OR ≥1 serious → MEDIUM\n"
            "   - Otherwise → LOW\n\n"
            "The openFDA data is post-market surveillance — it reflects real-world "
            "adverse events reported by healthcare professionals and consumers.\n\n"
            "⚕️ *HITL Notice: FDA AERS data has reporting bias and does not establish "
            "causation. Clinical judgment is essential.*"
        )

    return (
        "I'm HealthMind, your AI prescription safety assistant. I can help with:\n\n"
        "• **Drug interaction queries** — potential contraindications between medications\n"
        "• **Clinical safety guidelines** — condition-specific medication risks\n"
        "• **FHIR data interpretation** — understanding patient health records\n"
        "• **HITL workflow** — how human-in-the-loop validation works\n\n"
        "Try asking:\n"
        '• "What are common NSAID contraindications?"\n'
        '• "Explain Stage 3 CKD medication risks"\n'
        '• "How does openFDA adverse event reporting work?"\n\n'
        "⚕️ *HITL Notice: All responses are informational and require physician review.*"
    )


async def handle_health(request: Request) -> JSONResponse:
    """GET /health — Health check endpoint."""
    return JSONResponse({"status": "ok", "service": "HealthMind Safety Agent"})


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app():
    """Create the ASGI application with CORS and REST routes."""
    from starlette.applications import Starlette
    from starlette.middleware import Middleware

    routes = [
        Route("/health", handle_health, methods=["GET"]),
        Route("/check", handle_check, methods=["POST"]),
        Route("/chat", handle_chat, methods=["POST"]),
    ]

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ]

    app = Starlette(routes=routes, middleware=middleware)
    return app


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    rest_app = create_app()

    print("=" * 60)
    print("  HealthMind Safety Agent")
    print("  ─────────────────────────────────────────")
    print(f"  REST API:  http://{MCP_HOST}:{MCP_PORT}")
    print(f"  Health:    http://{MCP_HOST}:{MCP_PORT}/health")
    print(f"  Check:     POST http://{MCP_HOST}:{MCP_PORT}/check")
    print(f"  Chat:      POST http://{MCP_HOST}:{MCP_PORT}/chat")
    print("  ─────────────────────────────────────────")
    print("  MCP tools: drug_interaction, fhir_context, safety_check")
    print("=" * 60)

    uvicorn.run(rest_app, host=MCP_HOST, port=MCP_PORT)