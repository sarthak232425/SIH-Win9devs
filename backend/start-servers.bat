@echo off
echo Starting SIH Backend Services...
echo ================================

echo.
echo [1/3] Checking MongoDB connection...
echo Make sure MongoDB is running on mongodb://localhost:27017
echo Or update the MONGODB_URI in .env file for MongoDB Atlas
echo.

echo [2/3] Starting Flask Server (Port 5000)...
start "Flask Server" cmd /k "cd /d %~dp0 && python flask_server.py"

echo.
echo [3/3] Starting Express Server (Port 5001)...
start "Express Server" cmd /k "cd /d %~dp0 && node expressServer.js"

echo.
echo ================================
echo Both servers are starting...
echo.
echo Flask Server:   http://localhost:5000
echo Express Server: http://localhost:5001
echo.
echo Press Ctrl+C in each window to stop the servers
echo ================================

pause