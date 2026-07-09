from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel):
    name: str
    type: str  # Person, Organization, Location, etc.
    properties: Dict[str, Any] = {}


class Relationship(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_entity: str = Field(alias="from")
    to_entity: str = Field(alias="to")
    type: str  # WORKS_AT, LOCATED_IN, etc.
    properties: Dict[str, Any] = {}


class ExtractionResult(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]
    entity_count: int
    relationship_count: int
    extraction_summary: Dict[str, int]


class TaskResult(BaseModel):
    document_id: str
    filename: str
    saved_path: str
    content_length: int
    file_type: str
    status: str
    extraction_result: ExtractionResult
    storage_result: Optional[Dict[str, Any]] = None
    message: str


class UploadAcceptedResponse(BaseModel):
    task_id: str
    file_id: str
    filename: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # processing | completed | failed
    result: Optional[TaskResult] = None
    error: Optional[str] = None


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: str
    content_length: int
    created_at: datetime
    entity_count: int
    relationship_count: int


class EvidenceItem(BaseModel):
    matched_text: str
    document_filename: str


class RelationEvidence(BaseModel):
    relation_id: str
    type: str
    from_entity: Optional[str] = None
    to_entity: Optional[str] = None
    confidence: float
    evidence: List[EvidenceItem]


class DocumentRef(BaseModel):
    document_id: str
    filename: str


class EntityEvidenceResponse(BaseModel):
    entity_id: str
    name: str
    type: str
    confidence: float
    properties: Dict[str, Any]
    document: DocumentRef
    relations: List[RelationEvidence]
