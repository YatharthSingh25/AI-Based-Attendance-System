# AI-Based Intelligent Classroom Attendance System

> Deployment/security setup: see [DEPLOYMENT.md](DEPLOYMENT.md). Public
> registration creates STUDENT/FACULTY accounts only; ADMIN accounts are
> provisioned only with `python -m app.seed_admin`.

## Overview
An academic B.Tech major project: "AI-Based Intelligent Classroom Attendance System Using Face Recognition, Live Multi-Face Detection and Machine Learning".

The application exposes two attendance flows, both currently **demo/simulated**:
- **Classroom Photo Attendance**: Upload a classroom image; the API returns a clearly labeled simulated result.
- **Live Camera Attendance**: Uses the browser webcam preview; live-frame responses are simulated.

Face detection, face recognition, liveness, and ML inference are **not implemented**.
See [DEPLOYMENT.md](DEPLOYMENT.md) for the verified deployment configuration.

## Architecture
- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + SQLAlchemy + PostgreSQL
- **Database**: PostgreSQL (managed host recommended)
- **AI/ML**: Mock/demo mode by default; real model integration separate
- **Authentication**: JWT with bcrypt password hashing
- **Roles**: ADMIN, FACULTY, STUDENT

### Role permissions

| Area | Allowed roles |
|---|---|
| Student CRUD, face enrollment | `FACULTY`, `ADMIN` |
| Attendance sessions, photo/live processing, review | `FACULTY`, `ADMIN` |
| Analytics, reports, ML predictions | `FACULTY`, `ADMIN` |
| Read settings | `FACULTY`, `ADMIN` |
| Update settings, train ML | `ADMIN` |

