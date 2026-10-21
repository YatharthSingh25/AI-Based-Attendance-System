import React, { useEffect, useState } from 'react'
import { Badge, Table } from '../components/ui'
import Layout from '../layouts/MainLayout'
import { attendanceApi } from '../services/api'

interface AttendanceSession {
  id: string
  subject: string
  section: string
  date?: string
  start_time?: string
  end_time?: string
}

interface PersistedAttendance {
  id: number
  student_id: number
  status: string
  confidence: number | null
  method: string
  timestamp: string
  verified: boolean
}

interface SimulatedFace {
  student: string
  confidence: number
  status: 'present' | 'review' | 'unknown'
  name: string
}

const errorMessage = (error: any, fallback: string): string => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail) return JSON.stringify(detail)
  if (error?.message) return `${fallback} (${error.message})`
  return fallback
}

const TakeAttendance: React.FC = () => {
  const [mode, setMode] = useState<'photo' | 'live'>('photo')
  const [image, setImage] = useState<string | null>(null)
  const [faces, setFaces] = useState<SimulatedFace[]>([])
  const [sessions, setSessions] = useState<AttendanceSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState('')
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [sessionsError, setSessionsError] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [photoNotice, setPhotoNotice] = useState<string | null>(null)
  const [persisted, setPersisted] = useState<PersistedAttendance[]>([])
  const [persistedError, setPersistedError] = useState<string | null>(null)

  const selectedSession = sessions.find((s) => s.id === selectedSessionId)

  const loadPersisted = async (sessionId: string) => {
    setPersistedError(null)
    try {
      const response = await attendanceApi.getSessionAttendance(sessionId)
      setPersisted(Array.isArray(response.data) ? response.data : [])
    } catch (error: any) {
      setPersisted([])
      setPersistedError(errorMessage(error, 'Failed to load saved attendance records.'))
    }
  }

  const loadSessions = async () => {
    setSessionsLoading(true)
    setSessionsError(null)
    try {
      const response = await attendanceApi.getSessions()
      const list: AttendanceSession[] = Array.isArray(response.data) ? response.data : []
      setSessions(list)
      setSelectedSessionId((current) =>
        list.some((s) => s.id === current) ? current : (list[0]?.id || '')
      )
    } catch (error: any) {
      setSessions([])
      setSelectedSessionId('')
      setSessionsError(errorMessage(error, 'Failed to load attendance sessions.'))
    } finally {
      setSessionsLoading(false)
    }
  }

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    setFaces([])
    setPhotoNotice(null)
    if (selectedSessionId) {
      loadPersisted(selectedSessionId)
    } else {
      setPersisted([])
      setPersistedError(null)
    }
  }, [selectedSessionId])

  const handleModeChange = (newMode: 'photo' | 'live') => {
    setMode(newMode)
    setImage(null)
    setFaces([])
    setPhotoNotice(null)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = () => setImage(reader.result as string)
      reader.readAsDataURL(file)
    }
  }

  const processPhotoAttendance = async () => {
    if (!image) return
    if (!selectedSessionId) {
      alert('Select an attendance session before uploading a classroom photo.')
      return
    }

    setFaces([])
    setPhotoNotice(null)
    setProcessing(true)

    try {
      // Send the actual selected session id and a real multipart image upload.
      const blob = await fetch(image).then((res) => res.blob())
      const response = await attendanceApi.photoAttendance(selectedSessionId, blob)

      setPhotoNotice(
        response.data?.message ||
          'The backend received the photo but did not produce a recognition result.'
      )

      // Re-read the database records so the UI reflects what is actually saved.
      await loadPersisted(selectedSessionId)

      // Simulated output for UI demonstration only. The backend does not
      // perform face detection or recognition yet, so these rows are NOT
      // attendance records and are never persisted.
      setFaces([
        { student: 'Rahul Sharma', confidence: 97, status: 'present', name: 'Rahul Sharma' },
        { student: 'Priya Mehta', confidence: 94, status: 'present', name: 'Priya Mehta' },
        { student: 'Amit Kumar', confidence: 61, status: 'review', name: 'Amit Kumar' },
      ])
    } catch (error: any) {
      console.error('Photo attendance processing error:', error)
      alert(errorMessage(error, 'Error uploading the classroom photo.'))
    } finally {
      setProcessing(false)
    }
  }

  const processLiveFrame = () => {
    alert(
      'Live camera attendance is not implemented in the frontend yet. The Live Camera page is currently a demo and does not send frames to the backend.'
    )
  }

  return (
    <Layout>
      <h2>Take Attendance</h2>
      <div className="take-attendance-container">
        <div className="controls">
          <label>
            Attendance Session{' '}
            <select
              className="select"
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              disabled={sessionsLoading || sessions.length === 0}
            >
              {sessions.length === 0 && (
                <option value="">
                  {sessionsLoading ? 'Loading sessions...' : 'No sessions available'}
                </option>
              )}
              {sessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.subject} - Section {session.section} - {session.date || session.id}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn-secondary"
            onClick={loadSessions}
            disabled={sessionsLoading}
          >
            {sessionsLoading ? 'Loading...' : 'Refresh Sessions'}
          </button>
          <span className="date">Date: {new Date().toLocaleDateString()}</span>
        </div>

        {sessionsError && <p style={{ color: '#b91c1c' }}>{sessionsError}</p>}
        {!sessionsLoading && !sessionsError && sessions.length === 0 && (
          <p style={{ color: '#b45309' }}>
            No attendance sessions exist yet. Create one with
            {' '}
            <code>POST /api/attendance/sessions</code>, then refresh this page.
          </p>
        )}

        <div className="modes">
          <div className="mode-card photo-mode" onClick={() => handleModeChange('photo')}>
            <h3>📷 CLASSROOM PHOTO</h3>
            <p>Upload classroom image</p>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
            />
          </div>

          <div className="mode-card live-mode" onClick={() => handleModeChange('live')}>
            <h3>🎥 LIVE CAMERA</h3>
            <p>Start computer webcam</p>
            <button className="btn-secondary" disabled>
              Start Camera
            </button>
          </div>
        </div>

        {mode === 'photo' && image && (
          <div className="photo-preview">
            <h3>Classroom Image Preview</h3>
            <img src={image} alt="Classroom" style={{ maxWidth: '100%' }} />
            <p>
              The image is uploaded to the backend. Face recognition is not
              implemented yet, so no attendance records are created.
            </p>
            <button
              className="btn-primary"
              onClick={processPhotoAttendance}
              disabled={processing || !selectedSessionId}
            >
              {processing ? 'Uploading...' : 'Upload Classroom Photo'}
            </button>
          </div>
        )}

        {mode === 'live' && (
          <div className="live-interface">
            <h3>Live Camera Interface</h3>
            <p>Browser webcam access required</p>
            <div className="camera-placeholder">
              <p>Camera preview area - would use navigator.mediaDevices.getUserMedia()</p>
            </div>
            <p>Live frame processing is not wired to the backend in this page.</p>
            <button onClick={processLiveFrame} className="btn-primary">
              Start Live Attendance
            </button>
          </div>
        )}

        {photoNotice && (
          <div className="attendance-results">
            <h3>Backend Response</h3>
            <p>{photoNotice}</p>
            <p style={{ color: '#b45309' }}>
              This request uploads the image only. It does not create attendance
              records.
            </p>
          </div>
        )}

        <div className="attendance-results">
          <h3>
            Saved Attendance Records
            {selectedSession
              ? ` - ${selectedSession.subject} (Section ${selectedSession.section})`
              : ''}
          </h3>
          {!selectedSessionId && <p>Select a session to view its saved records.</p>}
          {persistedError && <p style={{ color: '#b91c1c' }}>{persistedError}</p>}
          {selectedSessionId && !persistedError && persisted.length === 0 && (
            <p>No attendance records are saved for this session.</p>
          )}
          {persisted.length > 0 && (
            <Table
              headers={'ID,Student DB ID,Status,Confidence,Method,Verified'.split(',')}
              rows={persisted.map((record) => [
                `${record.id}`,
                `${record.student_id}`,
                record.status,
                record.confidence === null ? '-' : `${record.confidence}%`,
                record.method,
                record.verified ? 'yes' : 'no',
              ])}
            />
          )}
          <button
            type="button"
            className="btn-secondary"
            onClick={() => selectedSessionId && loadPersisted(selectedSessionId)}
            disabled={!selectedSessionId}
          >
            Refresh Saved Records
          </button>
        </div>

        {faces.length > 0 && (
          <div className="attendance-results">
            <h3>Simulated Demo Results - NOT saved to the database</h3>
            <p style={{ color: '#b45309' }}>
              These rows are hardcoded demo data. They are not produced by a
              recognition model and are not attendance records.
            </p>
            <Table
              headers={'#,Simulated Student,Status,Confidence'.split(',')}
              rows={faces.map((f, i) => [
                `${i + 1}`,
                f.name,
                <Badge key={i} variant={f.status === 'present' ? 'success' : f.status === 'review' ? 'warning' : 'danger'}>{f.status}</Badge>,
                `${f.confidence}%`,
              ])}
            />
            <p>
              To record real attendance, the backend must detect faces, match
              them to enrolled students, and insert verified rows into the
              attendance table.
            </p>
          </div>
        )}
      </div>
    </Layout>
  )
}

export default TakeAttendance
