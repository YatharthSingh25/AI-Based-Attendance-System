import React, { useEffect, useState } from 'react'
import { Badge, Card, Table } from '../components/ui'
import Layout from '../layouts/MainLayout'
import { meApi } from '../services/api'

interface MyStudent {
  id: string
  student_id: string
  name: string
  email: string
  course: string
  branch: string
  section: string
  semester: number
}

interface SubjectSummary {
  subject: string
  present: number
  absent: number
  total: number
  percentage: number
}

interface AttendanceSummary {
  total_sessions: number
  present: number
  absent: number
  review: number
  unknown: number
  attendance_percentage: number
  subjects: SubjectSummary[]
}

interface AttendanceRow {
  id: number
  session_id: string
  subject: string | null
  section: string | null
  date: string | null
  status: string
  confidence: number | null
  method: string
  verified: boolean
  timestamp: string | null
}

const badgeVariant = (status: string) => {
  const value = status.toLowerCase()
  if (value === 'present') return 'success' as const
  if (value === 'absent') return 'danger' as const
  if (value === 'review') return 'warning' as const
  return 'secondary' as const
}

const MyAttendance: React.FC = () => {
  const [student, setStudent] = useState<MyStudent | null>(null)
  const [summary, setSummary] = useState<AttendanceSummary | null>(null)
  const [records, setRecords] = useState<AttendanceRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [profileResponse, attendanceResponse] = await Promise.all([
          meApi.getMyStudent(),
          meApi.getMyAttendance(),
        ])
        setStudent(profileResponse.data?.student ?? null)
        setSummary(profileResponse.data?.summary ?? null)
        setRecords(
          Array.isArray(attendanceResponse.data) ? attendanceResponse.data : []
        )
      } catch (err: any) {
        const status = err?.response?.status
        const detail = err?.response?.data?.detail

        if (status === 404) {
          setError(
            typeof detail === 'string'
              ? detail
              : 'No student record is linked to this account.'
          )
        } else if (status === 403) {
          setError('This account does not have access to student records.')
        } else if (typeof detail === 'string') {
          setError(detail)
        } else {
          setError('Unable to load your attendance. Please try again.')
        }
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  if (loading) {
    return (
      <Layout>
        <h2>My Attendance</h2>
        <p>Loading your attendance...</p>
      </Layout>
    )
  }

  if (error || !student) {
    return (
      <Layout>
        <h2>My Attendance</h2>
        <Card title="Account not linked">
          <p className="form-error">{error || 'No student record is linked to this account.'}</p>
          <p>
            Ask your teacher to add you as a student using this exact email
            address, then sign in again.
          </p>
        </Card>
      </Layout>
    )
  }

  const profileRows = [
    ['Roll Number', student.student_id],
    ['Name', student.name],
    ['Email', student.email],
    ['Course', student.course],
    ['Branch', student.branch],
    ['Section', student.section],
    ['Semester', String(student.semester)],
  ]

  return (
    <Layout>
      <h2>My Attendance</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{summary?.attendance_percentage ?? 0}%</div>
          <div className="stat-label">Attendance</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.present ?? 0}</div>
          <div className="stat-label">Present</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.absent ?? 0}</div>
          <div className="stat-label">Absent</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary?.total_sessions ?? 0}</div>
          <div className="stat-label">Classes Recorded</div>
        </div>
      </div>

      <div className="profile-section">
        <Card title="My Profile">
          <dl className="profile-grid">
            {profileRows.map(([label, value]) => (
              <div key={label} className="profile-item">
                <dt className="profile-label">{label}</dt>
                <dd className="profile-value">{value}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>

      <div className="subject-breakdown">
        <Card title="Attendance by Subject">
          {summary && summary.subjects.length > 0 ? (
            <Table
              headers={['Subject', 'Present', 'Absent', 'Recorded', 'Percentage']}
              rows={summary.subjects.map((subject) => [
                subject.subject,
                String(subject.present),
                String(subject.absent),
                String(subject.total),
                `${subject.percentage}%`,
              ])}
            />
          ) : (
            <p>No subject-wise attendance has been recorded yet.</p>
          )}
        </Card>
      </div>

      <div className="low-attendance">
        <Card title="Attendance History">
          {records.length > 0 ? (
            <Table
              headers={['Date', 'Subject', 'Section', 'Status', 'Method', 'Verified']}
              rows={records.map((record) => [
                record.date || (record.timestamp ? record.timestamp.slice(0, 10) : '-'),
                record.subject || '-',
                record.section || '-',
                <Badge key={record.id} variant={badgeVariant(record.status)}>
                  {record.status}
                </Badge>,
                record.method,
                record.verified ? 'Yes' : 'No',
              ])}
            />
          ) : (
            <p>No attendance records have been recorded for you yet.</p>
          )}
        </Card>
      </div>
    </Layout>
  )
}

export default MyAttendance
