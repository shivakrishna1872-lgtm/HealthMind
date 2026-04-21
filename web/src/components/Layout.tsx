import { NavLink, Outlet } from 'react-router-dom'
import { Home, ClipboardCheck, MessageSquare, Clock, Users } from 'lucide-react'

const navItems = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/analysis', icon: ClipboardCheck, label: 'Analysis Hub' },
  { to: '/chat', icon: MessageSquare, label: 'Ask AI' },
  { to: '/history', icon: Clock, label: 'History' },
]

export default function Layout() {
  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>🧠 HealthMind 2.0</h1>
          <p>Dual-Agent Clinical Platform</p>
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
              <strong>HITL CERTIFIED</strong>
              Processing history is audited for safety. Doctor review mandatory.
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
