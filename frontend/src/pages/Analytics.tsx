import React from 'react'
import { Card, Badge } from '../components/ui'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import Layout from '../layouts/MainLayout'

const Analytics: React.FC = () => {
  const subjects = ['DSA', 'DBMS', 'DAA', 'OS', 'CN']
  const present = [85, 78, 62, 90, 88]
  const absent = [15, 22, 38, 10, 12]

  const overallPresent = 403
  const overallAbsent = 97
  const overallTotal = overallPresent + overallAbsent
  const overallPercentage = Math.round((overallPresent / overallTotal) * 100)

  const atRiskStudents = 12

  return (
    <Layout>
      <h2>Analytics</h2>

      <div className="overview-stats">
        <Card>
          <div className="stat-value">{overallPresent}</div>
          <div className="stat-label">Present</div>
        </Card>
        <Card>
          <div className="stat-value">{overallAbsent}</div>
          <div className="stat-label">Absent</div>
        </Card>
        <Card>
          <div className="stat-value">{overallPercentage}%</div>
          <div className="stat-label">Overall Attendance</div>
        </Card>
        <Card>
          <div className="stat-value">{atRiskStudents}</div>
          <div className="stat-label">At Risk</div>
        </Card>
      </div>

      <div className="subject-analysis">
        <h3>Subject-wise Attendance</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={subjects.map((s, i) => ({ subject: s, present: present[i], absent: absent[i] }))}>
            <XAxis dataKey="subject" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="present" fill="#34d399" label="Present" />
            <Bar dataKey="absent" fill="#f87171" label="Absent" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="at-risk">
        <h3>Students At Risk (&lt; 75% Attendance)</h3>
        <Card>
          <p>12 students below 75% attendance threshold</p>
          <p>Intervention recommended for DAA and OS subjects</p>
        </Card>
      </div>
    </Layout>
  )
}

export default Analytics