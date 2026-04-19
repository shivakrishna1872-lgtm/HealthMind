# HealthMind 🧠

> AI-powered prescription safety agent — built for the **Agents Assemble** hackathon.
> Uses FastMCP, openFDA, FHIR, and Human-in-the-Loop (HITL) validation.

**GitHub:** https://github.com/shivakrishna1872-lgtm/healthmind.git

## What it does

1. Loads the patient's conditions and medications from FHIR data (SHARP context)
2. Calls the openFDA drug interaction API via a FastMCP tool
3. Applies a Safety Buffer with specialized rules (CKD + NSAID = hard BLOCK)
4. Returns a SHARP-compliant recommendation — physician makes the final call (HITL)

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add ANTHROPIC_API_KEY to .env
python server.py
```

Mobile app:
```bash
cd mobile && npm install && npx expo start
```

## Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - HealthMind Safety Agent"
git branch -M main
git remote add origin https://github.com/shivakrishna1872-lgtm/healthmind.git
git push -u origin main
```

## Safety note

HealthMind is a decision-support tool only. Every recommendation must be reviewed
and approved by a licensed physician before any clinical action (HITL design).