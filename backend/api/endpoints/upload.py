import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from config import settings
from models.knowledge_models import UploadAcceptedResponse
from tasks import process_document_task

router = APIRouter()

ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")


@router.post("/upload", response_model=UploadAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_file(file: UploadFile = File(...)):
    """Save the upload and hand parsing/extraction/storage off to a Celery worker.

    Returns immediately with a task id instead of blocking the request on
    parsing + NER + two database writes - poll GET /tasks/{task_id} for the result.
    """
    if not file.filename.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Only PDF, Word documents and text files are supported",
        )

    file_id = str(uuid.uuid4())
    file_extension = file.filename.rsplit(".", 1)[-1]
    saved_filename = f"{file_id}.{file_extension}"

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    try:
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    task = process_document_task.delay(file_path, file.filename, file_extension.lower())

    return {
        "task_id": task.id,
        "file_id": file_id,
        "filename": file.filename,
        "status": "processing",
        "message": "File uploaded, processing in background",
    }
