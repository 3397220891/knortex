import io

from fastapi.testclient import TestClient

import api.endpoints.upload as upload_module
import tasks
from api.endpoints.documents import get_document_query
from main import app
from services.document_query import DocumentQuery
from services.document_store import DocumentStore


def test_upload_then_poll_task_status(tmp_path, db_session_factory, monkeypatch):
    monkeypatch.setattr(upload_module.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(
        tasks.document_store_module,
        "document_store",
        DocumentStore(session_factory=db_session_factory),
    )
    app.dependency_overrides[get_document_query] = lambda: DocumentQuery(
        session_factory=db_session_factory
    )

    try:
        # No `with` block: avoids triggering the real startup event, which would
        # try to connect to the production Postgres URL in db.base.engine.
        client = TestClient(app)

        response = client.post(
            "/upload",
            files={
                "file": (
                    "sample.txt",
                    io.BytesIO(b"John Smith is the CEO of TechCorp Inc."),
                    "text/plain",
                )
            },
        )
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "processing"
        assert body["filename"] == "sample.txt"
        task_id = body["task_id"]

        # Celery runs in eager mode for tests, so by the time /upload returns,
        # the task has already finished - no need to actually poll.
        status_response = client.get(f"/tasks/{task_id}")
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["status"] == "completed"
        assert status_body["result"]["filename"] == "sample.txt"
        assert status_body["result"]["extraction_result"]["entity_count"] > 0

        unknown_response = client.get("/tasks/does-not-exist")
        assert unknown_response.status_code == 200
        assert unknown_response.json()["status"] == "processing"
    finally:
        app.dependency_overrides.clear()
