export const SAMPLE_FHIR = {
  resourceType: 'Bundle',
  type: 'collection',
  entry: [
    {
      resource: {
        resourceType: 'Patient',
        id: 'patient-jane-doe-001',
        name: [{ use: 'official', given: ['Jane'], family: 'Doe' }],
        gender: 'female',
        birthDate: '1965-04-12',
      },
    },
    {
      resource: {
        resourceType: 'Condition',
        id: 'condition-ckd-001',
        subject: { reference: 'Patient/patient-jane-doe-001' },
        code: {
          coding: [{ system: 'http://snomed.info/sct', code: '433144002', display: 'Stage 3 Chronic Kidney Disease' }],
          text: 'Stage 3 Chronic Kidney Disease',
        },
        clinicalStatus: { coding: [{ system: 'http://terminology.hl7.org/CodeSystem/condition-clinical', code: 'active' }] },
      },
    },
    {
      resource: {
        resourceType: 'Condition',
        id: 'condition-htn-001',
        subject: { reference: 'Patient/patient-jane-doe-001' },
        code: {
          coding: [{ system: 'http://snomed.info/sct', code: '38341003', display: 'Hypertension' }],
          text: 'Hypertension',
        },
        clinicalStatus: { coding: [{ system: 'http://terminology.hl7.org/CodeSystem/condition-clinical', code: 'active' }] },
      },
    },
    {
      resource: {
        resourceType: 'MedicationRequest',
        id: 'medrx-lisinopril-001',
        status: 'active',
        intent: 'order',
        subject: { reference: 'Patient/patient-jane-doe-001' },
        medicationCodeableConcept: {
          coding: [{ system: 'http://www.nlm.nih.gov/research/umls/rxnorm', code: '314076', display: 'Lisinopril 10 MG' }],
          text: 'Lisinopril 10 MG',
        },
      },
    },
    {
      resource: {
        resourceType: 'MedicationRequest',
        id: 'medrx-furosemide-001',
        status: 'active',
        intent: 'order',
        subject: { reference: 'Patient/patient-jane-doe-001' },
        medicationCodeableConcept: {
          coding: [{ system: 'http://www.nlm.nih.gov/research/umls/rxnorm', code: '310429', display: 'Furosemide 40 MG' }],
          text: 'Furosemide 40 MG',
        },
      },
    },
  ],
}
