
import os
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db, get_current_user
from app.models import Upload, User
from app.routers.accounts import owned_account
from app.services.ingest import process_upload

router = APIRouter(tags=["uploads"])


# Upload a bank statement
@router.post("/uploads", status_code=202)
async def upload_file(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    account_id: UUID = Form(...),
    pdf_password: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Check file type
    ext = file.filename.rsplit(".", 1)[-1].lower()

    if ext not in {"pdf", "csv", "xlsx"}:
        raise HTTPException(400, "Only PDF, CSV, XLSX allowed")

    # Read file and check its size
    content = await file.read()
    max_size = settings.MAX_UPLOAD_MB * 1024 * 1024

    if len(content) > max_size:
        raise HTTPException(413, "File too large")

    # Check account ownership
    owned_account(db, user, account_id)

    # Save file with a random name
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    path = os.path.join(settings.UPLOAD_DIR, f"{uuid4()}.{ext}")

    with open(path, "wb") as f:
        f.write(content)

    # Save upload details in the database
    up = Upload(
        user_id=user.id,
        account_id=account_id,
        filename=file.filename,
        stored_path=path,
        file_type=ext,
        status="pending",
    )

    db.add(up)
    db.commit()
    db.refresh(up)

    # Process the file in the background
    background.add_task(process_upload, str(up.id), pdf_password)

    return {
        "id": str(up.id),
        "status": "processing",
    }


# Check upload status
@router.get("/uploads/{upload_id}")
def upload_status(
    upload_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Find the upload belonging to this user
    up = (
        db.query(Upload)
        .filter_by(id=upload_id, user_id=user.id)
        .first()
    )

    if not up:
        raise HTTPException(404, "Upload not found")

    return {
        "id": str(up.id),
        "status": up.status,
        "detected_bank": up.detected_bank,
        "rows_total": up.rows_total,
        "rows_inserted": up.rows_inserted,
        "rows_duplicate": up.rows_duplicate,
        "error_message": up.error_message,
