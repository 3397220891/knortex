from celery.result import AsyncResult
from fastapi import APIRouter

from celery_app import celery_app
from models.knowledge_models import TaskStatusResponse

router = APIRouter()

_STATUS_MAP = {
    "PENDING": "processing",
    "STARTED": "processing",
    "RETRY": "processing",
    "SUCCESS": "completed",
    "FAILURE": "failed",
}


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """Poll the status of a background document-processing task."""
    async_result = AsyncResult(task_id, app=celery_app)
    status = _STATUS_MAP.get(async_result.state, async_result.state.lower())

    if status == "completed":
        return {"task_id": task_id, "status": status, "result": async_result.result}
    if status == "failed":
        return {"task_id": task_id, "status": status, "error": str(async_result.result)}
    return {"task_id": task_id, "status": status}
