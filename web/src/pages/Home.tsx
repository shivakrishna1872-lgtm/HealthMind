import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  ClipboardCheck, MessageSquare, Clock, 
  ArrowRight, FileUp, Terminal, Shield, 
  Database, Activity, Brain
} from 'lucide-react'

const cards = [
  {
    to: '/analysis',
    icon: ClipboardCheck,
    color: 'var(--accent)',
    bg: 'var(--accent-subtle)',
    title: 'Medical Analysis Hub',
    desc: 'The central area for all clinical processing. Upload PDFs, lab results, or type symptoms to trigger the Dual-Agent system.',
  },
  {
    to: '/chat',
    icon: MessageSquare,
    color: '#A78BFA',
    bg: 'rgba(167, 139, 250, 0.1)',
    title: 'Ask AI Helper',
    desc: 'Chat with HealthMind about medical standards, drug risks, and clinical workflow guidelines.',
  },
]

const stats = [
  { icon: Terminal, value: 'Active', label: 'Audit Agent' },
  { icon: Brain, value: 'Integrated', label: 'Clinical Agent' },
  { icon: Database, value: 'FHIR R4', label: 'Compliance' },
  { icon: Activity, value: 'OCR', label: 'PDF extraction' },
]

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.1 } },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
}

export default function Home() {
  return (
    <div className="page page-wide">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 12 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: 'var(--accent-subtle)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', fontSize: 28,
            boxShadow: '0 8px 16px -4px var(--accent-glow)'
          }}>
            🧠
          </div>
          <div>
            <h1 className="page-title" style={{ fontSize: 32 }}>HealthMind 2.0</h1>
            <p className="page-subtitle">Dual-Agent Clinical Data Analysis & Reporting</p>
          </div>
        </div>
      </motion.div>

      {/* Primary Actions */}
      <motion.div
        className="home-grid"
        variants={container}
        initial="hidden"
        animate="show"
        style={{ marginTop: 32, gridTemplateColumns: '1.2fr 0.8fr' }}
      >
        {cards.map(({ to, icon: Icon, color, bg, title, desc }) => (
          <motion.div key={to} variants={item}>
            <Link to={to} className="home-card">
              <div className="card card-hover card-interactive" style={{ height: '100%', padding: 28 }}>
                <div className="home-card-icon" style={{ background: bg, width: 50, height: 50 }}>
                  <Icon size={24} color={color} />
                </div>
                <div>
                  <div className="home-card-title" style={{ fontSize: 20 }}>{title}</div>
                  <div className="home-card-desc" style={{ fontSize: 14, marginTop: 10 }}>{desc}</div>
                </div>
                <div className="home-card-arrow">
                  <ArrowRight size={20} />
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </motion.div>

      {/* System Integrity Row */}
      <motion.div
        className="stats-row"
        variants={container}
        initial="hidden"
        animate="show"
        style={{ marginTop: 24 }}
      >
        {stats.map(({ icon: Icon, value, label }, i) => (
          <motion.div key={i} variants={item} className="card stat-card" style={{ padding: '20px 10px' }}>
            <Icon size={18} color="var(--accent)" style={{ marginBottom: 8 }} />
            <div className="stat-value" style={{ fontSize: 16 }}>{value}</div>
            <div className="stat-label" style={{ fontSize: 11 }}>{label}</div>
          </motion.div>
        ))}
      </motion.div>

      {/* Audit Banner */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.6 }}
        style={{
          marginTop: 32,
          padding: '24px 30px',
          background: 'var(--bg-input)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 20
        }}
      >
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Shield size={24} color="var(--accent)" />
          <div>
            <div style={{ fontWeight: 700, fontSize: 15 }}>Transparency & Accountability</div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>
              Every medical analysis generates a detailed Audit Log from the Reporting Agent.
            </p>
          </div>
        </div>
        <div className="hitl-badge" style={{ background: 'var(--accent-subtle)', borderColor: 'var(--accent-glow)', margin: 0 }}>
          HITL 2.0 PROTOCOL
        </div>
      </motion.div>
    </div>
  )
}
