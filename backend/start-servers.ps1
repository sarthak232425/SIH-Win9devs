# PowerShell script to start both backend servers
Write-Host "Starting SIH Backend Services..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

Write-Host "[1/3] Checking MongoDB connection..." -ForegroundColor Yellow
Write-Host "Make sure MongoDB is running on mongodb://localhost:27017" -ForegroundColor Yellow
Write-Host "Or update the MONGODB_URI in .env file for MongoDB Atlas" -ForegroundColor Yellow
Write-Host ""

Write-Host "[2/3] Starting Flask Server (Port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python flask_server.py" -WindowStyle Normal

Write-Host ""
Write-Host "[3/3] Starting Express Server (Port 5001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; node expressServer.js" -WindowStyle Normal

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Both servers are starting..." -ForegroundColor Green
Write-Host ""
Write-Host "Flask Server:   http://localhost:5000" -ForegroundColor Cyan
Write-Host "Express Server: http://localhost:5001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the servers" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Green

# Keep this window open
Read-Host "Press Enter to close this launcher window"