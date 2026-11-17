import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi, isTeacherRole, type LoginTab } from '../services/api'

const Login: React.FC = () => {
  const [tab, setTab] = useState<LoginTab>('teacher')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  const switchTab = (next: LoginTab) => {
    setTab(next)
    setError(null)
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const response = await authApi.login(email, password, tab)
      const { access_token, user } = response.data || {}

      if (!access_token) {
        setError('Login failed: the server did not return an access token.')
        return
      }

      localStorage.setItem('access_token', access_token)
      if (user) {
        authApi.setCurrentUser(user)
      }

      navigate(isTeacherRole(user?.role) ? '/' : '/my-attendance', { replace: true })
    } catch (err: any) {
      const status = err?.response?.status
      const detail = err?.response?.data?.detail

      if (status === 401 && typeof detail === 'string' && detail.toLowerCase().includes('login tab')) {
        setError(detail)
      } else if (status === 401) {
        setError('Invalid email or password.')
      } else if (typeof detail === 'string') {
        setError(detail)
      } else if (detail) {
        setError(JSON.stringify(detail))
      } else {
        setError('Unable to reach the server. Check your connection and try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const isTeacherTab = tab === 'teacher'

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>AI Attendance System</h2>

        <div className="login-tabs" role="tablist" aria-label="Login type">
          <button
            type="button"
            role="tab"
            aria-selected={isTeacherTab}
            className={isTeacherTab ? 'login-tab active' : 'login-tab'}
            onClick={() => switchTab('teacher')}
          >
            Teacher
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={!isTeacherTab}
            className={!isTeacherTab ? 'login-tab active' : 'login-tab'}
            onClick={() => switchTab('student')}
          >
            Student
          </button>
        </div>

        <p className="login-hint">
          {isTeacherTab
            ? 'Take attendance and manage students.'
            : 'View your own attendance and profile.'}
        </p>

        <h3 className="login-heading">{isTeacherTab ? 'Teacher Login' : 'Student Login'}</h3>

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && (
            <p role="alert" className="form-error">
              {error}
            </p>
          )}
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting
              ? 'Logging in...'
              : isTeacherTab
                ? 'Login as Teacher'
                : 'Login as Student'}
          </button>
        </form>

        <p className="login-footnote">
          Students sign in with the email a teacher registered for them.
        </p>
      </div>
    </div>
  )
}

export default Login
