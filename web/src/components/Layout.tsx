import { NavLink, Outlet } from 'react-router-dom'
import { Home, ShieldCheck, MessageSquare, Clock, Users } from 'lucide-react'

const navItems = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/safety-check', icon: ShieldCheck, label: 'Safety Check' },
  { to: '/chat', icon: MessageSquare, label: 'Ask AI' },
  { to: '/history', icon: Clock, label: 'History' },
]

export default function Layout() {
  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>🧠 HealthMind</h1>
          <p>Prescription Safety Agent</p>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'active' : ''}`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="hitl-badge">
            <Users size={16} color="var(--accent)" style={{ flexShrink: 0, marginTop: 2 }} />
            <p>
              <strong>HUMAN-IN-THE-LOOP</strong>
              All AI recommendations require physician review. HealthMind assists — the doctor decides.
            </p>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
