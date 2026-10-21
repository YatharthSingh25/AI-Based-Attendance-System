
import React from 'react'
import { Routes, Route } from 'react-router-dom'
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

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Dashboard />} />
      <Route path="/take-attendance" element={<TakeAttendance />} />
      <Route path="/live-camera" element={<LiveCamera />} />
      <Route path="/students" element={<Students />} />
      <Route path="/subjects" element={<Subjects />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/reports" element={<Reports />} />
      <Route path="/ml-insights" element={<MLInsights />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  )
}
