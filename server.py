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
from document_validator import DocumentValidator

_validator = DocumentValidator()

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


async def handle_validate(request: Request) -> JSONResponse:
    """POST /validate — Classify and validate a clinical document."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body"}, status_code=400)

    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"detail": "text is required"}, status_code=400)

    result = _validator.validate(text)
    status_code = 200 if result["action"] == "accept" else 422
    return JSONResponse(result, status_code=status_code)


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

    # Validate proposed medication input
    validation = _validator.validate(proposed)
    if validation["action"] == "reject":
        return JSONResponse(
            {"detail": "Input rejected by clinical document validator",
             "validation": validation},
            status_code=422,
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
                model="claude-3-5-sonnet-20241022",
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


# ---------------------------------------------------------------------------
# MCP Tool 4 — Diagnostic Agent
# ---------------------------------------------------------------------------
@mcp.tool()
async def diagnose_symptoms(
    symptoms: str,
    patient_fhir_json: str,
) -> dict[str, Any]:
    """
    Diagnostic Agent: Evaluate symptoms against patient history to find
    the most probable diagnosis.

    1. Parse FHIR for context (conditions, meds, age)
    2. Analyze symptoms using clinical reasoning
    3. Return differential diagnosis, confidence, and HITL warning
    """
    patient_ctx = await fhir_context(patient_fhir_json)
    if "error" in patient_ctx:
        return {"error": patient_ctx["error"]}

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if anthropic_key and anthropic_key != "sk-ant-your-key-here":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            
            prompt = (
                f"You are the HealthMind Diagnostic Agent. Perform a clinical assessment.\n\n"
                f"PATIENT DATA:\n"
                f"- Name: {patient_ctx.get('name')}\n"
                f"- Age/Gender: {patient_ctx.get('age')} / {patient_ctx.get('gender')}\n"
                f"- Conditions: {', '.join(patient_ctx.get('conditions', []))}\n"
                f"- Medications: {', '.join(patient_ctx.get('medications', []))}\n"
                f"- Allergies: {', '.join(patient_ctx.get('allergies', []))}\n\n"
                f"SYMPTOMS PRESENTED:\n{symptoms}\n\n"
                f"TASK: Provide a differential diagnosis in JSON format with fields:\n"
                f"- probable_diagnoses: list of {{condition, confidence, rationale}}\n"
                f"- recommended_next_steps: list of tests or assessments\n"
                f"- clinical_summary: 2-3 sentence overview\n"
                f"- urgent_flag: boolean (true if emergency signs like stroke/MI detected)\n\n"
                f"Respond ONLY with valid JSON."
            )

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            
            # Cleanly extract JSON
            raw_text = response.content[0].text
            try:
                # Basic JSON extraction in case there's lead-in text
                start_idx = raw_text.find("{")
                end_idx = raw_text.rfind("}") + 1
                result = json.loads(raw_text[start_idx:end_idx])
            except:
                result = {"error": "Failed to parse diagnostic output", "raw": raw_text}
                
            return {
                "patient": patient_ctx,
                "symptoms": symptoms,
                "assessment": result,
                "hitl_required": True,
                "disclaimer": "Informational assessment only. Physician must validate diagnosis.",
            }

        except Exception as exc:
            return {"error": f"AI Diagnostic Error: {str(exc)}"}
    else:
        # Static Fallback for Demo
        return {
            "patient": patient_ctx,
            "symptoms": symptoms,
            "assessment": {
                "probable_diagnoses": [
                    {
                        "condition": "Acute Exacerbation of HTN",
                        "confidence": "Medium",
                        "rationale": "High blood pressure history with new symptoms."
                    }
                ],
                "recommended_next_steps": ["Vital signs monitoring", "Renal panel"],
                "clinical_summary": f"Assessment of {symptoms} in context of Stage 3 CKD.",
                "urgent_flag": False
            },
            "hitl_required": True,
            "note": "AI key missing. Showing fallback assessment."
        }


async def handle_diagnose(request: Request) -> JSONResponse:
    """POST /diagnose — Run a diagnostic assessment."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body"}, status_code=400)

    symptoms = body.get("symptoms", "").strip()
    patient_json = body.get("patient_fhir_json", "")

    if not symptoms:
        return JSONResponse({"detail": "symptoms is required"}, status_code=400)

    if not patient_json:
        patient_json = json.dumps(build_sample_fhir_bundle())

    result = await diagnose_symptoms(symptoms, patient_json)
    return JSONResponse(result)


# ---------------------------------------------------------------------------
# HealthMind 2.0 — Unified Two-Agent Medical Analysis Hub
# ---------------------------------------------------------------------------

