import re
import uuid
from typing import Dict, List

import spacy

_NLP = None

# spaCy's GPE (countries/cities/states) and LOC (other locations, e.g. mountain
# ranges) both map onto our single "Location" entity type.
_LABEL_TO_TYPE = {
    "PERSON": "Person",
    "ORG": "Organization",
    "GPE": "Location",
    "LOC": "Location",
}

# Consecutive Capitalized words, e.g. "TechCorp", "TechCorp Inc", "New York" - a
# lightweight proper-noun heuristic. Unlike a hardcoded corporate-suffix
# alternation (" Corp| Inc| Company| Ltd"), it doesn't require a suffix to be
# present, and unlike an unanchored `[\w\s]+`, it stays bounded to capitalized
# words so it can't run on past the end of a sentence. Wrapped in a scoped
# `(?-i:...)` so it stays case-sensitive even though extract_relationships runs
# every pattern with re.IGNORECASE (needed for the surrounding literal phrases).
_PROPER_NOUN = r"(?-i:[A-Z][\w'-]*(?:\s[A-Z][\w'-]*)*)"

# (pattern, relationship type, source entity type, target entity type)
_RELATIONSHIP_PATTERNS = [
    # CEO of Organization
    (r'(\w+ \w+) is the CEO of (' + _PROPER_NOUN + r')',
    "CEO_OF", "Person", "Organization"),

    # works as at Organization
    (r'(\w+ \w+) works as (?:a|an)? ([^,.]+) at (' + _PROPER_NOUN + r')',
    "WORKS_AT", "Person", "Organization"),

    # headquartered in Location
    (r'(' + _PROPER_NOUN + r') is headquartered in (' + _PROPER_NOUN + r')',
    "HEADQUARTERED_IN", "Organization", "Location"),

    # has office in Location
    (r'(' + _PROPER_NOUN + r') has (?:a|an)? ([^,.]+) office in (' + _PROPER_NOUN + r')',
    "HAS_OFFICE_IN", "Organization", "Location"),

    # works with Person
    (r'(\w+ \w+) works (?:closely )?with (\w+ \w+)',
    "COLLABORATES_WITH", "Person", "Person"),

    # serves as Role
    (r'(\w+ \w+) serves as (?:the )?(\w+)',
    "HAS_POSITION", "Person", "Position")
]


def _get_nlp():
    """Lazily load the spaCy model once per process - loading it is the
    expensive part (tens of ms), running it on a doc is cheap."""
    global _NLP
    if _NLP is None:
        _NLP = spacy.load("en_core_web_sm")
    return _NLP


class InformationExtractor:
    """
    Entity extraction via spaCy NER (en_core_web_sm); relationship extraction
    via context-aware regex patterns matched against the recognized entities.
    """

    @staticmethod
    def extract_entities(text: str) -> List[Dict]:
        """Extract Person/Organization/Location entities using spaCy NER"""
        doc = _get_nlp()(text)
        entities = []
        seen_entities = set()

        for ent in doc.ents:
            entity_type = _LABEL_TO_TYPE.get(ent.label_)
            if entity_type is None:
                continue

            # spaCy sometimes includes trailing punctuation in the span
            # (e.g. "TechCorp Inc." at the end of a sentence).
            name = ent.text.strip().rstrip(".")
            if not name or name in seen_entities:
                continue

            entities.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "type": entity_type,
                "properties": {
                    "source": "spacy_ner",
                    "confidence": 0.85
                }
            })
            seen_entities.add(name)

        return entities
    
    @staticmethod
    def extract_relationships(text: str, entities: List[Dict]) -> List[Dict]:
        """Extract relationships with context-aware patterns"""
        relationships = []

        # Create entity mapping
        entity_map = {entity["name"]: entity for entity in entities}

        for pattern, rel_type, source_type, target_type in _RELATIONSHIP_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                source_name = match.group(1)
            
                # Determine target entity based on group count
                if len(match.groups()) >= 3:
                    target_name = match.group(3)  # Third group is target entity
                elif len(match.groups()) >= 2:
                    target_name = match.group(2)  # Second group is target entity
                else:
                    continue
            
                # Verify entity exists
                source_entity = entity_map.get(source_name)
                target_entity = entity_map.get(target_name)
            
                # If target entity does not exist but type is Position, create virtual entity
                if not target_entity and target_type == "Position":
                    target_entity = {"name": target_name, "type": "Position"}
            
                if source_entity and target_entity:
                    # Check type matching (allow Position type)
                    if (source_entity["type"] == source_type and 
                        (target_entity["type"] == target_type or target_type == "Position")):
                    
                        relationships.append({
                            "id": str(uuid.uuid4()),
                            "from": source_name,
                            "to": target_name,
                            "from_id": source_entity.get("id"),
                            "to_id": target_entity.get("id"),
                            "type": rel_type,
                            "properties": {
                                "source": "pattern_match",
                                "confidence": 0.7,
                                "context": match.group(0)
                            }
                        })
    
        return relationships
    
    @staticmethod
    def process_text(text: str) -> Dict:
        """Main method to process text and extract knowledge"""
        print("Extracting information from text...")
        
        entities = InformationExtractor.extract_entities(text)
        relationships = InformationExtractor.extract_relationships(text, entities)
        
        print(f"Extraction completed: {len(entities)} entities, {len(relationships)} relationships")
        
        return {
            "entities": entities,
            "relationships": relationships,
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "extraction_summary": {
                "person_count": len([e for e in entities if e["type"] == "Person"]),
                "organization_count": len([e for e in entities if e["type"] == "Organization"]),
                "location_count": len([e for e in entities if e["type"] == "Location"])
            }
        }


def get_extractor():
    """Single seam for selecting which extraction strategy runs.

    Currently always the regex/spaCy-based InformationExtractor; a future
    trigger-word or LLM-based extractor can be swapped in here (e.g. behind a
    config flag) without touching callers.
    """
    return InformationExtractor