import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import relationship

from db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    """Source of truth for an uploaded document. Neo4j never stores this content."""

    __tablename__ = "documents"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    saved_path = Column(String, nullable=False)
    content_length = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="success")
    created_at = Column(DateTime(timezone=True), default=_now)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    extraction_runs = relationship("ExtractionRun", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """A slice of a document's text. One row per document for now (no chunking yet)."""

    __tablename__ = "document_chunks"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=_uuid)
    document_id = Column(Uuid(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    document = relationship("Document", back_populates="chunks")
    evidence_spans = relationship("EvidenceSpan", back_populates="chunk", cascade="all, delete-orphan")


class ExtractionRun(Base):
    """One execution of the extraction pipeline over a document."""

    __tablename__ = "extraction_runs"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=_uuid)
    document_id = Column(Uuid(as_uuid=False), ForeignKey("documents.id"), nullable=False)
    extractor_version = Column(String, nullable=False, default="spacy-en_core_web_sm-v1")
    entity_count = Column(Integer, nullable=False, default=0)
    relationship_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=_now)

    document = relationship("Document", back_populates="extraction_runs")
    entities = relationship("EntityRecord", back_populates="extraction_run", cascade="all, delete-orphan")
    relations = relationship("RelationRecord", back_populates="extraction_run", cascade="all, delete-orphan")


class EntityRecord(Base):
    """Canonical entity row. The id here is reused as the Neo4j node id."""

    __tablename__ = "entities"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=_uuid)
    extraction_run_id = Column(Uuid(as_uuid=False), ForeignKey("extraction_runs.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    properties = Column(JSON, nullable=False, default=dict)

    extraction_run = relationship("ExtractionRun", back_populates="entities")
    evidence_spans = relationship("EvidenceSpan", back_populates="entity", cascade="all, delete-orphan")


class RelationRecord(Base):
    """Canonical relation row. The id here is reused as the Neo4j relationship id."""

    __tablename__ = "relations"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=_uuid)
    extraction_run_id = Column(Uuid(as_uuid=False), ForeignKey("extraction_runs.id"), nullable=False)
    from_entity_id = Column(Uuid(as_uuid=False), ForeignKey("entities.id"), nullable=False)
    to_entity_id = Column(Uuid(as_uuid=False), ForeignKey("entities.id"), nullable=False)
    type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    properties = Column(JSON, nullable=False, default=dict)

    extraction_run = relationship("ExtractionRun", back_populates="relations")
    evidence_spans = relationship("EvidenceSpan", back_populates="relation", cascade="all, delete-orphan")


class EvidenceSpan(Base):
    """Links an entity or relation back to the chunk (and eventually text offsets) it came from."""

    __tablename__ = "evidence_spans"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=_uuid)
    chunk_id = Column(Uuid(as_uuid=False), ForeignKey("document_chunks.id"), nullable=False)
    entity_id = Column(Uuid(as_uuid=False), ForeignKey("entities.id"), nullable=True)
    relation_id = Column(Uuid(as_uuid=False), ForeignKey("relations.id"), nullable=True)
    matched_text = Column(String, nullable=False)

    chunk = relationship("DocumentChunk", back_populates="evidence_spans")
    entity = relationship("EntityRecord", back_populates="evidence_spans")
    relation = relationship("RelationRecord", back_populates="evidence_spans")
