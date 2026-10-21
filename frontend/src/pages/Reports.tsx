import React from 'react'
import { Card, Table, Badge } from '../components/ui'
import Layout from '../layouts/MainLayout'

const Reports: React.FC = () => {
  const attendanceData = [
    { roll: '001', student: 'Rahul Sharma', status: 'present', confidence: '97%', method: 'Live', time: '09:02', verification: 'Verified' },
    { roll: '002', student: 'Priya Mehta', status: 'present', confidence: '94%', method: 'Photo', time: '09:02', verification: 'Verified' },
    { roll: '003', student: 'Amit Kumar', status: 'review', confidence: '61%', method: 'Live', time: '09:03', verification: 'Pending' },
    { roll: '004', student: 'Sneha Roy', status: 'present', confidence: '89%', method: 'Photo', time: '09:05', verification: 'Verified' },
    { roll: '005', student: 'Unknown', status: 'unknown', confidence: '54%', method: 'Live', time: '09:06', verification: 'Review' },
  ]

  const generateReport = (format: 'PDF' | 'CSV' | 'Excel') => {
    // Would generate and download report
    alert(`Report generation (${format}) - feature pending implementation`)
  }

  return (
    <Layout>
      <h2>Reports</h2>
      <div className="report-actions">
        <button onClick={() => generateReport('PDF')} className="btn-primary">
          Generate PDF Report
        </button>
        <button onClick={() => generateReport('CSV')} className="btn-secondary">
          Export CSV
        </button>
        <button onClick={() => generateReport('Excel')} className="btn-outline">
          Export Excel
        </button>
      </div>

      <Card>
        <h3>Daily Attendance</h3>
        <Table
          headers={"Roll No.,Student,Status,Confidence,Method,Time,Verification".split(",")}
          rows={attendanceData}
        />
      </Card>

      <div className="subject-breakdown">
        <h3>Subject Attendance Summary</h3>
        <table>
          <thead>
            <tr>
              <th>Subject</th>
              <th>Present</th>
              <th>Absent</th>
              <th>Percentage</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Data Structures</td>
              <td>42</td>
              <td>6</td>
              <td>87%</td>
            </tr>
            <tr>
              <td>Database Management</td>
              <td>38</td>
              <td>8</td>
              <td>83%</td>
            </tr>
            <tr>
              <td>Computer Networks</td>
              <td>35</td>
              <td>10</td>
              <td>78%</td>
            </tr>
            <tr>
              <td>Machine Learning</td>
              <td>40</td>
              <td>5</td>
              <td>89%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="low-attendance">
        <h3>Low Attendance Students</h3>
        <Card>
          <p>Students requiring attendance intervention</p>
        </Card>
      </div>
    </Layout>
  )
}

export default Reports