# FairLens AI Setup

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm

## 1) Backend Setup (FastAPI + ML)

### Windows PowerShell (recommended)

```powershell
cd backend
.\run_backend.ps1
```

What this does:
- creates local backend/venv if missing
- installs Python dependencies from requirements.txt
- starts API on http://localhost:8000

### macOS/Linux

```bash
cd backend
bash run_backend.sh
```

Manual alternative:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 2) Frontend Setup (Updated UI)

Open a second terminal while backend is running.

### Windows PowerShell

```powershell
cd frontend
.\run_frontend.ps1
```

### macOS/Linux

```bash
cd frontend
bash run_frontend.sh
```

Frontend runs at http://localhost:5173.

## 3) API Integration Notes

The updated frontend is migrated from fairlens-auditor and now lives in frontend/.

Frontend API adapter file:
- frontend/src/lib/api.ts

It maps backend responses into the UI-expected shapes for:
- analyze endpoint metrics
- AI explanation summary
- fix endpoint before/after + group-rate comparison

Backend base URL is configurable with:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Default is http://localhost:8000.

## 4) Verify Services

- Backend health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Frontend app: http://localhost:5173

## 5) Common Issues

- CORS errors: ensure backend is running on 8000 and frontend on 5173.
- Missing Python packages: rerun backend/run_backend.ps1 (or run_backend.sh).
- Frontend dependency errors: run npm install inside frontend/.
