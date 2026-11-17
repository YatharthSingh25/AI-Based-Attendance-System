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

interface MarkedStudent {
  student_id: string
  name: string
  confidence: number
}

interface AlreadyMarked {
  student_id: string
  name: string
  status: string
}

interface RecognitionResult {
  message: string
  faces_detected: number
  marked_present: MarkedStudent[]
  already_marked: AlreadyMarked[]
  unknown_faces: number
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
  const [sessions, setSessions] = useState<AttendanceSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState('')
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [sessionsError, setSessionsError] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [recognition, setRecognition] = useState<RecognitionResult | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [persisted, setPersisted] = useState<PersistedAttendance[]>([])
  const [persistedError, setPersistedError] = useState<string | null>(null)

  const [newSubject, setNewSubject] = useState('Data Structures')
  const [newSection, setNewSection] = useState('A')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

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
    setRecognition(null)
    setUploadError(null)
    if (selectedSessionId) {
      loadPersisted(selectedSessionId)
    } else {
      setPersisted([])
      setPersistedError(null)
    }
  }, [selectedSessionId])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = () => setImage(reader.result as string)
      reader.readAsDataURL(file)
      setRecognition(null)
      setUploadError(null)
    }
  }

  const createSession = async () => {
    const subject = newSubject.trim()
    if (!subject) {
      setCreateError('Enter a subject name.')
      return
    }

    setCreating(true)
    setCreateError(null)
    try {
      const response = await attendanceApi.createSession({
        subject,
        section: newSection,
      })
      const created = response.data?.session
      await loadSessions()
      if (created?.id) {
        setSelectedSessionId(created.id)
      }
    } catch (error: any) {
      setCreateError(errorMessage(error, 'Could not create the session.'))
    } finally {
      setCreating(false)
    }
  }

  const processPhotoAttendance = async () => {    if (!image) return
    if (!selectedSessionId) {
      setUploadError('Select an attendance session before uploading a photo.')
      return
    }

    setRecognition(null)
    setUploadError(null)
    setProcessing(true)

    try {
      const blob = await fetch(image).then((res) => res.blob())
      const response = await attendanceApi.photoAttendance(selectedSessionId, blob)
      setRecognition(response.data as RecognitionResult)
      await loadPersisted(selectedSessionId)
    } catch (error: any) {
      setUploadError(errorMessage(error, 'Could not process this photo.'))
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Layout>
      <h2>Take Attendance</h2>
      <div className="take-attendance-container">
        <div className="session-create">
          <label>
            Subject{' '}
            <input
              type="text"
              value={newSubject}
              onChange={(e) => setNewSubject(e.target.value)}
              placeholder="Data Structures"
            />
          </label>
          <label>
            Section{' '}
            <select
              className="select"
              value={newSection}
              onChange={(e) => setNewSection(e.target.value)}
            >
              <option>A</option>
              <option>B</option>
              <option>C</option>
            </select>
          </label>
          <button
            type="button"
            className="btn-primary"
            onClick={createSession}
            disabled={creating}
          >
            {creating ? 'Creating...' : 'Start New Session'}
          </button>
        </div>
        {createError && <p className="form-error">{createError}</p>}

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

        {sessionsError && <p className="form-error">{sessionsError}</p>}
        {!sessionsLoading && !sessionsError && sessions.length === 0 && (
          <p className="form-warning">
            No attendance sessions exist yet. Create one with{' '}
            <code>POST /api/attendance/sessions</code>, then refresh this page.
          </p>
        )}

        <div className="modes">
          <div
            className={mode === 'photo' ? 'mode-card photo-mode active' : 'mode-card photo-mode'}
            onClick={() => setMode('photo')}
          >
            <h3>CLASSROOM PHOTO</h3>
            <p>Upload a photo of one student or a group</p>
            <input type="file" accept="image/*" onChange={handleFileChange} />
          </div>

          <div
            className={mode === 'live' ? 'mode-card live-mode active' : 'mode-card live-mode'}
            onClick={() => setMode('live')}
          >
            <h3>LIVE CAMERA</h3>
            <p>Capture from the webcam</p>
          </div>
        </div>

        {mode === 'photo' && (
          <div className="photo-preview">
            {image ? (
              <>
                <h3>Photo Preview</h3>
                <img src={image} alt="Classroom" style={{ maxWidth: '100%' }} />
                <p>
                  Every detected face is matched against enrolled students in
                  section {selectedSession?.section || '-'}. Matching students are
                  marked present.
                </p>
                <button
                  className="btn-primary"
                  onClick={processPhotoAttendance}
                  disabled={processing || !selectedSessionId}
                >
                  {processing ? 'Recognising faces...' : 'Mark Attendance from Photo'}
                </button>
              </>
            ) : (
              <p>Choose a photo above to begin.</p>
            )}
          </div>
        )}

        {mode === 'live' && (
          <div className="live-interface">
            <p>
              Live capture lives on the Live Camera page, where a frame is sent
              to the same recognition service.
            </p>
            <a className="btn-primary" href="/live-camera">
              Open Live Camera
            </a>
          </div>
        )}

        {uploadError && <p className="form-error">{uploadError}</p>}

        {recognition && (
          <div className="attendance-results">
            <h3>Result</h3>
            <p>{recognition.message}</p>
            <p>
              Faces detected: {recognition.faces_detected} · Marked present:{' '}
              {recognition.marked_present.length} · Unknown:{' '}
              {recognition.unknown_faces}
            </p>

            {recognition.marked_present.length > 0 && (
              <Table
                headers={['Roll No.', 'Student', 'Confidence']}
                rows={recognition.marked_present.map((student) => [
                  student.student_id,
                  student.name,
                  `${student.confidence}%`,
                ])}
              />
            )}

            {recognition.already_marked.length > 0 && (
              <>
                <h4>Already marked for this session</h4>
                <Table
                  headers={['Roll No.', 'Student', 'Status']}
                  rows={recognition.already_marked.map((student) => [
                    student.student_id,
                    student.name,
                    <Badge key={student.student_id} variant="secondary">
                      {student.status}
                    </Badge>,
                  ])}
                />
              </>
            )}
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
          {persistedError && <p className="form-error">{persistedError}</p>}
          {selectedSessionId && !persistedError && persisted.length === 0 && (
            <p>No attendance records are saved for this session.</p>
          )}
          {persisted.length > 0 && (
            <Table
              headers={'ID,Student DB ID,Status,Confidence,Method,Verified'.split(',')}
              rows={persisted.map((record) => [
                `${record.id}`,
                `${record.student_id}`,
                <Badge
                  key={record.id}
                  variant={record.status === 'present' ? 'success' : 'danger'}
                >
                  {record.status}
                </Badge>,
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
      </div>
    </Layout>
  )
}

export default TakeAttendance
