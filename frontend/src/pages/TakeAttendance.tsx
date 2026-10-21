import React, { useState } from 'react'
import { Card, Badge } from '../components/ui'
import Layout from '../layouts/MainLayout'

const TakeAttendance: React.FC = () => {
  const [mode, setMode] = useState<'photo' | 'live'>('photo')
  const [image, setImage] = useState<string | null>(null)
  const [faces, setFaces] = useState<Array<{
    student: string
    confidence: number
    status: 'present' | 'review' | 'unknown'
    name: string
  }>>([])

  const subjects = ['Data Structures', 'Database Management', 'Computer Networks', 'Machine Learning']
  const sections = ['CSE-A', 'CSE-B', 'IT-A', 'EEE-A']

  return (
    <Layout>
      <h2>Take Attendance</h2>
      <div className="take-attendance-container">
        <div className="controls">
          <select className="select">
            <option>Subject: {subjects[0]}</option>
            <option>Database Management</option>
            <option>Computer Networks</option>
            <option>Machine Learning</option>
          </select>
          <select className="select">
            <option>Section: {sections[0]}</option>
            <option>CSE-B</option>
            <option>IT-A</option>
            <option>EEE-A</option>
          </select>
          <span className="date">Date: {new Date().toLocaleDateString()}</span>
          <span className="period">Period: 3</span>
        </div>

        <div className="modes">
          <div className="mode-card photo-mode" onClick={() => setMode('photo')}>
            <h3>📷 CLASSROOM PHOTO</h3>
            <p>Upload classroom image</p>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => {
                const file = e.target.files[0]
                if (file) {
                  const reader = new FileReader()
                  reader.onload = (f) => setImage(reader.result as string)
                  reader.readAsDataURL(file)
                }
              }}
            />
          </div>

          <div className="mode-card live-mode" onClick={() => setMode('live')}>
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
            <p>Faces will be detected and matched against registered students.</p>
            <button className="btn-primary" disabled>
              Detect Faces
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
            <p>Face detection and recognition would process the live feed.</p>
          </div>
        )}

        {faces.length > 0 && (
          <div className="attendance-results">
            <h3>Attendance Results</h3>
            <Table
              headers={"Roll No.,Student,Status,Confidence".split(",")}
              rows={faces.map((f, i) => [
                `${i + 1}`,
                f.name,
                <Badge variant={f.status === 'present' ? 'success' : f.status === 'review' ? 'warning' : 'danger'}>{f.status}</Badge>,
                `${f.confidence}%`
              ])}
            />
          </div>
        )}
      </div>
    </Layout>
  )
}

export default TakeAttendance