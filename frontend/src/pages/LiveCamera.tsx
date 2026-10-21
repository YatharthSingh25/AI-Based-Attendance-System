import React, { useState, useEffect } from 'react'
import { Card, Badge } from '../components/ui'
import Layout from '../layouts/MainLayout'

interface DetectedFace {
  name: string
  confidence: number
  status: 'present' | 'review' | 'unknown'
  trackId: string
}

const LiveCamera: React.FC = () => {
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null)
  const [fps, setFps] = useState(0)
  const [facesDetected, setFacesDetected] = useState(0)
  const [recognized, setRecognized] = useState(0)
  const [unknown, setUnknown] = useState(0)
  const [trackedFaces, setTrackedFaces] = useState<DetectedFace[]>([])
  const [isRunning, setIsRunning] = useState(false)
  let frameTimeout: NodeJS.Timeout | null = null

  const subjects = ['Data Structures', 'Database Management', 'Computer Networks']
  const sections = ['CSE-A', 'CSE-B', 'IT-A']

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 1280, height: 720 }
      })
      setVideoStream(stream)
      setIsRunning(true)
      startFaceDetectionLoop()
    } catch (err) {
      console.error('Camera access denied or failed:', err)
    }
  }

  const stopCamera = () => {
    setIsRunning(false)
    if (videoStream) {
      videoStream.getTracks().forEach(track => track.stop())
      setVideoStream(null)
    }
    if (frameTimeout) {
      clearTimeout(frameTimeout)
      frameTimeout = null
    }
  }

  const startFaceDetectionLoop = () => {
    if (!isRunning || !videoStream) return

    // Process frame for face detection
    const videoElement = document.querySelector('video') as HTMLVideoElement
    if (videoElement) {
      const canvas = document.createElement('canvas')
      canvas.width = videoElement.videoWidth
      canvas.height = videoElement.videoHeight
      const ctx = canvas.getContext('2d')!
      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height)

      // Mock face detection - in production would use a real detector
      const detections = mockFaceDetection(canvas)

      setFacesDetected(detections.length)
      setRecognized(detections.filter(f => f.status === 'present').length)
      setUnknown(detections.filter(f => f.status === 'unknown').length)

      setTrackedFaces(detections)
    }

    frameTimeout = setTimeout(startFaceDetectionLoop, 1000 / 24) // ~24 FPS
  }

  const mockFaceDetection = (canvas: HTMLCanvasElement): DetectedFace[] => {
    const faces: DetectedFace[] = []
    const ctx = canvas.getContext('2d')!
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height)
    // Generate mock faces for demonstration
    const numFaces = Math.min(3, 1 + Math.floor(Math.random() * 3))

    for (let i = 0; i < numFaces; i++) {
      const confidence = Math.round(80 + Math.random() * 20)
      const status = confidence >= 85 ? 'present' : confidence >= 70 ? 'review' : 'unknown'
      const trackId = `track_${i + 1}`

      faces.push({
        name: `Student ${i + 1}`,
        confidence,
        status,
        trackId,
      })
    }

    return faces
  }

  const handleAttendance = (face: DetectedFace) => {
    // Would call API to mark attendance
    console.log(`Marking attendance for ${face.name} (${face.confidence}%)`)
  }

  return (
    <Layout>
      <h2>Live Camera Attendance</h2>
      <div className="live-camera-container">
        <div className="camera-header">
          <span>LIVE</span>
          <div className="fps-counter">FPS: {fps}</div>
          <div className="faces-counter">
            Faces Detected: {facesDetected} | Recognized: {recognized} | Unknown: {unknown}
          </div>
        </div>

        {isRunning && videoStream ? (
          <video
            autoPlay
            playsInline
            style={{ width: '100%', height: 'auto' }}
          />
        ) : (
          <div className="camera-placeholder">
            <p>Click {"\"Start Camera\""} to access webcam</p>
          </div>
        )}

        <div className="tracking-results">
          {trackedFaces.length > 0 && (
            <div className="faces-list">
              {trackedFaces.map((face, i) => (
                <div key={i} className="face-item">
                  <span className="face-name">{face.name}</span>
                  <Badge variant={face.confidence >= 85 ? 'success' : face.confidence >= 70 ? 'warning' : 'danger'}>
                    {face.confidence}%
                  </Badge>
                  <span className="track-id">Track: {face.trackId}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="camera-controls">
          <button onClick={startCamera} className="btn-primary" disabled={isRunning}>
            {isRunning ? 'Stop Camera' : 'Start Camera'}
          </button>
          <button onClick={stopCamera} className="btn-secondary" disabled={!isRunning}>
            Stop
          </button>
        </div>
      </div>
    </Layout>
  )
}

export default LiveCamera