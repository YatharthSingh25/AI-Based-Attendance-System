import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TakeAttendance from './pages/TakeAttendance'
import LiveCamera from './pages/LiveCamera'
import Students from './pages/Students'
import Subjects from './pages/Subjects'
import Analytics from './pages/Analytics'
import Reports from './pages/Reports'
import MLInsights from './pages/MLInsights'
import Settings from './pages/Settings'

const RequireAuth: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
      <Route path="/take-attendance" element={<RequireAuth><TakeAttendance /></RequireAuth>} />
      <Route path="/live-camera" element={<RequireAuth><LiveCamera /></RequireAuth>} />
      <Route path="/students" element={<RequireAuth><Students /></RequireAuth>} />
      <Route path="/subjects" element={<RequireAuth><Subjects /></RequireAuth>} />
      <Route path="/analytics" element={<RequireAuth><Analytics /></RequireAuth>} />
      <Route path="/reports" element={<RequireAuth><Reports /></RequireAuth>} />
      <Route path="/ml-insights" element={<RequireAuth><MLInsights /></RequireAuth>} />
      <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
