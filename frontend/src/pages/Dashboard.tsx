import React from 'react'
import { Card, Chart } from './ui'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface Student {
  id: string
  name: string
  rollNo: string
  course: string
  status: 'present' | 'absent' | 'unknown'
}

const Dashboard: React.FC = () => {
  const students: Student[] = [
    { id: '1', name: 'Rahul Sharma', rollNo: '001', course: 'Data Structures', status: 'present' },
    { id: '2', name: 'Priya Mehta', rollNo: '002', course: 'Data Structures', status: 'present' },
    { id: '3', name: 'Amit Kumar', rollNo: '003', course: 'Data Structures', status: 'absent' },
    { id: '4', name: 'Sneha Roy', rollNo: '004', course: 'Data Structures', status: 'present' },
  ]

  const total = students.length
  const present = students.filter(s => s.status === 'present').length
  const absent = students.filter(s => s.status === 'absent').length
  const unknown = students.filter(s => s.status === 'unknown').length
  const percentage = Math.round((present / total) * 100)

  return (
    <div className="dashboard-page">
      <h2>{"Today's Attendance"}</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{present}</div>
          <div className="stat-label">Present</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{absent}</div>
          <div className="stat-label">Absent</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{unknown}</div>
          <div className="stat-label">Unknown</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{percentage}%</div>
          <div className="stat-label">Overall Attendance</div>
        </div>
      </div>

      <div className="charts-section">
        <h3>Attendance Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={students}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="status" backgroundColor="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default Dashboard