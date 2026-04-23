# Quiz Or Sheet v2 - Startup Script

Write-Host "🚀 Starting Quiz Or Sheet v2..." -ForegroundColor Cyan

# Start Backend
Write-Host "📦 Initializing Backend (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py"

# Start Frontend
Write-Host "🎨 Initializing Frontend (Next.js)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "✅ Both servers are starting in separate windows!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
