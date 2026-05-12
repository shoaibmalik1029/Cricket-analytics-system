# Cricket Analytics - Setup & Running Instructions

## Prerequisites
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Running the Application (Full Stack)

You need **TWO terminal windows/tabs** - one for backend, one for frontend:

### Terminal 1: Backend (Python FastAPI)
```bash
cd c:\Users\HP\cricket_analysis
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Terminal 2: Frontend (React/Vite)
```bash
cd c:\Users\HP\cricket_analysis\frontend
npm install  # (only needed first time)
npm run dev
```

**Expected output:**
```
  ➜  Local:   http://localhost:5173/
```

## Verification

Once both are running:

1. **Backend Health Check:**
   - Visit `http://127.0.0.1:8000/health` in browser
   - Should show: `{"status":"ok"}`

2. **Frontend:**
   - Visit `http://localhost:5173/`
   - Should load the cricket analytics dashboard

3. **API Integration:**
   - Frontend should automatically connect to backend via proxy
   - All dashboard sections should populate with data

## Troubleshooting

### Backend shows no output
- Ensure you're in the correct directory: `c:\Users\HP\cricket_analysis`
- Check that port 8000 is not in use: `netstat -ano | findstr :8000`
- If port is in use, kill the process or use a different port: `--port 8001`

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check browser console (F12) for CORS or connection errors
- Ensure Vite proxy is configured correctly (see `vite.config.js`)

### Dependencies missing
- Run `pip install -r requirements.txt` to install all Python packages
- Run `npm install` in the `frontend/` directory for Node packages

## Quick Start Scripts

**Windows Batch Files:**
- `start_app.bat` - Attempt to start both (if configured)
- `run_backend.bat` - Start backend only
- `run_frontend.bat` - Start frontend only

## Architecture

- **Backend:** Python FastAPI at `http://127.0.0.1:8000`
- **Frontend:** React/Vite at `http://localhost:5173`
- **Proxy:** Vite proxies `/api/*` requests to backend
- **Data:** CSV files loaded from `c:\Users\HP\Downloads\archive (12)\Cricket statsguru-data`
