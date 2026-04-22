import json
import unittest
from document_validator import DocumentValidator

class TestDocumentValidator(unittest.TestCase):
    def setUp(self):
        self.validator = DocumentValidator()

    def test_valid_clinical_note(self):
        input_text = "Patient is a 65-year-old male with CKD stage 3, currently taking Lisinopril. Proposed medication: Ibuprofen."
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "clinical_note")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["action"], "accept")

    def test_valid_fhir(self):
        input_text = json.dumps({
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "123",
                        "name": [{"given": ["Jane"], "family": "Doe"}]
                    }
                }
            ]
        })
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "FHIR")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["action"], "accept")

    def test_invalid_essay(self):
        input_text = "This essay discusses the importance of early diagnosis in chronic kidney disease..."
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "essay")
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["action"], "reject")

    def test_invalid_article(self):
        input_text = "Studies show that NSAIDs can increase the risk of kidney damage..."
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "article")
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["action"], "reject")

    def test_lab_report(self):
        input_text = "Lab results for John Doe: Creatinine 1.8 mg/dL, GFR 45 mL/min, Potassium 4.2 mEq/L."
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "lab_report")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["action"], "accept")

    def test_short_medication(self):
        input_text = "Lisinopril"
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "clinical_note")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["action"], "accept")

    def test_empty_input(self):
        input_text = ""
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "unknown")
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["action"], "reject")

    def test_ambiguous_input(self):
        input_text = "The quick brown fox jumps over the lazy dog."
        result = self.validator.validate(input_text)
        self.assertEqual(result["document_type"], "unknown")
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["action"], "reject")

if __name__ == "__main__":
    unittest.main()
