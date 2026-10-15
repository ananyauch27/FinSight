# cd C:\dev\finsight\backend
# .\venv\Scripts\Activate.ps1
# uvicorn app.main:app --reload

from fastapi import FastAPI

app = FastAPI(title="FinSight API")

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}