import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Shield, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { useReportStore, SafetyReport } from '../store/reportStore'

const STATUS_CLASSES: Record<string, string> = {
  BLOCK: 'status-block',
  WARN: 'status-warn',
  ALLOW: 'status-allow',
}

function ReportCard({ report, index }: { report: SafetyReport; index: number }) {
  const cls = STATUS_CLASSES[report.status] || 'status-allow'
  const dateStr = format(new Date(report.timestamp), 'MMM d, yyyy · h:mm a')

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.35, ease: 'easeOut' }}
      className="card history-card"
    >
      <div className="history-card-left">
        <div className="history-card-med">{report.proposed_medication}</div>
        <div className="history-card-reason">
          {report.reasons[0] || 'No issues detected'}
        </div>
        <div className="history-card-meta">
          <span className="history-card-patient">Patient: {report.patient_name}</span>
          <span className="history-card-date">{dateStr}</span>
        </div>
      </div>
      <div className={`status-badge ${cls}`}>
        <span className="status-badge-dot" />
        {report.status}
      </div>
    </motion.div>
  )
}

export default function History() {
  const reports = useReportStore((s) => s.reports)
  const loadReports = useReportStore((s) => s.loadReports)
  const clearReports = useReportStore((s) => s.clearReports)

  useEffect(() => {
    loadReports()
  }, [loadReports])

  return (
    <div className="page">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
      >
        <div>
          <h1 className="page-title">History</h1>
          <p className="page-subtitle">Past safety check results and recommendations</p>
        </div>
        {reports.length > 0 && (
          <button className="btn btn-ghost btn-sm" onClick={clearReports}>
            <Trash2 size={14} />
            Clear
          </button>
        )}
      </motion.div>

      {reports.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.4 }}
          className="empty-state"
        >
          <div className="empty-state-icon">
            <Shield size={32} color="var(--text-muted)" />
          </div>
          <div className="empty-state-title">No checks yet</div>
          <div className="empty-state-desc">
            Run a safety check to see your results here.
          </div>
        </motion.div>
      ) : (
        <div className="history-list">
          <AnimatePresence>
            {reports.map((r, i) => (
              <ReportCard key={r.id} report={r} index={i} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
