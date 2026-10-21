import React, { useState } from 'react'
import { Card, Table, Badge } from '../components/ui'
import Layout from '../layouts/MainLayout'

interface Student {
  id: string
  studentId: string
  name: string
  email: string
  course: string
  branch: string
  section: string
  semester: number
}

const Students: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'view' | 'add' | 'enroll' | 'edit'>('view')
  const [newStudent, setNewStudent] = useState<Partial<Student>>({
    studentId: '',
    name: '',
    email: '',
    course: '',
    branch: '',
    section: '',
    semester: 1,
  })
  const [enrollImages, setEnrollImages] = useState<FileList | null>(null)

  // Sample data - would fetch from API in production
  const loadStudents = () => {
    setStudents([
      { id: '1', studentId: 'CSE001', name: 'Rahul Sharma', email: 'rahul@college.edu', course: 'Data Structures', branch: 'CSE', section: 'A', semester: 3 },
      { id: '2', studentId: 'CSE002', name: 'Priya Mehta', email: 'priya@college.edu', course: 'DBMS', branch: 'CSE', section: 'A', semester: 3 },
      { id: '3', studentId: 'CSE003', name: 'Amit Kumar', email: 'amit@college.edu', course: 'DAA', branch: 'CSE', section: 'B', semester: 4 },
      { id: '4', studentId: 'CSE004', name: 'Sneha Roy', email: 'sneha@college.edu', course: 'OS', branch: 'CSE', section: 'A', semester: 3 },
    ])
  }

  const handleAddStudent = () => {
    setMode('add')
  }

  const handleEnrollFace = () => {
    setMode('enroll')
  }

  const saveStudent = () => {
    if (!newStudent.name || !newStudent.studentId) return
    const student: Student = {
      ...newStudent,
      id: String(Date.now()),
    }
    setStudents([...students, student])
    loadStudents()
    setMode('view')
    setNewStudent({
      studentId: '',
      name: '',
      email: '',
      course: '',
      branch: '',
      section: '',
      semester: 1,
    })
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEnrollImages(e.target.files as FileList)
  }

  const generateEmbedding = () => {
    if (!enrollImages) return
    // Would process images and generate face embeddings
    alert('Face embedding generation - AI service integration pending')
    setEnrollImages(null)
    setMode('view')
  }

  loadStudents()

  return (
    <Layout>
      <h2>Students</h2>
      <div className="students-container">
        <div className="actions">
          <button onClick={handleAddStudent} className="btn-primary">
            Add Student
          </button>
          <button onClick={handleEnrollFace} className="btn-secondary">
            Enroll Face
          </button>
        </div>

        {mode === 'add' && (
          <div className="form-section">
            <h3>Add New Student</h3>
            <form>
              <div className="form-group">
                <label>Student ID</label>
                <input
                  type="text"
                  placeholder="CSE005"
                  value={newStudent.studentId || ''}
                  onChange={(e) => setNewStudent({ ...newStudent, studentId: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  placeholder="Enter student name"
                  value={newStudent.name || ''}
                  onChange={(e) => setNewStudent({ ...newStudent, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  placeholder="student@college.edu"
                  value={newStudent.email || ''}
                  onChange={(e) => setNewStudent({ ...newStudent, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Course</label>
                <select
                  value={newStudent.course || ''}
                  onChange={(e) => setNewStudent({ ...newStudent, course: e.target.value })}
                >
                  <option>Data Structures</option>
                  <option>Database Management</option>
                  <option>Computer Networks</option>
                  <option>Machine Learning</option>
                  <option>DAA</option>
                  <option>OS</option>
                </select>
              </div>
              <div className="form-group">
                <label>Branch</label>
                <select
                  value={newStudent.branch || ''}
                  onChange={(e) => setNewStudent({ ...newStudent, branch: e.target.value })}
                >
                  <option>CSE</option>
                  <option>ECE</option>
                  <option>EEE</option>
                  <option>IT</option>
                </select>
              </div>
              <div className="form-group">
                <label>Section</label>
                <select
                  value={newStudent.section || ''}
                  onChange={(e) => setNewStudent({ ...newStudent, section: e.target.value })}
                >
                  <option>A</option>
                  <option>B</option>
                  <option>C</option>
                </select>
              </div>
              <div className="form-group">
                <label>Semester</label>
                <input
                  type="number"
                  min="1"
                  max="8"
                  value={newStudent.semester || 1}
                  onChange={(e) => setNewStudent({ ...newStudent, semester: Number(e.target.value) })}
                />
              </div>
              <button type="button" className="btn-secondary" onClick={saveStudent}>
                Save Student
              </button>
              <button type="button" className="btn-outline" onClick={loadStudents}>
                Cancel
              </button>
            </form>
          </div>
        )}

        {mode === 'enroll' && (
          <div className="form-section">
            <h3>Enroll Face Images</h3>
            <p>Student: {newStudent?.name || 'Select student'} ({newStudent?.studentId || ''})</p>
            <p>Upload 3-5 face images for enrollment</p>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleImageSelect}
            />
            <button onClick={generateEmbedding} className="btn-primary" disabled={!enrollImages}>
              Generate Face Embedding
            </button>
            <button onClick={() => setMode('view')} className="btn-secondary">
              Cancel
            </button>
          </div>
        )}

        {mode === 'view' && (
          <Card>
            <Table
              headers={"Roll No.,Student,Course,Branch,Section,Semester,Actions".split(",")}
              rows={students.map((s, i) => [
                s.studentId,
                s.name,
                s.course,
                s.branch,
                s.section,
                s.semester,
                (
                  <div>
                    <button>View</button>
                    <button>Edit</button>
                    <button>Delete</button>
                  </div>
                ),
              ])}
            />
          </Card>
        )}
      </div>
    </Layout>
  )
}

export default Students