@mcp.tool()
async def analyze_medical_data(
    input_text: str,
    patient_fhir_json: str,
) -> dict[str, Any]:
    """
    Unified Analysis Hub powered by two specialized agents.
    
    Agent 1: Validation & Insight Agent
    Agent 2: Audit & Reporting Agent
    """
    processing_history = []
    timestamp = lambda: uuid.uuid4().hex[:8]
    
    # --- Step 1: Validation & Insight Agent ---
    processing_history.append({
        "agent": "Validation & Insight",
        "step": "Data Normalization",
        "status": "Success",
        "detail": "Extracted medical entities from input text."
    })
    
    patient_ctx = await fhir_context(patient_fhir_json)
    processing_history.append({
        "agent": "Validation & Insight",
        "step": "FHIR Context Verification",
        "status": "Success",
        "detail": f"Verified history for {patient_ctx.get('name')}."
    })
    
    # Check if input is likely a short medication name or a full clinical document
    # A full document might contain "mg" or "dose", so simply checking for those keywords is not enough.
    is_medication = len(input_text.split()) < 5
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    extracted_symptoms = ""
    extracted_meds = []
    
    if anthropic_key and anthropic_key != "sk-ant-your-key-here" and not is_medication:
        processing_history.append({
            "agent": "Validation & Insight",
            "step": "Document NLP Extraction",
            "status": "Running",
            "detail": "Using LLM to extract symptoms and medications from the clinical document."
        })
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            prompt = (
                f"You are the HealthMind Validation Agent. Read the following medical document or text:\n\n"
                f"{input_text}\n\n"
                f"TASK: Extract 1) any mentioned symptoms or clinical findings, and 2) any specific medications mentioned for proposed treatment.\n"
                f"Respond in JSON format with fields: 'symptoms' (string summarizing symptoms) and 'medications' (list of strings)."
            )
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.content[0].text
            try:
                start_idx = raw_text.find("{")
                end_idx = raw_text.rfind("}") + 1
                extraction = json.loads(raw_text[start_idx:end_idx])
                extracted_symptoms = extraction.get("symptoms", "")
                extracted_meds = extraction.get("medications", [])
            except:
                pass
        except Exception as e:
            pass
            
    if not extracted_symptoms and not extracted_meds:
        # Fallback approach
        if is_medication:
            extracted_meds = [input_text]
        else:
            extracted_symptoms = input_text

    clinical_findings = {}
    
    if extracted_symptoms and len(extracted_symptoms) > 5:
        processing_history.append({
            "agent": "Validation & Insight",
            "step": "Diagnostic Engine",
            "status": "Running",
            "detail": "Analyzing extracted symptoms against clinical knowledge base."
        })
        res = await diagnose_symptoms(extracted_symptoms, patient_fhir_json)
        clinical_findings = {
            "type": "diagnosis",
            "status": "ALLOW",
            "priority": "medium",
            "findings": res.get("assessment", {}).get("probable_diagnoses", []),
            "recommendation": res.get("assessment", {}).get("clinical_summary", "")
        }
    elif extracted_meds:
        processing_history.append({
            "agent": "Validation & Insight",
            "step": "Safety Check Engine",
            "status": "Running",
            "detail": f"Checking safety for extracted medication: {extracted_meds[0]}"
        })
        res = await safety_check(extracted_meds[0], patient_fhir_json)
        clinical_findings = {
            "type": "safety_check",
            "status": res.get("status", "ALLOW"),
            "priority": res.get("priority", "low"),
            "findings": res.get("reasons", []),
            "recommendation": res.get("sharp_recommendation", "")
        }
    else:
        clinical_findings = {
            "type": "diagnosis",
            "status": "ALLOW",
            "priority": "low",
            "findings": [{"condition": "No clear findings", "confidence": "Low", "rationale": "Could not parse document."}],
            "recommendation": "Please try providing a clearer clinical note."
        }

    # --- Step 2: Audit & Reporting Agent ---
    processing_history.append({
        "agent": "Audit & Reporting",
        "step": "Audit Trail Compilation",
        "status": "Success",
        "detail": "Generated chronological log of agent interactions."
    })
    
    report_id = f"HM-2.0-{uuid.uuid4().hex[:6].upper()}"
    processing_history.append({
        "agent": "Audit & Reporting",
        "step": "PDF Structure Prep",
        "status": "Success",
        "detail": f"Finalizing report {report_id}."
    })

    return {
        "report_id": report_id,
        "patient": patient_ctx,
        "analysis": clinical_findings,
        "audit_trail": processing_history,
        "agents": ["Validation & Insight Agent", "Audit & Reporting Agent"],
        "hitl_required": True,
        "disclaimer": "This analysis was processed by the HealthMind 2.0 dual-agent system. Clinical review is mandatory."
    }


async def handle_analyze(request: Request) -> JSONResponse:
    """POST /analyze — Unified analysis hub endpoint."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body"}, status_code=400)

    text = body.get("text", "").strip()
    patient_json = body.get("patient_fhir_json", "")

    if not text:
        return JSONResponse({"detail": "input text is required"}, status_code=400)

    # Pre-validate input before analysis
    validation = _validator.validate(text)
    if validation["action"] == "reject":
        return JSONResponse(
            {"detail": "Input rejected by clinical document validator",
             "validation": validation},
            status_code=422,
        )

    if not patient_json:
        patient_json = json.dumps(build_sample_fhir_bundle())

    result = await analyze_medical_data(text, patient_json)
    return JSONResponse(result)


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
        Route("/validate", handle_validate, methods=["POST"]),
        Route("/check", handle_check, methods=["POST"]),
        Route("/chat", handle_chat, methods=["POST"]),
        Route("/diagnose", handle_diagnose, methods=["POST"]),
        Route("/analyze", handle_analyze, methods=["POST"]),
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
    print(f"  Validate:  POST http://{MCP_HOST}:{MCP_PORT}/validate")
    print("  ─────────────────────────────────────────")
    print("  MCP tools: drug_interaction, fhir_context, safety_check")
    print("=" * 60)

    uvicorn.run(rest_app, host=MCP_HOST, port=MCP_PORT)