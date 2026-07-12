from typing import Dict

from db.base import SessionLocal
from db.models import Document, DocumentChunk, EntityRecord, EvidenceSpan, ExtractionRun, RelationRecord


class DocumentStore:
    """PostgreSQL persistence layer: source of truth for documents, chunks and extraction results.

    Neo4j only stores a graph projection (nodes/edges) keyed by the ids handed out here.
    """

    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def save_extraction(
        self,
        *,
        filename: str,
        file_type: str,
        saved_path: str,
        content: str,
        status: str,
        extraction_result: Dict,
    ) -> Dict:
        with self._session_factory() as session:
            document = Document(
                filename=filename,
                file_type=file_type,
                saved_path=saved_path,
                content_length=len(content),
                status=status,
            )
            session.add(document)
            session.flush()

            chunk = DocumentChunk(document_id=document.id, chunk_index=0, content=content)
            session.add(chunk)
            session.flush()

            run = ExtractionRun(
                document_id=document.id,
                entity_count=extraction_result["entity_count"],
                relationship_count=extraction_result["relationship_count"],
            )
            session.add(run)
            session.flush()

            entity_id_by_name: Dict[str, str] = {}
            for entity in extraction_result["entities"]:
                record_kwargs = dict(
                    extraction_run_id=run.id,
                    name=entity["name"],
                    type=entity["type"],
                    confidence=entity.get("properties", {}).get("confidence", 0.0),
                    properties=entity.get("properties", {}),
                )
                # Reuse the id minted at extraction time (see information_extractor.py)
                # so the same id identifies this entity in both Postgres and Neo4j.
                if entity.get("id"):
                    record_kwargs["id"] = entity["id"]
                record = EntityRecord(**record_kwargs)
                session.add(record)
                session.flush()
                entity_id_by_name[entity["name"]] = record.id

            for rel in extraction_result["relationships"]:
                from_id = entity_id_by_name.get(rel["from"])
                to_id = entity_id_by_name.get(rel["to"])
                # Relationship targets that were only created as ad-hoc "virtual" entities
                # (e.g. a Position that isn't in the entities list) have no PG row yet and
                # are skipped here, matching the existing Neo4j MATCH-based write behavior.
                if not from_id or not to_id:
                    continue

                relation_kwargs = dict(
                    extraction_run_id=run.id,
                    from_entity_id=from_id,
                    to_entity_id=to_id,
                    type=rel["type"],
                    confidence=rel.get("properties", {}).get("confidence", 0.0),
                    properties=rel.get("properties", {}),
                )
                # Reuse the id minted at extraction time so the same id identifies
                # this relation in both Postgres and Neo4j.
                if rel.get("id"):
                    relation_kwargs["id"] = rel["id"]
                relation_record = RelationRecord(**relation_kwargs)
                session.add(relation_record)
                session.flush()

                context = rel.get("properties", {}).get("context")
                if context:
                    session.add(
                        EvidenceSpan(
                            chunk_id=chunk.id,
                            relation_id=relation_record.id,
                            matched_text=context,
                        )
                    )

            session.commit()

            return {
                "document_id": document.id,
                "extraction_run_id": run.id,
                "entity_ids": entity_id_by_name,
            }


document_store = DocumentStore()