Public routes: `/health`, `/api/auth/login`, `/api/auth/register`. The `STUDENT`
role is authenticated but currently has no staff/admin endpoints. See
[DEPLOYMENT.md](DEPLOYMENT.md#authorization-policy) for the per-route matrix.

## Folder Structure
```
attendance-ai/
├── frontend/           # React Vite frontend
├── backend/            # FastAPI backend
├── .env.example        # Backend environment variables
├── frontend/.env.example  # Frontend environment variables
├── tests/              # Backend API tests
├── backend/alembic/    # Unverified migrations (startup create_all is supported)
└── README.md           # This file
```

## Phase 1: Project Setup + Database + Authentication
1. Clone the repository
2. Install dependencies (see below)
3. Create a hosted PostgreSQL database
4. Configure environment variables
5. Start the backend (tables are created automatically) and bootstrap an admin with `python -m app.seed_admin`
6. Start the frontend server

## Phase 2: Student Registration + Student Management
- Student CRUD endpoints require `FACULTY` or `ADMIN`; `STUDENT` requests receive 403
- Full route-by-route permissions are documented in [DEPLOYMENT.md](DEPLOYMENT.md#authorization-policy)
- Add students with Student ID, Name, Email, Course, Branch, Section, Semester
- Enroll face images (3-5 per student)
- Generate face embeddings (mock mode available)

## Phase 3-4: Face Detection + Recognition Service
- Mock mode: Synthetic face detection/recognition for demonstration
- Real mode: Requires YOLO/InsightFace/ArcFace model integration
- API endpoints: `/api/attendance/photo`, `/api/attendance/live/frame`

## Phase 5: Attendance Engine
- Create attendance sessions via `/api/attendance/sessions`
- Photo attendance: `/api/attendance/photo`
- Live attendance: `/api/attendance/live/frame`
- Teacher review: `/api/attendance/{id}/review`
- Duplicate prevention: `UNIQUE(student_id, session_id)` database constraint

## Phase 6: Live Camera + Multi-Face Tracking
- Browser webcam access via `navigator.mediaDevices.getUserMedia()`
- Simulated tracking IDs in demo mode
- Prevents repeated attendance records for the same student

## Phase 7: Liveness Abstraction
- Mock liveness provider available
- Real liveness model integration separate
- Clearly disclaimed: "Liveness is an additional verification layer and is not guaranteed to stop every attack"

## Phase 8: Teacher Verification
- Review panel for uncertain/low-confidence results
- Actions: Confirm, Change Student, Reject, Mark Unknown
- All manual corrections stored in audit log

## Phase 9: Analytics
- Overview stats (Present/Absent/Unknown percentages)
- Subject-wise attendance charts (Recharts)
- Students at risk (< 75% attendance)

## Phase 10: ML Attendance-Risk Prediction (Planned)
- Planned models: Logistic Regression, Random Forest, XGBoost
- Features: current_attendance, classes_attended, classes_missed, etc.
- Output: LOW RISK, MEDIUM RISK, HIGH RISK
- **Important**: Predicts only attendance shortage risk, not academic performance
- The current `/api/ml/*` endpoints are demo/placeholder responses; no model is trained
- `POST /api/ml/train` returns HTTP 501 `{"status": "not_implemented"}` and does not train a model
- `GET /api/ml/predictions` returns a rule-based list only; it is not ML inference

## Phase 11: Reports
- Daily attendance exports (PDF/CSV/Excel - demo mode)
- Subject attendance summaries
- Student attendance histories
- Low attendance students list

## Phase 12: Testing + Documentation
- Backend pytest tests
- Frontend production build
- Complete README and deployment documentation

## Deployment Instructions

### 1. Review and Push Code to GitHub
```bash
# From the attendance-ai directory
git add .
git commit -m "Final year project - AI attendance system"
git push origin main
```

### 2. Create Frontend Hosting Project (Vercel)
1. Go to https://vercel.com and create a new account
2. Click "Add New Project" → "Import from GitHub"
3. Select repository: `YatharthSingh25/AI-Based-Attendance-System`
4. Framework Preset: **Vite**
5. Root Directory: `attendance-ai/frontend`
6. Build Command: `vite build`
7. Output Directory: `dist`
8. **Environment Variables** (critical - set these):
   - `VITE_API_BASE_URL`: `https://your-backend-service.onrender.com`
   - `VITE_APP_NAME`: `AI Attendance System`
   - `VITE_ENVIRONMENT`: `production`
9. Click "Deploy"

### 3. Create Backend Service (Render)
1. Go to https://render.com and create a new account
2. Click "New Web Service" → "Connect Repository"
3. Select same GitHub repository
4. Root Directory: `attendance-ai/backend`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. **Environment Variables** (required):
   - `ENVIRONMENT`: `production` (enables strict JWT and database validation)
   - `DATABASE_URL`: `postgresql://username:password@host:5432/db_name` (from hosted DB; SQLite/local default rejected)
   - `JWT_SECRET`: Generate a secure random string (min 32 characters)
   - `JWT_ALGORITHM`: `HS256`
   - `JWT_EXPIRES_MINUTES`: `30`
   - `CORS_ORIGINS`: `https://your-vercel-app.vercel.app` (add localhost only for local testing)
8. Click "Create Web Service"

### 4. Create Hosted Database
1. **Option A: Render PostgreSQL**
   - In your Render dashboard, add a PostgreSQL database
   - Connect it to your web service
   - The DATABASE_URL will be auto-filled

   **Option B: External PostgreSQL (ElephantSQL, Supabase, etc.)**
   - Create a PostgreSQL database account
   - Get the connection string: `postgresql://user:password@host:port/dbname`
   - Set as `DATABASE_URL` env var in Render

   **Never use the default `postgresql://postgres:postgres@localhost:5432/attendance_ai` in production!**

### 5. Database Initialization and Administrator Bootstrap
Tables are created automatically on backend startup by `create_db_and_tables()`
using SQLAlchemy `create_all` with `checkfirst=True`. Production startup first
rejects a missing/SQLite/local-default `DATABASE_URL`. This only adds missing
tables and does not drop or reset existing data. No manual step is required.

Create the first administrator once, from the backend directory, using the
environment-based seed command (public registration cannot create admins):

```powershell
$env:ADMIN_EMAIL = "admin@example.com"
$env:ADMIN_PASSWORD = "<strong-password-min-12-chars>"
.\.venv\Scripts\python.exe -m app.seed_admin
Remove-Item Env:\ADMIN_EMAIL, Env:\ADMIN_PASSWORD
```

Alembic files exist in `backend/alembic`, but migrations are not the supported
initialization path and have not been validated against PostgreSQL. See
[DEPLOYMENT.md](DEPLOYMENT.md) for PostgreSQL verification steps.

Tables: users, students, face_embeddings, attendance_sessions, attendance, audit_logs, timetable, ml_predictions.

### 6. AI Model Files (Not Implemented)
No face detection, face recognition, liveness, or ML model loading is
implemented. `/api/attendance/photo` and `/api/attendance/live/frame` return
placeholder responses and do not create attendance records. Do not represent
these results as real biometric predictions. There are no AI model environment
variables consumed by the application.

**Cost Estimate (Monthly)**:
- Render Free Tier: Backend URL + 750 hours/month (sufficient for development)
- Render PostgreSQL: $7-15/month
- Vercel Pro: $20/month (custom domains, higher bandwidth)
- **Total: ~$25-40/month** for production-ready deployment

### 7. Deploy the Services
1. Visit your Vercel URL: `https://your-app-name.vercel.app`
2. Visit your Render URL: `https://your-service-name.onrender.com`
3. Test the backend health: `GET https://your-service-name.onrender.com/health`
   - Expected: `{"status":"healthy","service":"AI Attendance System API","version":"1.0.0"}`
4. Open the Vercel app and test:
    - Student enrollment
    - Login with a registered account
    - Photo attendance processing (shows a demo disclaimer)
    - Live camera interface (shows an API pending message)
    - Analytics and reports

### 8. Testing the Connected Services
**Backend Health Check:**
```
GET https://your-backend.onrender.com/health
```
Expected: `{"status":"healthy","service":"AI Attendance System API","version":"1.0.0"}`

**Frontend-to-Backend Communication:**
1. Visit frontend URL
2. Login with faculty credentials
3. Navigate to Students → should fetch data from backend
4. Navigate to Take Attendance → should show photo/live modes
5. Navigate to Analytics → should show stats from backend
6. Check browser console for no red error messages

**Student Enrollment Persistence:**
1. Add a new student via `/students`
2. Reload the page and confirm the student is still listed
3. Create an attendance session via `/api/attendance/sessions` if needed
4. Photo/live attendance endpoints return simulated results and do **not**
   create attendance records in this build

**CORS Verification:**
- No CORS errors in browser console
- All API calls succeed with proper credentials
- `withCredentials` works if using cookie-based auth

**AI Mode Verification:**
- Demo mode active by default
- All AI results clearly labeled as simulated/mock
- No fake AI claims or results
- "DEMO MODE" banner visible in UI
- Real AI mode is not implemented; no model files or model environment variables are supported

### 9. Troubleshooting

**CORS Errors:**
- Verify `CORS_ORIGINS` env var in Render includes your Vercel URL
- Ensure no extra spaces in comma-separated list
- Try: `CORS_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app`

**Database Connection Errors:**
- Verify `DATABASE_URL` is correct
- Ensure PostgreSQL is running and accessible
- Check firewall rules allow Render-to-DB connection
- Test with: `python -c "from app.database import create_db_and_tables; create_db_and_tables()"`

**Build Failures:**
- Frontend: `npm run build` → check `dist/` folder exists
- Backend: `pip install -r requirements.txt` → ensure all packages install
- Ensure `node_modules/` and `venv/` are not committed

**Authentication Errors:**
- Verify `JWT_SECRET` is set (not the default placeholder)
- Ensure login POST sends form-encoded `username` (the account email) and `password`
- Check browser console for JWT decode errors

**AI Model Behavior:**
- No model files are loaded; attendance endpoints always return demo responses
- Do not commit model weights or personal face images to git

## Security & Privacy

### Secrets Management
- **Never** commit `.env` files to git
- All secrets in hosting provider dashboard (Render, Vercel)
- `JWT_SECRET` must be changed from default placeholder
- `DATABASE_URL` must use production credentials

### Biometric Data Privacy
- Face embeddings are biometric data - subject to privacy regulations
- Minimize retention - delete unused embeddings
- Inform users about biometric data collection in privacy policy
- **Do not use real student biometric data for testing without consent**
- Embedding vectors stored securely in PostgreSQL

### API Security
- Role-based access is enforced server-side: staff routes require `FACULTY`/`ADMIN`; settings writes and ML training require `ADMIN`
- `STUDENT` accounts currently have no protected staff/admin endpoints
- Rate limiting recommended for production
- File upload size limits (currently no limit - add in production)
- Uploaded classroom photos should be scanned for malware
- HTTPS required on both frontend and backend
- Secure cookie flags if using session-based auth

### Production Checklist
- [ ] `JWT_SECRET` changed from default
- [ ] `DATABASE_URL` uses production PostgreSQL credentials (not SQLite/local default)
- [ ] Live PostgreSQL verification test run successfully (see DEPLOYMENT.md)
- [ ] RBAC verified: student gets 403, faculty/admin access per matrix
- [ ] `CORS_ORIGINS` includes only actual frontend domains
- [ ] HTTPS enabled on both services
- [ ] No secrets in Git history
- [ ] Demo mode disclaimer visible
- [ ] Browser console: no red error messages
- [ ] Backend `/health` returns 200
- [ ] Student CRUD works via API
- [ ] Attendance duplicate prevention verified
- [ ] CORS configured correctly
- [ ] Environment variables set in both Render and Vercel dashboards

## Demo Mode vs Real AI Mode

### Demo Mode (Default)
- ✅ Active immediately after deployment
- ✅ Uses mock/synthetic face detection and recognition
- ✅ Clearly labeled as simulated results
- ✅ No real biometric processing
- ✅ Fast, works on any hardware
- ⚠️ Persistent warning: "This result is simulated and is not generated by a live recognition model"

### Real AI Mode (Not Implemented)
- No model loading, inference, or model-path configuration exists
- `/api/attendance/photo` and `/api/attendance/live/frame` return placeholder responses
- Real recognition is future work requiring code, tested model files, and a privacy review
- ⚠️ **Do not claim real face recognition works in this build**

**Never present simulated results as real biometric predictions without explicit disclosure.**

## Quick Reference: Environment Variables

| Variable | Service | Description | Example |
|----------|---------|-------------|---------|
| `ENVIRONMENT` | Backend | `production` enforces strict JWT and PostgreSQL validation | `production` |
| `DATABASE_URL` | Backend | PostgreSQL connection string (required in production) | `postgresql://user:pw@host:5432/db` |
| `VITE_API_BASE_URL` | Frontend | Backend API URL (build time) | `https://api.onrender.com` |
| `JWT_SECRET` | Backend | JWT signing key (32+ chars, unique) | `<generated-secret>` |
| `CORS_ORIGINS` | Backend | Allowed origins (comma-sep) | `http://localhost:5173,https://vercel.app` |
| `JWT_ALGORITHM` | Backend | JWT algorithm (`HS256`/`HS384`/`HS512`) | `HS256` |
| `JWT_EXPIRES_MINUTES` | Backend | Token lifetime, 1-1440 | `30` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Backend seed only | One-off admin bootstrap | `<admin@example.com>` / `<strong-password>` |

Face detection/recognition and liveness are not implemented; those endpoints
remain placeholders regardless of configuration.

## Git Ignored Files
The following are intentionally NOT committed to git (per `.gitignore`):
- `.env*` (environment variables with secrets)
- `backend/*.pt`, `backend/*.onnx`, `backend/*.pth` (model weights)
- `backend/venv/`, `backend/.venv/` (virtual environments)
- `frontend/node_modules/` (npm packages)
- `backend/*.log`, `frontend/*.log` (log files)
- `backend/uploads/`, `backend/face_data/` (uploaded biometric data)
- `alembic/versions/*.py` (migration scripts - generated, not static)

## Future Scope
- Real face detection with YOLO/InsightFace models
- Real face recognition with ArcFace models
- Liveness/anti-spoofing detection
- Multi-factor authentication
- Mobile application
- Parent-student portal
- Advanced analytics with academic performance correlation (separate from attendance risk)
- Offline attendance mode
- SMS/Email notifications for absences
