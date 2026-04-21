import { create } from 'zustand'

const STORAGE_KEY = 'healthmind_reports'

export interface SafetyReport {
  id: string
  proposed_medication: string
  status: 'BLOCK' | 'WARN' | 'ALLOW'
  priority: string
  reasons: string[]
  patient_name: string
  patient_conditions: string[]
  patient_medications: string[]
  sharp_recommendation: string
  hitl_required: boolean
  timestamp: number
}

interface ReportState {
  reports: SafetyReport[]
  addReport: (report: Omit<SafetyReport, 'id' | 'timestamp'>) => void
  loadReports: () => void
  clearReports: () => void
}

const genId = () => `report_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

export const useReportStore = create<ReportState>((set, get) => ({
  reports: [],

  addReport: (report) => {
    const newReport: SafetyReport = { ...report, id: genId(), timestamp: Date.now() }
    const updated = [newReport, ...get().reports]
    set({ reports: updated })
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(updated)) } catch {}
  },

  loadReports: () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) set({ reports: JSON.parse(stored) })
    } catch {}
  },

  clearReports: () => {
    set({ reports: [] })
    try { localStorage.removeItem(STORAGE_KEY) } catch {}
  },
}))
