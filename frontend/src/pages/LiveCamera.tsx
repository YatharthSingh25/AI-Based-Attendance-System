import React, { useEffect, useRef, useState } from 'react'
import { Card, Table } from '../components/ui'
import Layout from '../layouts/MainLayout'
import { attendanceApi } from '../services/api'

interface Session {
  id: string
  subject: string
  section: string
  date?: string
}

interface MarkedStudent {
  student_id: string
  name: string
  confidence: number
}

interface RecognitionResult {
  message: string
  faces_detected: number
  marked_present: MarkedStudent[]
  already_marked: { student_id: string; name: string; status: string }[]
  unknown_faces: number
}

const errorMessage = (error: any, fallback: string): string => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail) return JSON.stringify(detail)
  return error?.message ? `${fallback} (${error.message})` : fallback
}

const LiveCamera: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const [running, setRunning] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [sessionId, setSessionId] = useState('')
  const [capturing, setCapturing] = useState(false)
  const [result, setResult] = useState<RecognitionResult | null>(null)
  const [captureError, setCaptureError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const response = await attendanceApi.getSessions()
        const list: Session[] = Array.isArray(response.data) ? response.data : []
        setSessions(list)
        setSessionId((current) =>
          list.some((s) => s.id === current) ? current : (list[0]?.id || '')
        )
      } catch (error: any) {
        setCaptureError(errorMessage(error, 'Could not load attendance sessions.'))
      }
    }
    load()

    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop())
    }
  }, [])

  const startCamera = async () => {
    setCameraError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setRunning(true)
    } catch {
      setCameraError(
        'Camera access was blocked. Allow camera permission in the browser and try again.'
      )
    }
  }

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setRunning(false)
  }

  const captureAndMark = async () => {
    const video = videoRef.current
    if (!video) return
    if (!sessionId) {
      setCaptureError('Select an attendance session first.')
      return
    }

    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const context = canvas.getContext('2d')
    if (!context) return
    context.drawImage(video, 0, 0, canvas.width, canvas.height)

    setCaptureError(null)
    setCapturing(true)
    try {
      const blob: Blob | null = await new Promise((resolve) =>
        canvas.toBlob((value) => resolve(value), 'image/jpeg', 0.9)
      )
      if (!blob) {
        setCaptureError('Could not read a frame from the camera.')
        return
      }
      const response = await attendanceApi.liveFrame(sessionId, blob)
      setResult(response.data as RecognitionResult)
    } catch (error: any) {
      setCaptureError(errorMessage(error, 'Could not process this frame.'))
    } finally {
      setCapturing(false)
    }
  }

  return (
    <Layout>
      <h2>Live Camera Attendance</h2>
      <div className="live-camera-container">
        <div className="controls">
          <label>
            Attendance Session{' '}
            <select
              className="select"
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              disabled={sessions.length === 0}
            >
              {sessions.length === 0 && <option value="">No sessions available</option>}
              {sessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.subject} - Section {session.section} - {session.date || session.id}
                </option>
              ))}
            </select>
          </label>
        </div>

        {sessions.length === 0 && (
          <p className="form-warning">
            No attendance sessions exist yet. Create one before using the camera.
          </p>
        )}

        <div className="camera-placeholder">
          <video
            ref={videoRef}
            playsInline
            muted
            style={{ width: '100%', display: running ? 'block' : 'none' }}
          />
          {!running && <p>Start the camera, then capture a frame to mark attendance.</p>}
        </div>

        {cameraError && <p className="form-error">{cameraError}</p>}
        {captureError && <p className="form-error">{captureError}</p>}

        <div className="camera-controls">
          <button
            type="button"
            className="btn-primary"
            onClick={startCamera}
            disabled={running}
          >
            Start Camera
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={stopCamera}
            disabled={!running}
          >
            Stop
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={captureAndMark}
            disabled={!running || capturing || !sessionId}
          >
            {capturing ? 'Recognising...' : 'Capture & Mark Attendance'}
          </button>
        </div>

        {result && (
          <Card title="Last capture">
            <p>{result.message}</p>
            <p>
              Faces detected: {result.faces_detected} · Marked present:{' '}
              {result.marked_present.length} · Unknown: {result.unknown_faces}
            </p>
            {result.marked_present.length > 0 && (
              <Table
                headers={['Roll No.', 'Student', 'Confidence']}
                rows={result.marked_present.map((student) => [
                  student.student_id,
                  student.name,
                  `${student.confidence}%`,
                ])}
              />
            )}
          </Card>
        )}
      </div>
    </Layout>
  )
}

export default LiveCamera
