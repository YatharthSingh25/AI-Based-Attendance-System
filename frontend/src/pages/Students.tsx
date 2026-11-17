import React, { useEffect, useState } from 'react'
import { Card, Table } from '../components/ui'
import Layout from '../layouts/MainLayout'
import { studentApi } from '../services/api'

interface Student {
  id: string
  student_id: string
  name: string
  email: string
  course: string
  branch: string
  section: string
  semester: number
  face_enrolled?: boolean
}

type Mode = 'view' | 'form' | 'enroll'

const EMPTY_FORM: Partial<Student> = {
  student_id: '',
  name: '',
  email: '',
  course: 'Data Structures',
  branch: 'CSE',
  section: 'A',
  semester: 1,
}

// The backend enforces this pattern; check it here so the user sees why.
const STUDENT_ID_PATTERN = /^[A-Z]{3}[0-9]{3}$/
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const errorMessage = (error: any, fallback: string): string => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    // FastAPI validation errors: surface the first field problem.
    const first = detail[0]
    const field = Array.isArray(first?.loc) ? first.loc[first.loc.length - 1] : null
    const msg = first?.msg || 'invalid value'
    return field ? `${field}: ${msg}` : msg
  }
  if (error?.message) return `${fallback} (${error.message})`
  return fallback
}

