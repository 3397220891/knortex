from typing import Dict, List, Optional

from db.base import SessionLocal
from db.models import Document, EntityRecord, RelationRecord


class DocumentQuery:
    """Read-side queries against PostgreSQL: document listing and entity/relation provenance.

    This is the counterpart to DocumentStore (the write side) - it's what makes the
    evidence_spans data actually reachable instead of write-only.
    """

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def list_documents(self, limit: int = 50) -> List[Dict]:
        with self._session_factory() as session:
            documents = (
                session.query(Document)
                .order_by(Document.created_at.desc())
                .limit(limit)
                .all()
            )

            results = []
            for document in documents:
                latest_run = max(
                    document.extraction_runs, key=lambda r: r.created_at, default=None
                )
                results.append(
                    {
                        "document_id": document.id,
                        "filename": document.filename,
                        "file_type": document.file_type,
                        "status": document.status,
                        "content_length": document.content_length,
                        "created_at": document.created_at,
                        "entity_count": latest_run.entity_count if latest_run else 0,
                        "relationship_count": latest_run.relationship_count if latest_run else 0,
                    }
                )
            return results

    def get_entity_evidence(self, entity_id: str) -> Optional[Dict]:
        with self._session_factory() as session:
            entity = session.get(EntityRecord, entity_id)
            if entity is None:
                return None

            document = entity.extraction_run.document

            relations = (
                session.query(RelationRecord)
                .filter(
                    (RelationRecord.from_entity_id == entity_id)
                    | (RelationRecord.to_entity_id == entity_id)
                )
                .all()
            )

            relation_payloads = []
            for relation in relations:
                from_entity = session.get(EntityRecord, relation.from_entity_id)
                to_entity = session.get(EntityRecord, relation.to_entity_id)
                evidence = [
                    {
                        "matched_text": span.matched_text,
                        "document_filename": span.chunk.document.filename,
                    }
                    for span in relation.evidence_spans
                ]
                relation_payloads.append(
                    {
                        "relation_id": relation.id,
                        "type": relation.type,
                        "from_entity": from_entity.name if from_entity else None,
                        "to_entity": to_entity.name if to_entity else None,
                        "confidence": relation.confidence,
                        "evidence": evidence,
                    }
                )

            return {
                "entity_id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "confidence": entity.confidence,
                "properties": entity.properties,
                "document": {
                    "document_id": document.id,
                    "filename": document.filename,
                },
                "relations": relation_payloads,
            }


document_query = DocumentQuery()
