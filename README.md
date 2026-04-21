# HealthMind 🧠💊

**AI-Powered Prescription Safety Agent** — Built for the *Agents Assemble* Hackathon

HealthMind is an intelligent prescription safety system that combines real FDA adverse event data, FHIR R4 patient records, and clinical rule engines to help physicians make safer prescribing decisions. Every recommendation is flagged for **Human-in-the-Loop (HITL)** validation — the AI advises, the doctor decides.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   WEB APP (React + Vite)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   Home   │  │  Safety  │  │  Ask AI  │  │   History     │  │
│  │  Page    │  │  Check   │  │  Chat    │  │   Page        │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       │              │             │               │           │
│  ┌────┴──────────────┴─────────────┴───────────────┴───────┐  │
│  │          Zustand Store + localStorage                   │  │
│  └─────────────────────────┬───────────────────────────────┘  │
│                            │ HTTP/JSON                        │
└────────────────────────────┼──────────────────────────────────┘
                             │
                  ┌──────────┴──────────┐
                  │  FastMCP Backend    │
                  │  (Python + Starlette)│
                  ├─────────────────────┤
                  │  POST /check        │
                  │  POST /chat         │
                  │  GET  /health       │
                  ├─────────────────────┤
                  │  MCP Tools:         │
                  │  • drug_interaction │
                  │  • fhir_context     │
                  │  • safety_check     │
                  └──────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴───┐  ┌──────┴──────┐  ┌────┴────────┐
     │  openFDA   │  │  Safety     │  │  FHIR R4    │
     │  AERS API  │  │  Buffer     │  │  Parser     │
     │            │  │  (Rules)    │  │             │
     └────────────┘  └─────────────┘  └─────────────┘
```

---

## ✨ Features

- **Real FDA Data** — Queries openFDA Adverse Event Reporting System for drug-drug interactions
- **FHIR R4 Support** — Parses standard healthcare data bundles (Patient, Condition, MedicationRequest, AllergyIntolerance)
- **Clinical Rule Engine** — Hard-coded safety rules (CKD + NSAID = BLOCK, Warfarin + Aspirin = WARN, etc.)
- **SHARP Recommendations** — Formatted clinical recommendations with patient context and rationale
- **HITL Enforcement** — Every recommendation requires physician review (`hitl_required: true`)
- **AI Chat** — Natural language Q&A about medications, interactions, and safety guidelines
- **Premium Dark UI** — Glassmorphism-inspired design with framer-motion animations

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Clone & Setup

```bash
git clone https://github.com/shivakrishna1872-lgtm/HealthMind.git
cd HealthMind
```

### 2. Python Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your API keys (optional — works without them)

# Start the server
python server.py
```

The server will start at `http://0.0.0.0:8000`.

### 3. Web App

```bash
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open `http://localhost:3000` in your browser. The Vite dev server proxies API requests to the Python backend automatically.

---

## 🔧 MCP Tools

| Tool | Description |
|------|-------------|
| `drug_interaction(drug_a, drug_b)` | Query openFDA AERS for co-prescribed drug adverse events |
| `fhir_context(fhir_bundle_json)` | Parse a FHIR R4 Bundle into flat patient context |
| `safety_check(proposed_medication, patient_fhir_json)` | Full pipeline: FHIR parse → FDA query → Safety rules → SHARP recommendation |

---

## 🛡️ Safety Rules

| Condition | Drug | Decision |
|-----------|------|----------|
| Stage 3 CKD | Any NSAID | ⛔ BLOCK |
| CKD | Any NSAID | ⛔ BLOCK |
| Heart Failure | Any NSAID | ⛔ BLOCK |
| Pregnancy | Any NSAID | ⛔ BLOCK |
| Renal Failure | Any NSAID | ⛔ BLOCK |
| CKD | Metformin | ⚠️ WARN |
| Peptic Ulcer | Any NSAID | ⚠️ WARN |
| Warfarin (current) | Aspirin (proposed) | ⚠️ WARN |

---

## 📱 Tech Stack

**Backend:**
- FastMCP 0.4+ (Model Context Protocol)
- Starlette (REST endpoints + CORS)
- httpx (async HTTP to openFDA)
- Anthropic SDK (optional AI chat)

**Frontend:**
- React 18 + TypeScript
- Vite 5 (dev server + build)
- Framer Motion (animations)
- Zustand (state management)
- Lucide React (icons)
- date-fns (date formatting)

---

## 📄 License

MIT License — Built for educational and hackathon purposes.

---

## 🏁 Git Setup

```bash
git init
git add .
git commit -m "Initial commit - HealthMind Safety Agent"
git branch -M main
git remote add origin https://github.com/shivakrishna1872-lgtm/HealthMind.git
git push -u origin main
```
