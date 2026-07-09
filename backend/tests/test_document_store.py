from db.models import Document, EntityRecord, EvidenceSpan, RelationRecord
from services.document_store import DocumentStore
from services.information_extractor import InformationExtractor

SAMPLE_TEXT = "John Smith is the CEO of TechCorp Inc."


def test_save_extraction_persists_document_entities_and_relations(db_session_factory):
    store = DocumentStore(session_factory=db_session_factory)
    extraction_result = InformationExtractor.process_text(SAMPLE_TEXT)

    result = store.save_extraction(
        filename="test.txt",
        file_type="txt",
        saved_path="uploads/test.txt",
        content=SAMPLE_TEXT,
        status="success",
        extraction_result=extraction_result,
    )

    assert result["document_id"]
    assert result["extraction_run_id"]
    assert set(result["entity_ids"]) == {e["name"] for e in extraction_result["entities"]}

    with db_session_factory() as session:
        assert session.query(Document).count() == 1
        assert session.query(EntityRecord).count() == len(extraction_result["entities"])
        assert session.query(RelationRecord).count() == len(extraction_result["relationships"])

        ceo_relation = session.query(RelationRecord).filter_by(type="CEO_OF").one()
        evidence = session.query(EvidenceSpan).filter_by(relation_id=ceo_relation.id).one()
        assert "CEO" in evidence.matched_text


def test_save_extraction_skips_relations_missing_an_entity_row(db_session_factory):
    """A relationship whose 'to' name has no matching row in entities (e.g. an
    extractor emitted a relation referencing an entity it didn't also report)
    must be skipped rather than fail the whole write."""
    store = DocumentStore(session_factory=db_session_factory)
    extraction_result = {
        "entities": [{"name": "Jane Doe", "type": "Person", "properties": {}}],
        "relationships": [
            {"from": "Jane Doe", "to": "CTO", "type": "HAS_POSITION", "properties": {}}
        ],
        "entity_count": 1,
        "relationship_count": 1,
        "extraction_summary": {"person_count": 1, "organization_count": 0, "location_count": 0},
    }

    store.save_extraction(
        filename="virtual.txt",
        file_type="txt",
        saved_path="uploads/virtual.txt",
        content="Jane Doe serves as CTO.",
        status="success",
        extraction_result=extraction_result,
    )

    with db_session_factory() as session:
        assert session.query(RelationRecord).count() == 0
