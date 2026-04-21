import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ShieldCheck, XCircle, AlertTriangle, CheckCircle, Users, AlertCircle, ChevronDown, ChevronUp, Download } from 'lucide-react'
import { api, SafetyCheckResult } from '../services/api'
import { SAMPLE_FHIR } from '../constants/sampleFhir'
import { useReportStore } from '../store/reportStore'
import { generatePDF } from '../services/reportGenerator'

const STATUS_CONFIG = {
  BLOCK: {
    bannerClass: 'status-banner-block',
    badgeClass: 'status-block',
    icon: XCircle,
    color: 'var(--danger)',
    label: 'BLOCKED',
  },
  WARN: {
    bannerClass: 'status-banner-warn',
    badgeClass: 'status-warn',
    icon: AlertTriangle,
    color: 'var(--warning)',
    label: 'WARNING',
  },
  ALLOW: {
    bannerClass: 'status-banner-allow',
    badgeClass: 'status-allow',
    icon: CheckCircle,
    color: 'var(--success)',
    label: 'ALLOWED',
  },
}

export default function SafetyCheck() {
  const [medication, setMedication] = useState('')
  const [useSample, setUseSample] = useState(true)
  const [customFhir, setCustomFhir] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SafetyCheckResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showRaw, setShowRaw] = useState(false)
  const addReport = useReportStore((s) => s.addReport)

  const canSubmit = medication.trim().length > 0 && !loading

  const runCheck = async () => {
    if (!canSubmit) return
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      let fhirData: string | object
      if (useSample) {
        fhirData = SAMPLE_FHIR
      } else {
        const trimmed = customFhir.trim()
        if (!trimmed) {
          setError('Please paste a FHIR JSON bundle or enable the sample patient.')
          setLoading(false)
          return
        }
        try {
          fhirData = JSON.parse(trimmed)
        } catch {
          setError('Invalid JSON. Please check your FHIR bundle.')
          setLoading(false)
          return
        }
      }

      const res = await api.check(medication.trim(), fhirData)
      setResult(res)

      addReport({
        proposed_medication: res.proposed_medication,
        status: res.status,
        priority: res.priority,
        reasons: res.reasons,
        patient_name: res.patient?.name || 'Unknown',
        patient_conditions: res.patient?.conditions || [],
        patient_medications: res.patient?.medications || [],
        sharp_recommendation: res.sharp_recommendation,
        hitl_required: res.hitl_required,
      })
    } catch (err: any) {
      setError(err.message || 'Failed to perform safety check. Is the server running?')
    } finally {
      setLoading(false)
    }
  }

  const exportReport = () => {
    if (!result) return
    generatePDF({
      type: 'SAFETY_CHECK',
      patient: {
        name: result.patient?.name || 'Unknown',
        age: result.patient?.age || 'N/A',
        gender: result.patient?.gender || 'N/A',
        conditions: result.patient?.conditions || [],
        medications: result.patient?.medications || [],
        allergies: result.patient?.allergies || [],
      },
      findings: {
        title: 'Safety Check Result',
        status: result.status,
        priority: result.priority,
        content: result.reasons,
        recommendation: result.sharp_recommendation,
      },
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && canSubmit) runCheck()
  }

  const cfg = result ? STATUS_CONFIG[result.status] : null

  return (
    <div className="page">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="page-title">Safety Check</h1>
        <p className="page-subtitle">
          Enter a medication to check against patient data for contraindications and drug interactions.
        </p>
      </motion.div>

      {/* Medication Input */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        style={{ marginTop: 28 }}
      >
        <label className="input-label">PROPOSED MEDICATION</label>
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            className="input"
            type="text"
            placeholder="e.g., Ibuprofen, Metformin, Aspirin..."
            value={medication}
            onChange={(e) => setMedication(e.target.value)}
            onKeyDown={handleKeyDown}
            style={{ borderColor: medication ? 'var(--accent)' : undefined }}
          />
        </div>
      </motion.div>

      {/* Patient Source Toggle */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
        className="card"
        style={{ marginTop: 18 }}
      >
        <div className="toggle-container">
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
              Use Sample Patient
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 3 }}>
              Jane Doe — Stage 3 CKD, Hypertension, Lisinopril, Furosemide
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

        <AnimatePresence>
          {!useSample && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              style={{ overflow: 'hidden' }}
            >
              <textarea
                className="input textarea"
                placeholder="Paste your FHIR R4 Bundle JSON here..."
                value={customFhir}
                onChange={(e) => setCustomFhir(e.target.value)}
                style={{ marginTop: 16 }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Run Button */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.4 }}
        style={{ marginTop: 20 }}
      >
        <button className="btn btn-primary btn-block" disabled={!canSubmit} onClick={runCheck}>
          <ShieldCheck size={18} />
          {loading ? 'Analyzing Clinical Rules...' : 'Run Safety Check'}
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
            <div className="skeleton" style={{ height: 100 }} />
            <div className="skeleton" style={{ height: 80 }} />
            <div className="skeleton" style={{ height: 60, width: '70%' }} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && cfg && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            style={{ marginTop: 28, display: 'flex', flexDirection: 'column', gap: 18 }}
          >
            {/* Status Banner */}
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.35 }}
              className={`status-banner ${cfg.bannerClass}`}
              style={{ position: 'relative' }}
            >
              <div className="status-banner-icon">
                <cfg.icon size={30} color={cfg.color} />
              </div>
              <div style={{ flex: 1 }}>
                <div className="status-banner-label">{cfg.label}</div>
                <div className="status-banner-sub">
                  {result.proposed_medication} — Priority: {result.priority.toUpperCase()}
                </div>
              </div>
              <button 
                className="btn btn-ghost btn-sm" 
                onClick={exportReport}
                style={{ height: 40, background: 'rgba(255,255,255,0.05)' }}
              >
                <Download size={16} />
                Export PDF
              </button>
            </motion.div>

            {/* Clinical Rationale */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.35 }}
              className="card"
            >
              <div className="section-label">CLINICAL RATIONALE</div>
              {result.reasons.map((reason, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 10, paddingLeft: 2 }}>
                  <span style={{ color: cfg.color, flexShrink: 0 }}>•</span>
                  <span style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>{reason}</span>
                </div>
              ))}
            </motion.div>

            {/* Patient Context */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.35 }}
              className="card"
            >
              <div className="section-label">PATIENT CONTEXT</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                <InfoRow label="Name" value={result.patient?.name || 'Unknown'} />
                <InfoRow label="Age / Gender" value={`${result.patient?.age ?? 'N/A'} / ${result.patient?.gender || 'N/A'}`} />
                <InfoRow label="Conditions" value={result.patient?.conditions?.join(', ') || 'None documented'} />
                <InfoRow label="Current Medications" value={result.patient?.medications?.join(', ') || 'None documented'} />
              </div>
            </motion.div>

            {/* SHARP Recommendation (Collapsible) */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.35 }}
              className="card"
            >
              <button
                onClick={() => setShowRaw(!showRaw)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  width: '100%', background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--text-secondary)', fontFamily: 'inherit', padding: 0,
                }}
              >
                <span className="section-label" style={{ margin: 0 }}>SHARP CLINICAL RECOMMENDATION</span>
                {showRaw ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>
              <AnimatePresence>
                {showRaw && (
                  <motion.pre
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{
                      marginTop: 12, padding: 16, background: 'var(--bg-input)', borderRadius: 'var(--radius-md)',
                      fontSize: 12, lineHeight: 1.7, overflow: 'auto', color: 'var(--text-secondary)',
                      fontFamily: "'SF Mono', 'Fira Code', monospace", whiteSpace: 'pre-wrap',
                    }}
                  >
                    {result.sharp_recommendation}
                  </motion.pre>
                )}
              </AnimatePresence>
            </motion.div>

            {/* HITL Notice */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.35 }}
              style={{
                padding: 20, background: 'var(--accent-subtle)',
                border: '1px solid var(--accent-glow)', borderRadius: 'var(--radius-lg)',
                display: 'flex', gap: 12, alignItems: 'flex-start',
              }}
            >
              <Users size={18} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent)', letterSpacing: 0.8, marginBottom: 4 }}>
                  HITL SAFETY PROTOCOL
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {result.disclaimer}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: 0.3, marginBottom: 3 }}>
        {label}
      </div>
      <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.5 }}>{value}</div>
    </div>
  )
}
