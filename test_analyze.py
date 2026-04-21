import asyncio
import json
from server import analyze_medical_data

async def test():
    input_text = "Patient reports severe chest pain and shortness of breath. Current medication: Ibuprofen 200mg."
    patient_fhir_json = json.dumps({
        "resourceType": "Bundle",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "123", "name": [{"given": ["Jane", "Doe"]}]}}
        ]
    })
    try:
        res = await analyze_medical_data(input_text, patient_fhir_json)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
