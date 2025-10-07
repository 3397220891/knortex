from typing import Dict, List, Optional
from pydantic import BaseModel

class Entity(BaseModel):
    name: str
    type: str  # Person, Organization, Location, etc.
    properties: Dict = {}
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Smith",
                "type": "Person", 
                "properties": {"confidence": 0.9}
            }
        }

class Relationship(BaseModel):
    from_entity: str
    to_entity: str  
    type: str  # WORKS_AT, LOCATED_IN, etc.
    properties: Dict = {}
    
    class Config:
        schema_extra = {
            "example": {
                "from_entity": "John Smith",
                "to_entity": "TechCorp Inc",
                "type": "WORKS_AT",
                "properties": {"confidence": 0.7}
            }
        }

class ExtractionResult(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]
    entity_count: int
    relationship_count: int
    extraction_summary: Dict

class DocumentProcessingResult(BaseModel):
    file_id: str
    filename: str
    content_length: int
    extraction_result: ExtractionResult
    status: str
    message: str