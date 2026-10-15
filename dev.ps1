# Starts backend and frontend in two separate windows
$root = $PSScriptRoot

Start-Process powershell -ArgumentList "-NoExit","-Command",
  "cd '$root\backend'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

Start-Process powershell -ArgumentList "-NoExit","-Command",
  "cd '$root\frontend'; npm run dev"