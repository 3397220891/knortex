from services.document_query import DocumentQuery
from services.document_store import DocumentStore
from services.information_extractor import InformationExtractor

SAMPLE_TEXT = "John Smith is the CEO of TechCorp Inc."


def _seed(db_session_factory, text=SAMPLE_TEXT, filename="test.txt"):
    store = DocumentStore(session_factory=db_session_factory)
    extraction_result = InformationExtractor.process_text(text)
    return store.save_extraction(
        filename=filename,
        file_type="txt",
        saved_path=f"uploads/{filename}",
        content=text,
        status="success",
        extraction_result=extraction_result,
    )


def test_list_documents_returns_latest_first_with_counts(db_session_factory):
    _seed(db_session_factory, filename="first.txt")
    _seed(db_session_factory, filename="second.txt")

    query = DocumentQuery(session_factory=db_session_factory)
    documents = query.list_documents()

    assert [d["filename"] for d in documents] == ["second.txt", "first.txt"]
    assert documents[0]["entity_count"] > 0


def test_get_entity_evidence_returns_none_for_unknown_id(db_session_factory):
    query = DocumentQuery(session_factory=db_session_factory)
    assert query.get_entity_evidence("does-not-exist") is None


def test_get_entity_evidence_includes_relation_and_source_text(db_session_factory):
    pg_result = _seed(db_session_factory)
    john_id = pg_result["entity_ids"]["John Smith"]

    query = DocumentQuery(session_factory=db_session_factory)
    evidence = query.get_entity_evidence(john_id)

    assert evidence["name"] == "John Smith"
    assert evidence["document"]["filename"] == "test.txt"
    assert len(evidence["relations"]) == 1

    relation = evidence["relations"][0]
    assert relation["type"] == "CEO_OF"
    assert relation["from_entity"] == "John Smith"
    assert relation["to_entity"] == "TechCorp Inc"
    assert "CEO" in relation["evidence"][0]["matched_text"]
    assert relation["evidence"][0]["document_filename"] == "test.txt"
