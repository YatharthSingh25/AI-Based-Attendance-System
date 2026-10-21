import React, { useEffect, useState } from 'react'
import { Card, Table, Badge } from '../components/ui'
import Layout from '../layouts/MainLayout'
import api, { studentApi } from '../services/api'

interface Student {
  id: string
  student_id: string
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
    student_id: '',
    name: '',
    email: '',
    course: '',
    branch: '',
    section: '',
    semester: 1,
  })
  const [enrollImages, setEnrollImages] = useState<FileList | null>(null)

  // Fetch students from backend
  useEffect(() => {
    const fetchStudents = async () => {
      setLoading(true)
      try {
        const response = await studentApi.getStudents()
        setStudents(response.data || [])
      } catch (error) {
        console.error('Failed to fetch students:', error)
        // Do not fall back to mock data - show empty list and alert user
        setStudents([])
      } finally {
        setLoading(false)
      }
    }
    fetchStudents()
  }, [])

  const handleAddStudent = () => {
    setMode('add')
  }

  const handleEnrollFace = () => {
    setMode('enroll')
  }

  const saveStudent = async () => {
    if (!newStudent.name || !newStudent.student_id) return
    try {
      await studentApi.createStudent({
        student_id: newStudent.student_id,
        name: newStudent.name,
        email: newStudent.email || '',
        course: newStudent.course || 'Data Structures',
        branch: newStudent.branch || 'CSE',
        section: newStudent.section || 'A',
        semester: newStudent.semester || 1,
      })
      // Refresh the list
      const response = await studentApi.getStudents()
      setStudents(response.data || [])
      setMode('view')
      setNewStudent({
        student_id: '',
        name: '',
        email: '',
        course: '',
        branch: '',
        section: '',
        semester: 1,
      })
    } catch (error) {
      console.error('Failed to create student:', error)
    }
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEnrollImages(e.target.files as FileList)
  }

  const generateEmbedding = async () => {
    if (!enrollImages) return
    // Would process images and generate face embeddings via API
    // For now, alert the user
    alert('Face embedding generation - API integration pending')
    setEnrollImages(null)
    setMode('view')
  }

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
                  value={newStudent.student_id || ''}
                  onChange={(e) => setNewStudent({ ...newStudent, student_id: e.target.value })}
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
              <button type="button" className="btn-outline" onClick={() => setMode('view')}>
                Cancel
              </button>
            </form>
          </div>
        )}

        {mode === 'enroll' && (
          <div className="form-section">
            <h3>Enroll Face Images</h3>
            <p>Student: {newStudent?.name || 'Select student'} ({newStudent?.student_id || ''})</p>
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
                s.student_id,
                s.name,
                s.course,
                s.branch,
                s.section,
                s.semester,
                (
                  <div key={s.id}>
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