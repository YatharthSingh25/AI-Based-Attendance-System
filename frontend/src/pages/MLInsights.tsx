import React from 'react'
import { Card, Badge, Table } from '../components/ui'
import Layout from '../layouts/MainLayout'

const MLInsights: React.FC = () => {
  const students = [
    { id: '1', name: 'Rahul Sharma', overall: '84%', risk: 'LOW', subjects: { 'DSA': '91%', 'DBMS': '84%', 'DAA': '73%', 'OS': '88%' } },
    { id: '2', name: 'Priya Mehta', overall: '76%', risk: 'MEDIUM', subjects: { 'DSA': '88%', 'DBMS': '70%', 'DAA': '65%', 'OS': '82%' } },
    { id: '3', name: 'Amit Kumar', overall: '62%', risk: 'HIGH', subjects: { 'DSA': '55%', 'DBMS': '72%', 'DAA': '48%', 'OS': '75%' } },
    { id: '4', name: 'Sneha Roy', overall: '91%', risk: 'LOW', subjects: { 'DSA': '95%', 'DBMS': '88%', 'DAA': '82%', 'OS': '93%' } },
  ]

  const hasInsufficientData = false

  return (
    <Layout>
      <h2>ML Insights</h2>

      {hasInsufficientData ? (
        <Card>
          <h3>Insufficient Historical Data</h3>
          <p>Not enough attendance data to train reliable ML prediction models.</p>
          <p>Please ensure attendance is being recorded consistently for accurate predictions.</p>
        </Card>
      ) : (
        <div>
          <h3>Attendance Risk Prediction</h3>

          <div className="student-risk-cards">
            {students.map((student) => (
              <Card key={student.id} className="risk-card">
                <div className="risk-info">
                  <span className="student-name">{student.name}</span>
                  <span className="overall-percentage">{student.overall}</span>
                </div>
                <Badge variant={student.risk === 'LOW' ? 'success' : student.risk === 'MEDIUM' ? 'warning' : 'danger'}>
                  {student.risk}
                </Badge>
              </Card>
            ))}
          </div>

          <h3>Subject Attendance Breakdown</h3>
          <table>
            <thead>
              <tr>
                <th>Subject</th>
                {/* Dynamic rows would be generated from student.subjects */}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Data Structures</td>
                <td>91%</td>
                <td>88%</td>
                <td>73%</td>
                <td>88%</td>
              </tr>
              <tr>
                <td>DBMS</td>
                <td>84%</td>
                <td>70%</td>
                <td>65%</td>
                <td>70%</td>
              </tr>
              <tr>
                <td>DAA</td>
                <td>73%</td>
                <td>65%</td>
                <td>48%</td>
                <td>75%</td>
              </tr>
              <tr>
                <td>OS</td>
                <td>88%</td>
                <td>82%</td>
                <td>75%</td>
                <td>93%</td>
              </tr>
            </tbody>
          </table>

          <p>Models available: Logistic Regression, Random Forest, XGBoost</p>
          <p>Metrics after evaluation: Accuracy, Precision, Recall, F1 Score, Confusion Matrix</p>
        </div>
      )}

      <div className="ml-methods">
        <h3>ML Models Used</h3>
        <ul>
          <li>Logistic Regression - Binary classification for attendance presence</li>
          <li>Random Forest - Ensemble method for pattern detection</li>
          <li>XGBoost - Gradient boosting for risk scoring</li>
        </ul>
        <p>Features: current_attendance, classes_attended, classes_missed, recent_attendance, consecutive_absences, subject_attendance, attendance_trend</p>
        <p>Output: LOW RISK, MEDIUM RISK, HIGH RISK (attendance shortage only)</p>
      </div>
    </Layout>
  )
}

export default MLInsights