const Students: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<Mode>('view')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<Partial<Student>>(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [listError, setListError] = useState<string | null>(null)

  const [enrollStudent, setEnrollStudent] = useState<Student | null>(null)
  const [enrollFiles, setEnrollFiles] = useState<File[]>([])
  const [enrolling, setEnrolling] = useState(false)
  const [enrollMessage, setEnrollMessage] = useState<string | null>(null)
  const [enrollError, setEnrollError] = useState<string | null>(null)
  const [enrollSkipped, setEnrollSkipped] = useState<string[]>([])

  const loadStudents = async () => {
    setLoading(true)
    setListError(null)
    try {
      const response = await studentApi.getStudents()
      setStudents(Array.isArray(response.data) ? response.data : [])
    } catch (error: any) {
      setStudents([])
      setListError(errorMessage(error, 'Failed to load students.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStudents()
  }, [])

  const openAdd = () => {
    setEditingId(null)
    setForm(EMPTY_FORM)
    setFormError(null)
    setMode('form')
  }

  const openEdit = (student: Student) => {
    setEditingId(student.id)
    setForm({
      student_id: student.student_id,
      name: student.name,
      email: student.email,
      course: student.course,
      branch: student.branch,
      section: student.section,
      semester: student.semester,
    })
    setFormError(null)
    setMode('form')
  }

  const closeForm = () => {
    setMode('view')
    setEditingId(null)
    setFormError(null)
  }

  const saveStudent = async () => {
    const studentId = (form.student_id || '').trim().toUpperCase()
    const name = (form.name || '').trim()
    const email = (form.email || '').trim()

    if (!name) {
      setFormError('Name is required.')
      return
    }
    if (!editingId && !STUDENT_ID_PATTERN.test(studentId)) {
      setFormError(
        'Student ID must be 3 capital letters followed by 3 digits, for example CSE005.'
      )
      return
    }
    if (!email || !EMAIL_PATTERN.test(email)) {
      setFormError('A valid email address is required, for example cse005@college.edu.')
      return
    }

    setFormError(null)
    setSaving(true)
    try {
      if (editingId) {
        await studentApi.updateStudent(editingId, {
          name,
          email,
          course: form.course || 'Data Structures',
          branch: form.branch || 'CSE',
          section: form.section || 'A',
          semester: form.semester || 1,
        })
        setNotice(`${name} was updated.`)
      } else {
        await studentApi.createStudent({
          student_id: studentId,
          name,
          email,
          course: form.course || 'Data Structures',
          branch: form.branch || 'CSE',
          section: form.section || 'A',
          semester: form.semester || 1,
        })
        setNotice(`${name} (${studentId}) was added.`)
      }

      await loadStudents()
      setMode('view')
      setEditingId(null)
      setForm(EMPTY_FORM)
    } catch (error: any) {
      setFormError(errorMessage(error, 'Could not save the student.'))
    } finally {
      setSaving(false)
    }
  }

  const deleteStudent = async (student: Student) => {
    const confirmed = window.confirm(
      `Delete ${student.name} (${student.student_id})? Their attendance records will also be removed.`
    )
    if (!confirmed) return

    setNotice(null)
    setListError(null)
    try {
      await studentApi.deleteStudent(student.id)
      setNotice(`${student.name} (${student.student_id}) was deleted.`)
      await loadStudents()
    } catch (error: any) {
      setListError(errorMessage(error, 'Could not delete the student.'))
    }
  }

  const update = (field: keyof Student, value: string | number) =>
    setForm((current) => ({ ...current, [field]: value }))

  const openEnroll = (student: Student) => {
    setEnrollStudent(student)
    setEnrollFiles([])
    setEnrollMessage(null)
    setEnrollError(null)
    setEnrollSkipped([])
    setMode('enroll')
  }

  const closeEnroll = () => {
    setMode('view')
    setEnrollStudent(null)
    setEnrollFiles([])
    setEnrollMessage(null)
    setEnrollError(null)
    setEnrollSkipped([])
  }

  const saveEnrollment = async () => {
    if (!enrollStudent) return
    if (enrollFiles.length === 0) {
      setEnrollError('Choose at least one photo of the student.')
      return
    }

    setEnrollError(null)
    setEnrollMessage(null)
    setEnrolling(true)
    try {
      const formData = new FormData()
      enrollFiles.forEach((file) => formData.append('files', file))

      const response = await studentApi.enrollFace(enrollStudent.id, formData)
      setEnrollMessage(
        response.data?.message || 'Face photos were saved.'
      )
      setEnrollSkipped(
        Array.isArray(response.data?.skipped) ? response.data.skipped : []
      )
      setEnrollFiles([])
      await loadStudents()
    } catch (error: any) {
      setEnrollError(errorMessage(error, 'Could not enroll these photos.'))
    } finally {
      setEnrolling(false)
    }
  }

  return (
    <Layout>
      <h2>Students</h2>
      <div className="students-container">
        <div className="actions">
          <button onClick={openAdd} className="btn-primary">
            Add Student
          </button>
        </div>

        {notice && <p className="form-success">{notice}</p>}
        {listError && <p className="form-error">{listError}</p>}

        {mode === 'form' && (
          <div className="form-section">
            <h3>{editingId ? 'Edit Student' : 'Add New Student'}</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                saveStudent()
              }}
            >
              <div className="form-group">
                <label>Student ID</label>
                <input
                  type="text"
                  placeholder="CSE005"
                  value={form.student_id || ''}
                  onChange={(e) => update('student_id', e.target.value.toUpperCase())}
                  maxLength={6}
                  disabled={Boolean(editingId)}
                />
                <small>Format: 3 letters and 3 digits (CSE005). Cannot be changed later.</small>
              </div>
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  placeholder="Enter student name"
                  value={form.name || ''}
                  onChange={(e) => update('name', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  placeholder="cse005@college.edu"
                  value={form.email || ''}
                  onChange={(e) => update('email', e.target.value)}
                />
                <small>
                  The student signs in with this email, so it must match the
                  account they register.
                </small>
              </div>
              <div className="form-group">
                <label>Course</label>
                <select
                  value={form.course || 'Data Structures'}
                  onChange={(e) => update('course', e.target.value)}
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
                  value={form.branch || 'CSE'}
                  onChange={(e) => update('branch', e.target.value)}
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
                  value={form.section || 'A'}
                  onChange={(e) => update('section', e.target.value)}
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
                  value={form.semester || 1}
                  onChange={(e) => update('semester', Number(e.target.value))}
                />
              </div>

              {formError && <p className="form-error">{formError}</p>}

              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : editingId ? 'Save Changes' : 'Save Student'}
                </button>
                <button type="button" className="btn-outline" onClick={closeForm}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {mode === 'enroll' && enrollStudent && (
          <div className="form-section">
            <h3>Enroll Face — {enrollStudent.name} ({enrollStudent.student_id})</h3>
            <p>
              Upload 3-5 clear, front-facing photos of this student. One face per
              photo. These photos let attendance be marked from a group picture.
            </p>
            <div className="form-group">
              <label>Face photos</label>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={(e) => setEnrollFiles(Array.from(e.target.files || []))}
              />
              <small>
                {enrollFiles.length > 0
                  ? `${enrollFiles.length} photo(s) selected.`
                  : 'No photos selected yet.'}
              </small>
            </div>

            {enrollError && <p className="form-error">{enrollError}</p>}
            {enrollMessage && <p className="form-success">{enrollMessage}</p>}
            {enrollSkipped.length > 0 && (
              <ul className="enroll-skipped">
                {enrollSkipped.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            )}

            <div className="form-actions">
              <button
                type="button"
                className="btn-primary"
                onClick={saveEnrollment}
                disabled={enrolling || enrollFiles.length === 0}
              >
                {enrolling ? 'Saving face photos...' : 'Save Face Photos'}
              </button>
              <button type="button" className="btn-outline" onClick={closeEnroll}>
                Close
              </button>
            </div>
          </div>
        )}

        {mode === 'view' && (
          <Card>
            {loading ? (
              <p>Loading students...</p>
            ) : students.length === 0 ? (
              <p>No students yet. Use Add Student to create the first one.</p>
            ) : (
              <Table
                headers={
                  'Roll No.,Student,Email,Course,Section,Face,Actions'.split(',')
                }
                rows={students.map((student) => [
                  student.student_id,
                  student.name,
                  student.email || '-',
                  student.course,
                  student.section,
                  student.face_enrolled ? 'Enrolled' : 'Not enrolled',
                  <div key={student.id} className="row-actions">
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => openEnroll(student)}
                    >
                      Enroll Face
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => openEdit(student)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn-danger"
                      onClick={() => deleteStudent(student)}
                    >
                      Delete
                    </button>
                  </div>,
                ])}
              />
            )}
          </Card>
        )}
      </div>
    </Layout>
  )
}

export default Students
