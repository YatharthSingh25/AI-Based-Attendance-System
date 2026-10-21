import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'

const Sidebar: React.FC = () => {
  return (
    <nav className="sidebar">
      <ul>
        <li>
          <Link to="/">Dashboard</Link>
        </li>
        <li>
          <Link to="/take-attendance">Take Attendance</Link>
        </li>
        <li>
          <Link to="/live-camera">Live Camera</Link>
        </li>
        <li>
          <Link to="/students">Students</Link>
        </li>
        <li>
          <Link to="/subjects">Subjects</Link>
        </li>
        <li>
          <Link to="/analytics">Analytics</Link>
        </li>
        <li>
          <Link to="/reports">Reports</Link>
        </li>
        <li>
          <Link to="/ml-insights">ML Insights</Link>
        </li>
        <li>
          <Link to="/settings">Settings</Link>
        </li>
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
        <span className="faculty-name">{user?.name || user?.email || 'Faculty'}</span>
        <button type="button" className="btn-outline" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  )
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-container">
      <Sidebar />
      <Header />
      <main>{children}</main>
    </div>
  )
}