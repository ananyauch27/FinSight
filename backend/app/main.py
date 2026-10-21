# cd C:\dev\finsight\backend
# .\venv\Scripts\Activate.ps1
# uvicorn app.main:app --reload

# git add .
# git commit -m "Describe your changes"
# git push


from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (auth,# accounts, uploads, transactions, categories,
                        # analytics, recurring, alerts, budgets, goals, insights
                        )

app = FastAPI(title="FinSight API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
for r in (auth,# accounts, uploads, transactions, categories, analytics,
          #recurring, alerts, budgets, goals, insights
           ):
    app.include_router(r.router, prefix=PREFIX)

@app.get(f"{PREFIX}/health")
def health():
    return {"status": "ok"}
