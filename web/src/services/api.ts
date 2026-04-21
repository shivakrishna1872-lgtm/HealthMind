import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg = err.response?.data?.detail ?? err.message ?? 'Unknown error'
    throw new Error(msg)
  },
)

export interface PatientInfo {
  name: string
  id: string
  age: number | null
  gender: string
  conditions: string[]
  medications: string[]
  allergies: string[]
}

export interface SafetyCheckResult {
  patient: PatientInfo
  proposed_medication: string
  fda_interactions: any[]
  status: 'BLOCK' | 'WARN' | 'ALLOW'
  priority: string
  reasons: string[]
  sharp_recommendation: string
  hitl_required: boolean
  disclaimer: string
}

export interface ChatResponse {
  reply: string
  session_id: string
  note?: string
}

export const api = {
  check: async (proposed_medication: string, patient_fhir_json: string | object) => {
    const payload = {
      proposed_medication,
      patient_fhir_json:
        typeof patient_fhir_json === 'string'
          ? patient_fhir_json
          : JSON.stringify(patient_fhir_json),
    }
    const { data } = await client.post<SafetyCheckResult>('/check', payload)
    return data
  },

  chat: async (message: string, sessionId: string, history: { role: string; content: string }[]) => {
    const { data } = await client.post<ChatResponse>('/chat', {
      message,
      session_id: sessionId,
      history,
    })
    return data
  },

  health: async () => {
    const { data } = await client.get('/health')
    return data
  },
}
