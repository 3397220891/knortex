from db.models import Document, EntityRecord
from models.knowledge_models import ExtractionResult
from services.document_store import DocumentStore

import tasks


def test_process_document_task_persists_to_postgres(tmp_path, db_session_factory, monkeypatch):
    monkeypatch.setattr(
        tasks.document_store_module,
        "document_store",
        DocumentStore(session_factory=db_session_factory),
    )

    file_path = tmp_path / "sample.txt"
    file_path.write_text("John Smith is the CEO of TechCorp Inc.", encoding="utf-8")

    result = tasks.process_document_task(str(file_path), "sample.txt", "txt")

    assert result["filename"] == "sample.txt"
    assert result["file_type"] == "txt"
    assert result["extraction_result"]["entity_count"] > 0
    assert result["document_id"]
    # get_extractor()'s output must satisfy the ExtractionResult contract that
    # document_store/knowledge_graph rely on, regardless of which extraction
    # strategy tasks.py is wired to.
    ExtractionResult.model_validate(result["extraction_result"])
    # Neo4j isn't running in tests - the graph write should fail softly rather
    # than blow up the whole task, same as the pre-Celery upload handler did.
    assert isinstance(result["storage_result"], dict)

    with db_session_factory() as session:
        assert session.query(Document).count() == 1
        assert session.query(EntityRecord).count() > 0
