import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileUp, Upload, Brain, ShieldCheck, 
  Search, FileText, Download, CheckCircle, 
  AlertCircle, History, Terminal, ChevronRight
} from 'lucide-react'
import * as pdfjs from 'pdfjs-dist'
import { api } from '../services/api'
import { SAMPLE_FHIR } from '../constants/sampleFhir'
import { generatePDF } from '../services/reportGenerator'

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.mjs`

export default function AnalysisHub() {
  const [inputText, setInputText] = useState('')
  const [useSample, setUseSample] = useState(true)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)

  const extractTextFromPDF = async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      const arrayBuffer = await file.arrayBuffer()
      const pdf = await pdfjs.getDocument(arrayBuffer).promise
      let fullText = ''
      
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i)
        const content = await page.getTextContent()
        const strings = content.items.map((item: any) => item.str)
        fullText += strings.join(' ') + '\n'
      }
      
      setInputText(fullText.trim())
    } catch (err: any) {
      setError(`Failed to read PDF: ${err.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.type === 'application/pdf') {
      extractTextFromPDF(file)
    } else {
      const reader = new FileReader()
      reader.onload = (re) => setInputText(re.target?.result as string)
      reader.readAsText(file)
    }
  }

  const runAnalysis = async () => {
    if (!inputText.trim() || loading) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.analyze(inputText, useSample ? SAMPLE_FHIR : {})
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'Analysis failed.')
    } finally {
      setLoading(false)
    }
  }

  const exportReport = () => {
    if (!result) return
    generatePDF({
      type: 'ANALYSIS',
      reportId: result.report_id,
      patient: {
        name: result.patient?.name || 'Unknown',
        age: result.patient?.age || 'N/A',
        gender: result.patient?.gender || 'N/A',
        conditions: result.patient?.conditions || [],
        medications: result.patient?.medications || [],
        allergies: result.patient?.allergies || [],
      },
      findings: {
        title: 'Unified Medical Analysis',
        status: result.analysis.status,
        priority: result.analysis.priority,
        content: result.analysis.findings,
        recommendation: result.analysis.recommendation,
      },
      auditTrail: result.audit_trail,
    })
  }

  return (
    <div className="page page-wide">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title">Medical Analysis Hub</h1>
        <p className="page-subtitle">Unified diagnostic and safety analysis powered by Dual-Agent processing.</p>
      </motion.div>

      <div className="grid-2" style={{ marginTop: 28, gridTemplateColumns: '1fr 1.2fr', alignItems: 'start' }}>
        
        {/* Left Column: Input */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          {/* Upload Area */}
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card interactive-card"
            style={{ border: '2px dashed var(--accent-glow)', padding: 30, textAlign: 'center' }}
          >
            <input 
              type="file" 
              id="file-upload" 
              hidden 
              onChange={handleFileUpload} 
              accept=".pdf,.txt"
            />
            <label htmlFor="file-upload" style={{ cursor: 'pointer' }}>
              <div style={{ 
                width: 50, height: 50, borderRadius: '50%', background: 'var(--accent-subtle)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px'
              }}>
                <FileUp size={24} color="var(--accent)" />
              </div>
              <div style={{ fontWeight: 600, fontSize: 16 }}>Upload Medical Document</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                Supports PDF reports, Lab Results, or Clinical Notes
              </div>
            </label>
            {uploading && (
              <div style={{ marginTop: 12, fontSize: 12, color: 'var(--accent)' }}>
                Extracting clinical text...
              </div>
            )}
          </motion.div>

          {/* Text Input */}
          <div className="card">
            <div className="section-label">CLINICAL DATA / TEXT</div>
            <textarea
              className="input textarea"
              placeholder="Paste medical text here or use upload above..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              style={{ minHeight: 200, fontSize: 13, marginTop: 10 }}
            />
            
            <div className="toggle-container" style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>Apply Jane Doe context</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Cross-ref Stage 3 CKD history</div>
              </div>
              <button 
                className={`toggle ${useSample ? 'active' : ''}`}
                onClick={() => setUseSample(!useSample)}
              >
                <span className="toggle-knob" />
              </button>
            </div>

            <button 
              className="btn btn-primary btn-block" 
              style={{ marginTop: 20 }}
              disabled={!inputText.trim() || loading}
              onClick={runAnalysis}
            >
              <Brain size={18} />
              {loading ? 'Agents Processing...' : 'Start Dual-Agent Analysis'}
            </button>
          </div>
        </div>

        {/* Right Column: Execution & Results */}
        <div>
          <AnimatePresence mode="wait">
            {!result && !loading && !error && (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }} 
                className="card"
                style={{ height: 500, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', color: 'var(--text-muted)' }}
              >
                <Search size={40} strokeWidth={1} style={{ marginBottom: 16, opacity: 0.3 }} />
                <div style={{ fontWeight: 500 }}>Ready for Analysis</div>
                <p style={{ fontSize: 13, maxWidth: 300, marginTop: 8 }}>
                  Upload a document or enter text to trigger the Validation and Audit agents.
                </p>
              </motion.div>
            )}

            {loading && (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card" style={{ height: 500 }}>
                <div className="section-label">AGENT PROCESSING LOG</div>
                <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div className="skeleton" style={{ height: 40 }} />
                  <div className="skeleton" style={{ height: 40, width: '90%' }} />
                  <div className="skeleton" style={{ height: 40, width: '95%' }} />
                  <div className="skeleton" style={{ height: 40, width: '85%' }} />
                </div>
              </motion.div>
            )}

            {error && (
              <motion.div key="error" className="card" style={{ borderLeft: '4px solid var(--danger)' }}>
                <div style={{ display: 'flex', gap: 12, color: 'var(--danger)' }}>
                  <AlertCircle size={20} />
                  <div>
                    <div style={{ fontWeight: 700 }}>System Error</div>
                    <div style={{ fontSize: 14, marginTop: 4 }}>{error}</div>
                  </div>
                </div>
              </motion.div>
            )}

            {result && (
              <motion.div 
                key="result"
                initial={{ opacity: 0, x: 20 }} 
                animate={{ opacity: 1, x: 0 }}
                style={{ display: 'flex', flexDirection: 'column', gap: 20 }}
              >
                {/* Findings Header */}
                <div className="card" style={{ borderLeft: '4px solid var(--accent)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <div>
                      <div className="section-label">ANALYSIS RESULT</div>
                      <div style={{ fontWeight: 800, fontSize: 18, marginTop: 4 }}>{result.analysis.type === 'safety_check' ? 'Medication Safety' : 'Diagnostic Insight'}</div>
                    </div>
                    <button className="btn btn-ghost btn-sm" onClick={exportReport}>
                      <Download size={14} /> Export Report
                    </button>
                  </div>
                  
                  <div className={`status-badge ${result.analysis.status === 'BLOCK' ? 'status-block' : 'status-warn'}`} style={{ marginBottom: 12 }}>
                    <span className="status-badge-dot" />
                    {result.analysis.status} — {result.analysis.priority.toUpperCase()} PRIORITY
                  </div>

                  {result.analysis.type === 'safety_check' ? (
                    <div>
                      {result.analysis.findings.map((reason: string, i: number) => (
                        <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8, paddingLeft: 2 }}>
                          <span style={{ color: result.analysis.status === 'BLOCK' ? 'var(--danger)' : 'var(--warning)', flexShrink: 0 }}>•</span>
                          <span style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>{reason}</span>
                        </div>
                      ))}
                      <div style={{ marginTop: 16, padding: 12, background: 'var(--bg-input)', borderRadius: 8, fontSize: 13, color: 'var(--text-secondary)', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                        {result.analysis.recommendation}
                      </div>
                    </div>
                  ) : (
                    <div>
                      <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text-secondary)', marginBottom: 16 }}>
                        {result.analysis.recommendation}
                      </p>
                      
                      <div className="section-label" style={{ marginBottom: 12 }}>DIFFERENTIAL DIAGNOSIS</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {result.analysis.findings.map((diag: any, i: number) => (
                          <div key={i} style={{ padding: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg-input)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div style={{ fontWeight: 700, fontSize: 14 }}>{diag.condition || 'Finding'}</div>
                              <div className="status-badge status-allow" style={{ padding: '2px 8px', fontSize: 11 }}>
                                {diag.confidence || 'Medium'} Confidence
                              </div>
                            </div>
                            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 6 }}>
                              {diag.rationale || diag}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Audit Trail (The 2nd Agent) */}
                <div className="card" style={{ background: '#0F172A', borderColor: '#1E293B' }}>
                  <div className="section-label" style={{ color: 'var(--accent)' }}>
                    <Terminal size={14} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                    AUDIT & REPORTING AGENT LOG
                  </div>
                  <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {result.audit_trail.map((log: any, i: number) => (
                      <div key={i} style={{ display: 'flex', gap: 12, fontSize: 12, color: '#94A3B8' }}>
                        <span style={{ color: '#64748B', fontFamily: 'monospace' }}>[{i+1}]</span>
                        <div style={{ flex: 1 }}>
                          <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{log.agent}</span>: {log.step}
                          <div style={{ color: '#475569', fontSize: 11, marginTop: 2 }}>{log.detail}</div>
                        </div>
                        <CheckCircle size={12} color="var(--success)" style={{ marginTop: 2 }} />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Disclaimer */}
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', padding: '0 20px' }}>
                  <ShieldCheck size={12} style={{ marginRight: 6, display: 'inline' }} />
                  {result.disclaimer}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
