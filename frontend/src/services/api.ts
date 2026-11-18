import axios from "axios"

// API base URL - read from environment variable
// In production, set VITE_API_BASE_URL to your deployed backend URL
// e.g., https://your-backend-service.onrender.com
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

export type LoginTab = "teacher" | "student"

export const isTeacherRole = (role?: string | null): boolean => {
  const value = (role || "").toUpperCase()
  return value === "FACULTY" || value === "ADMIN"
}

// A token is only useful while it is unexpired. The backend answers every JWT
// problem (expired, tampered, wrong secret) with the same 401, so check the
// embedded expiry here to send the user to the login page before an action
// fails with "Invalid authentication credentials".
const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
  try {
    const part = token.split(".")[1]
    if (!part) return null
    const base64 = part.replace(/-/g, "+").replace(/_/g, "/")
    const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=")
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}

const isTokenExpired = (token: string, skewSeconds = 30): boolean => {
  const payload = decodeJwtPayload(token)
  const exp = payload?.exp
  if (typeof exp !== "number") {
    // Unreadable expiry: let the server decide rather than logging out blindly.
    return false
  }
  return exp * 1000 <= Date.now() + skewSeconds * 1000
}

const clearSession = () => {
  if (typeof window === "undefined") return
  localStorage.removeItem("access_token")
  localStorage.removeItem("user")
}

export const SESSION_EXPIRED_PARAM = "expired"

const redirectToLogin = () => {
  if (typeof window === "undefined") return
  if (window.location.pathname === "/login") return
  window.location.assign(`/login?${SESSION_EXPIRED_PARAM}=1`)
}

// Create axios instance with base URL. Content-Type is deliberately not set
// here: axios then sends JSON for plain objects and multipart (with boundary)
// for FormData. A global application/json default would serialise uploads to
// an empty object.
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
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

// A 401 means the stored token is no longer accepted (most often expired).
// Clear it and send the user to the login page instead of surfacing the raw
// "Invalid authentication credentials" message from the backend. The login
// request itself is exempt: there a 401 means wrong credentials.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const url: string = error?.config?.url || ""
    const isLoginAttempt = url.includes("/api/auth/login")

    if (status === 401 && !isLoginAttempt) {
      clearSession()
      redirectToLogin()
    }

    return Promise.reject(error)
  }
)

// Auth APIs
export const authApi = {
  login: (email: string, password: string, tab: LoginTab = "teacher") => {
    // Backend uses OAuth2PasswordRequestForm: form-encoded username/password.
    // The server authenticates by email, so the email maps to "username".
    // "scope" carries the chosen login tab; the backend rejects a tab that
    // does not match the account's real role.
    const form = new URLSearchParams()
    form.append("username", email)
    form.append("password", password)
    form.append("scope", tab)
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

  // First-time password setup for a student whose class record the teacher
  // created. Returns a token, so the student is signed in straight away.
  activate: (email: string, password: string) =>
    api.post("/api/auth/activate", { email, password }),

  getCurrentUser: () => {
    // This would typically verify the token with the backend
    // For now, return user from localStorage
    if (typeof window !== "undefined") {
      const user = localStorage.getItem("user")
      if (!user) return null
      try {
        return JSON.parse(user)
      } catch {
        localStorage.removeItem("user")
        return null
      }
    }
    return null
  },
  setCurrentUser: (user: any) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("user", JSON.stringify(user))
    }
  },

  // True only when a token exists and has not expired. Route guards use this
  // so a stale token lands on the login page instead of the first API call.
  hasValidSession: (): boolean => {
    if (typeof window === "undefined") return false
    const token = localStorage.getItem("access_token")
    if (!token) return false
    if (isTokenExpired(token)) {
      clearSession()
      return false
    }
    return true
  },

  logout: () => {
    clearSession()
  },
}

// Student self-service APIs - always scoped to the signed-in account
export const meApi = {
  getMe: () => api.get("/api/me"),

  getMyStudent: () => api.get("/api/me/student"),

  getMyAttendance: () => api.get("/api/me/attendance"),
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
    // Do not pass a headers object: the instance default is JSON, and axios
    // only sets the multipart boundary itself when the config has no override.
    api.post(`/api/students/${studentId}/enroll-face`, formData),
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