import React from 'react'
import { Card } from '../components/ui'
import Layout from '../layouts/MainLayout'

const Subjects: React.FC = () => {
  return (
    <Layout>
      <h2>Subjects</h2>
      <Card>
        <h3>Registered Subjects</h3>
        <table>
          <thead>
            <tr>
              <th>Subject Code</th>
              <th>Subject Name</th>
              <th>Faculty</th>
              <th>Section</th>
              <th>Credits</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>CSE301</td>
              <td>Data Structures</td>
              <td>Prof. Sharma</td>
              <td>CSE-A</td>
              <td>3</td>
            </tr>
            <tr>
              <td>CSE302</td>
              <td>Database Management Systems</td>
              <td>Prof. Singh</td>
              <td>CSE-A</td>
              <td>3</td>
            </tr>
            <tr>
              <td>CSE303</td>
              <td>Computer Networks</td>
              <td>Prof. Patel</td>
              <td>CSE-B</td>
              <td>3</td>
            </tr>
            <tr>
              <td>CSE304</td>
              <td>Machine Learning</td>
              <td>Prof. Agarwal</td>
              <td>CSE-B</td>
              <td>3</td>
            </tr>
          </tbody>
        </table>
        <p>Total: 4 subjects</p>
      </Card>
    </Layout>
  )
}

export default Subjects