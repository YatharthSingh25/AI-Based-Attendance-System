import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi, isTeacherRole } from '../services/api'

const TEACHER_LINKS = [
  { to: '/', label: 'Dashboard' },
  { to: '/take-attendance', label: 'Take Attendance' },
  { to: '/live-camera', label: 'Live Camera' },
  { to: '/students', label: 'Students' },
  { to: '/subjects', label: 'Subjects' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/reports', label: 'Reports' },
  { to: '/ml-insights', label: 'ML Insights' },
  { to: '/settings', label: 'Settings' },
]

const STUDENT_LINKS = [{ to: '/my-attendance', label: 'My Attendance' }]

const Sidebar: React.FC<{ teacher: boolean }> = ({ teacher }) => {
  const links = teacher ? TEACHER_LINKS : STUDENT_LINKS

  return (
    <nav className="sidebar" aria-label="Main navigation">
      <ul>
        {links.map((link) => (
          <li key={link.to}>
            <Link to={link.to}>{link.label}</Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}

const Header: React.FC = () => {
  const navigate = useNavigate()
  const user = authApi.getCurrentUser()

  const handleLogout = () => {
    authApi.logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="top-bar">
      <div className="header-left">
        <h1>AI Attendance System</h1>
      </div>
      <div className="header-right">
        <span className="faculty-name">{user?.name || user?.email || 'User'}</span>
        <span className="role-pill">{isTeacherRole(user?.role) ? 'Teacher' : 'Student'}</span>
        <button type="button" className="btn-outline" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  )
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const user = authApi.getCurrentUser()

  return (
    <div className="app-container">
      <Sidebar teacher={isTeacherRole(user?.role)} />
      <Header />
      <main>{children}</main>
    </div>
  )
}
