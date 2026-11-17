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
import MyAttendance from './pages/MyAttendance'
import { authApi, isTeacherRole } from './services/api'

type Area = 'teacher' | 'student'

const RequireRole: React.FC<{ allow: Area; children: React.ReactElement }> = ({
  allow,
  children,
}) => {
  const hasToken =
    typeof window !== 'undefined' && Boolean(localStorage.getItem('access_token'))
  const hasSession = authApi.hasValidSession()

  if (!hasSession) {
    // A token that exists but no longer verifies (usually expired) gets an
    // explanation on the login page instead of a silent redirect.
    return <Navigate to={hasToken ? '/login?expired=1' : '/login'} replace />
  }

  const user = authApi.getCurrentUser()
  const teacher = isTeacherRole(user?.role)

  // A signed-in user is sent to the area that matches their real role.
  if (allow === 'teacher' && !teacher) {
    return <Navigate to="/my-attendance" replace />
  }
  if (allow === 'student' && teacher) {
    return <Navigate to="/" replace />
  }

  return children
}

const teacherOnly = (element: React.ReactElement) => (
  <RequireRole allow="teacher">{element}</RequireRole>
)

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={teacherOnly(<Dashboard />)} />
      <Route path="/take-attendance" element={teacherOnly(<TakeAttendance />)} />
      <Route path="/live-camera" element={teacherOnly(<LiveCamera />)} />
      <Route path="/students" element={teacherOnly(<Students />)} />
      <Route path="/subjects" element={teacherOnly(<Subjects />)} />
      <Route path="/analytics" element={teacherOnly(<Analytics />)} />
      <Route path="/reports" element={teacherOnly(<Reports />)} />
      <Route path="/ml-insights" element={teacherOnly(<MLInsights />)} />
      <Route path="/settings" element={teacherOnly(<Settings />)} />
      <Route
        path="/my-attendance"
        element={<RequireRole allow="student"><MyAttendance /></RequireRole>}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
