import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  authApi,
  isTeacherRole,
  SESSION_EXPIRED_PARAM,
  type LoginTab,
} from '../services/api'

type Mode = 'signin' | 'activate'

const describeError = (error: any, fallback: string): string => {
  const status = error?.response?.status
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    // FastAPI validation errors: surface the first field problem.
    const first = detail[0]
    const field = Array.isArray(first?.loc) ? first.loc[first.loc.length - 1] : null
    const message = first?.msg || 'invalid value'
    return field ? `${field}: ${message}` : message
  }
  if (status === 409) {
    return 'This email already has a password. Sign in with it instead.'
  }
  if (status === 404) {
    return 'No student record uses this email. Ask your teacher to add you before setting a password.'
  }
  if (error?.message) return `${fallback} (${error.message})`
  return fallback
}

const Login: React.FC = () => {
  const [tab, setTab] = useState<LoginTab>('teacher')
  const [mode, setMode] = useState<Mode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // The API layer redirects here with ?expired=1 after clearing a rejected
  // token. Explain why, then drop the marker so a reload is quiet.
  useEffect(() => {
    if (searchParams.get(SESSION_EXPIRED_PARAM) !== '1') return

    setNotice('Your session expired. Please sign in again.')
    const next = new URLSearchParams(searchParams)
    next.delete(SESSION_EXPIRED_PARAM)
    setSearchParams(next, { replace: true })
  }, [searchParams, setSearchParams])

  const switchTab = (next: LoginTab) => {
    setTab(next)
    setMode('signin')
    setError(null)
  }

  const storeSession = (data: any) => {
    localStorage.setItem('access_token', data.access_token)
    if (data.user) {
      authApi.setCurrentUser(data.user)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setNotice(null)
    setSubmitting(true)

    try {
      const response = await authApi.login(email, password, tab)
      const { access_token, user } = response.data || {}

      if (!access_token) {
        setError('Login failed: the server did not return an access token.')
        return
      }

      storeSession(response.data)
      navigate(isTeacherRole(user?.role) ? '/' : '/my-attendance', { replace: true })
    } catch (err: any) {
      const status = err?.response?.status
      const detail = err?.response?.data?.detail

      if (status === 401 && typeof detail === 'string' && detail.toLowerCase().includes('login tab')) {
        setError(detail)
      } else if (status === 401) {
        // Do not reveal whether the address exists.
        setError('Invalid email or password.')
      } else {
        setError(
          describeError(
            err,
            'Unable to reach the server. Check your connection and try again.'
          )
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  const openActivation = () => {
    setMode('activate')
    setPassword('')
    setConfirmPassword('')
    setError(null)
    setNotice(null)
  }

  const closeActivation = () => {
    setMode('signin')
    setPassword('')
    setConfirmPassword('')
    setError(null)
  }

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setNotice(null)

    const address = email.trim()
    if (!address) {
      setError('Enter the email your teacher registered for you.')
      return
    }
    if (password.length < 6) {
      setError('Choose a password with at least 6 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('The two passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      const response = await authApi.activate(address, password)
      const { access_token } = response.data || {}
      if (!access_token) {
        setError('Password saved, but the server did not sign you in. Try signing in.')
        setMode('signin')
        return
      }

      storeSession(response.data)
      navigate('/my-attendance', { replace: true })
    } catch (err: any) {
      setError(describeError(err, 'Could not set your password. Try again.'))
    } finally {
      setSubmitting(false)
    }
  }

  const isTeacherTab = tab === 'teacher'
  const activating = mode === 'activate'

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>AI Attendance System</h2>

        {!activating && (
          <>
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
          </>
        )}

        <h3 className="login-heading">
          {activating
            ? 'First-Time Password'
            : isTeacherTab
              ? 'Teacher Login'
              : 'Student Login'}
        </h3>

        {activating && (
          <p className="login-hint">
            Use the email your teacher registered for you, then choose a
            password. You will use it every time you sign in.
          </p>
        )}

        {notice && (
          <p role="status" className="form-warning">
            {notice}
          </p>
        )}

        <form onSubmit={activating ? handleActivate : handleLogin}>
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
            <label>{activating ? 'New password' : 'Password'}</label>
            <input
              type="password"
              placeholder={activating ? 'At least 6 characters' : 'Enter your password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={activating ? 'new-password' : 'current-password'}
              required
              minLength={activating ? 6 : undefined}
            />
          </div>

          {activating && (
            <div className="form-group">
              <label>Confirm password</label>
              <input
                type="password"
                placeholder="Type the password again"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                required
                minLength={6}
              />
            </div>
          )}

          {error && (
            <p role="alert" className="form-error">
              {error}
            </p>
          )}

          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting
              ? activating
                ? 'Saving...'
                : 'Logging in...'
              : activating
                ? 'Set Password & Sign In'
                : isTeacherTab
                  ? 'Login as Teacher'
                  : 'Login as Student'}
          </button>

          {activating && (
            <button
              type="button"
              className="btn-outline login-secondary"
              onClick={closeActivation}
            >
              Back to sign in
            </button>
          )}
        </form>

        {!activating && !isTeacherTab && (
          <div className="login-footnote">
            <p>First time signing in? Your teacher added your email, so set your password now.</p>
            <button type="button" className="link-button" onClick={openActivation}>
              Set your password
            </button>
          </div>
        )}

        {!activating && isTeacherTab && (
          <p className="login-footnote">
            Students sign in with the email a teacher registered for them.
          </p>
        )}
      </div>
    </div>
  )
}

export default Login
