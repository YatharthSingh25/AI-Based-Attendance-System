import axios from "axios"

// API base URL - read from environment variable
// In production, set VITE_API_BASE_URL to your deployed backend URL
// e.g., https://your-backend-service.onrender.com
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

// Create axios instance with base URL and default headers
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
})

// Attach the current access token to every request at request time.
// Reading localStorage here (rather than once at module load) means tokens
// obtained after login are attached without a page reload.
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token")
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Auth APIs
export const authApi = {
  login: (email: string, password: string) => {
    // Backend uses OAuth2PasswordRequestForm: form-encoded username/password.
    // The server authenticates by email, so the email maps to "username".
    const form = new URLSearchParams()
    form.append("username", email)
    form.append("password", password)
    return api.post("/api/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
  },

  register: (userData: {
    email: string
    password: string
    name?: string
    role?: string
  }) => api.post("/api/auth/register", userData),

  getCurrentUser: () => {
    // This would typically verify the token with the backend
    // For now, return user from localStorage
    if (typeof window !== "undefined") {
      const user = localStorage.getItem("user")
      return user ? JSON.parse(user) : null
    }
    return null
  },
  setCurrentUser: (user: any) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("user", JSON.stringify(user))
    }
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      localStorage.removeItem("user")
    }
  },
}

// Student APIs
export const studentApi = {
  getStudents: () => api.get("/api/students"),

  createStudent: (studentData: {
    student_id: string
    name: string
    email: string
    course: string
    branch: string
    section: string
    semester: number
  }) => api.post("/api/students", studentData),

  getStudent: (studentId: string) =>
    api.get(`/api/students/${studentId}`),

  updateStudent: (studentId: string, studentData: {
    name?: string
    email?: string
    course?: string
    branch?: string
    section?: string
    semester?: number
  }) =>
    api.put(`/api/students/${studentId}`, studentData),

  deleteStudent: (studentId: string) =>
    api.delete(`/api/students/${studentId}`),

  enrollFace: (studentId: string, formData: FormData) =>
    api.post(`/api/students/${studentId}/enroll-face`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        // Handle upload progress if needed
      },
    }),
}

// Attendance APIs
export const attendanceApi = {
  getSessions: () => api.get("/api/attendance/sessions"),

  getSessionAttendance: (sessionId: string) =>
    api.get(`/api/attendance/${sessionId}`),

  createSession: (sessionData: {
    subject: string
    section: string
  }) => api.post("/api/attendance/sessions", sessionData),

  photoAttendance: (sessionId: string, imageFile: File | Blob) => {
    const formData = new FormData()
    formData.append("session_id", sessionId)
    formData.append("image_data", imageFile, "classroom-photo.jpg")
    return api.post("/api/attendance/photo", formData)
  },

  liveFrame: (sessionId: string, frameFile: File | Blob) => {
    const formData = new FormData()
    formData.append("session_id", sessionId)
    formData.append("frame_data", frameFile, "live-frame.jpg")
    return api.post("/api/attendance/live/frame", formData)
  },

  reviewAttendance: (attendanceId: string, action: string) =>
    api.post(`/api/attendance/${attendanceId}/review`, null, {
      params: { action },
    }),
}

// Analytics APIs
export const analyticsApi = {
  getOverview: () => api.get("/api/analytics/overview"),

  getStudentAnalytics: (studentId: string) =>
    api.get(`/api/analytics/student/${studentId}`),

  trainML: () => api.post("/api/ml/train"),

  getMLPredictions: () => api.get("/api/ml/predictions"),
}

// Reports APIs
export const reportsApi = {
  getDailyAttendance: (sessionId: string) =>
    api.get(`/api/attendance/${sessionId}`),

  exportCSV: (format: "CSV" | "Excel" | "PDF") =>
    api.post(`/api/reports/export`, { format }),
}

// Settings APIs
export const settingsApi = {
  getThresholds: () => api.get("/api/settings/thresholds"),

  updateThresholds: (thresholds: {
    highConfidence: number
    reviewThreshold: number
    unknownThreshold: number
  }) => api.post("/api/settings/thresholds", thresholds),

  getLivenessSettings: () => api.get("/api/settings/liveness"),

  updateLivenessSettings: (settings: {
    enabled: boolean
    spoofThreshold: number
  }) => api.post("/api/settings/liveness", settings),

  getMLSettings: () => api.get("/api/settings/ml"),

  updateMLSettings: (settings: {
    model: string
    autoTrain: boolean
  }) => api.post("/api/settings/ml", settings),
}

export default api