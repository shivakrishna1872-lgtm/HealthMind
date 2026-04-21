import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Stethoscope, AlertCircle, FileText, Download, Users, ChevronRight } from 'lucide-react'
import { api } from '../services/api'
import { SAMPLE_FHIR } from '../constants/sampleFhir'
import { generatePDF } from '../services/reportGenerator'

export default function Diagnosis() {
  const [symptoms, setSymptoms] = useState('')
  const [useSample, setUseSample] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = symptoms.trim().length > 10 && !loading

  const runDiagnosis = async () => {
    if (!canSubmit) return
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const res = await api.diagnose(symptoms.trim(), useSample ? SAMPLE_FHIR : {})
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'Diagnostic assessment failed.')
    } finally {
      setLoading(false)
    }
  }

  const exportReport = () => {
    if (!result) return
    generatePDF({
      type: 'DIAGNOSIS',
      patient: {
        name: result.patient?.name || 'Unknown',
        age: result.patient?.age || 'N/A',
        gender: result.patient?.gender || 'N/A',
        conditions: result.patient?.conditions || [],
        medications: result.patient?.medications || [],
        allergies: result.patient?.allergies || [],
      },
      findings: {
        title: 'Diagnostic Assessment',
        content: symptoms,
        differential: result.assessment?.probable_diagnoses || [],
        recommendation: result.assessment?.clinical_summary,
      },
    } as any)
  }

  return (
    <div className="page">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="page-title">Diagnostic Agent</h1>
        <p className="page-subtitle">Analyze complex symptoms against patient history to determine differential diagnosis.</p>
      </motion.div>

      {/* Symptom Input */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        style={{ marginTop: 28 }}
      >
        <label className="input-label">PATIENT SYMPTOMS & PRESENTATION</label>
        <textarea
          className="input textarea"
          placeholder="Describe symptoms in detail (e.g., patient reports sudden onset shortness of breath and bilateral ankle edema...)"
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          style={{ minHeight: 180, borderColor: symptoms.length > 10 ? 'var(--accent)' : undefined }}
        />
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, textAlign: 'right' }}>
          Minimum 10 characters required for clinical analysis.
        </div>
      </motion.div>

      {/* Settings Card */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="card"
        style={{ marginTop: 20 }}
      >
        <div className="toggle-container">
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
              Context: Jane Doe (Sample)
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 3 }}>
              History: Stage 3 CKD, Hypertension. Current Meds: Lisinopril, Furosemide.
            </div>
          </div>
          <button
            className={`toggle ${useSample ? 'active' : ''}`}
            onClick={() => setUseSample(!useSample)}
            type="button"
          >
            <span className="toggle-knob" />
          </button>
        </div>
      </motion.div>

      {/* Run Button */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.4 }}
        style={{ marginTop: 20 }}
      >
        <button className="btn btn-primary btn-block" disabled={!canSubmit} onClick={runDiagnosis}>
          <Brain size={18} />
          {loading ? 'Analyzing Clinical Context...' : 'Run Differential Diagnosis'}
        </button>
      </motion.div>

      {/* Loading Skeletons */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 14 }}
          >
            <div className="skeleton" style={{ height: 120 }} />
            <div className="skeleton" style={{ height: 200 }} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              marginTop: 24, padding: 20,
              background: 'var(--danger-bg)', border: '1px solid var(--danger-border)',
              borderRadius: 'var(--radius-lg)', display: 'flex', gap: 12,
            }}
          >
            <AlertCircle size={20} color="var(--danger)" />
            <div style={{ color: 'var(--danger)', fontSize: 14 }}>{error}</div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            style={{ marginTop: 28, display: 'flex', flexDirection: 'column', gap: 20 }}
          >
            {/* Header / Summary */}
            <div className="card" style={{ borderLeft: '4px solid var(--accent)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div className="section-label">ASSESSMENT SUMMARY</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
                    Diagnostic Impression
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={exportReport}>
                  <Download size={14} />
                  Export PDF
                </button>
              </div>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 12, lineHeight: 1.6 }}>
                {result.assessment?.clinical_summary || 'Analysis complete.'}
              </p>
              {result.assessment?.urgent_flag && (
                <div style={{ 
                  marginTop: 14, padding: '8px 14px', borderRadius: 8, 
                  background: 'var(--danger-bg)', border: '1px solid var(--danger-border)',
                  color: 'var(--danger)', fontSize: 12, fontWeight: 700, display: 'inline-flex', gap: 8 
                }}>
                  <AlertCircle size={14} /> URGENT MEDICAL ATTENTION REQUIRED
                </div>
              )}
            </div>

            {/* Differential Diagnosis Table */}
            <div>
              <div className="section-label">DIFFERENTIAL DIAGNOSIS</div>
              <div className="history-list">
                {result.assessment?.probable_diagnoses.map((diag: any, i: number) => (
                  <motion.div 
                    key={i} 
                    initial={{ opacity: 0, x: -10 }} 
                    animate={{ opacity: 1, x: 0 }} 
                    transition={{ delay: i * 0.1 }}
                    className="card" 
                    style={{ marginBottom: 10 }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontWeight: 700, fontSize: 15 }}>{diag.condition}</div>
                      <div className="status-badge status-allow">
                        <span className="status-badge-dot" />
                        {diag.confidence} Confidence
                      </div>
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>
                      {diag.rationale}
                    </p>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Next Steps */}
            <div className="card">
              <div className="section-label">RECOMMENDED NEXT STEPS</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                {result.assessment?.recommended_next_steps.map((step: string, i: number) => (
                  <div key={i} style={{ 
                    padding: 12, background: 'var(--bg-input)', borderRadius: 10,
                    fontSize: 13, display: 'flex', alignItems: 'center', gap: 10
                  }}>
                    <ChevronRight size={14} color="var(--accent)" />
                    {step}
                  </div>
                ))}
              </div>
            </div>

            {/* HITL Notice */}
            <div style={{
              padding: 20, background: 'var(--accent-subtle)',
              border: '1px solid var(--accent-glow)', borderRadius: 'var(--radius-lg)',
              display: 'flex', gap: 12, alignItems: 'flex-start',
            }}>
              <Users size={18} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent)', letterSpacing: 0.8, marginBottom: 4 }}>
                  HITL DIAGNOSTIC WARNING
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {result.disclaimer}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
