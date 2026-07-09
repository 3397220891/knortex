from typing import List

from fastapi import APIRouter, Depends, HTTPException

from models.knowledge_models import DocumentSummary, EntityEvidenceResponse
from services.document_query import DocumentQuery, document_query

router = APIRouter()


def get_document_query() -> DocumentQuery:
    return document_query


@router.get("/documents", response_model=List[DocumentSummary])
def list_documents(limit: int = 50, query: DocumentQuery = Depends(get_document_query)):
    """List uploaded documents (PostgreSQL, source of truth) newest first."""
    return query.list_documents(limit=limit)


@router.get("/entities/{entity_id}/evidence", response_model=EntityEvidenceResponse)
def get_entity_evidence(entity_id: str, query: DocumentQuery = Depends(get_document_query)):
    """Trace an entity back to the relations and source text it came from."""
    evidence = query.get_entity_evidence(entity_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return evidence
