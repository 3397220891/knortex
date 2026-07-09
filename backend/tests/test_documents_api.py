from fastapi.testclient import TestClient

from api.endpoints.documents import get_document_query
from main import app
from services.document_query import DocumentQuery
from services.document_store import DocumentStore
from services.information_extractor import InformationExtractor


def _seed(db_session_factory):
    store = DocumentStore(session_factory=db_session_factory)
    text = "John Smith is the CEO of TechCorp Inc."
    extraction_result = InformationExtractor.process_text(text)
    return store.save_extraction(
        filename="test.txt",
        file_type="txt",
        saved_path="uploads/test.txt",
        content=text,
        status="success",
        extraction_result=extraction_result,
    )


def test_documents_and_evidence_endpoints(db_session_factory):
    pg_result = _seed(db_session_factory)
    john_id = pg_result["entity_ids"]["John Smith"]

    app.dependency_overrides[get_document_query] = lambda: DocumentQuery(
        session_factory=db_session_factory
    )
    try:
        # No `with` block: avoids triggering the real startup event, which would
        # try to connect to the production Postgres URL in db.base.engine.
        client = TestClient(app)

        list_response = client.get("/documents")
        assert list_response.status_code == 200
        assert list_response.json()[0]["filename"] == "test.txt"

        evidence_response = client.get(f"/entities/{john_id}/evidence")
        assert evidence_response.status_code == 200
        body = evidence_response.json()
        assert body["name"] == "John Smith"
        assert body["relations"][0]["type"] == "CEO_OF"
        assert "CEO" in body["relations"][0]["evidence"][0]["matched_text"]

        missing_response = client.get("/entities/does-not-exist/evidence")
        assert missing_response.status_code == 404
    finally:
        app.dependency_overrides.clear()
