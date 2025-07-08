# Set execution policy for this script
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "Starting Snake Game AI Application..." -ForegroundColor Green

# Start Backend Server in existing venv
Write-Host "Starting Backend Server in virtual environment..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python app.py" -Wait:$false

# Wait for backend to initialize
Write-Host "Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Start Frontend Server
Write-Host "Starting Frontend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm start"

# Wait for frontend to initialize
Write-Host "Waiting for frontend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Open the web application in default browser
Write-Host "Opening web application in default browser..." -ForegroundColor Cyan
Start-Process "http://localhost:8080"

Write-Host "All servers started! The web application should open automatically." -ForegroundColor Green
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown') 