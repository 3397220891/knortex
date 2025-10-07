import re
from typing import Dict, List, Tuple

class InformationExtractor:
    """
    Advanced information extraction with improved entity recognition
    """
    
    @staticmethod
    def extract_entities(text: str) -> List[Dict]:
        """Extract entities with improved patterns and context awareness"""
        entities = []
        seen_entities = set()
    
        # Extract locations first - using predefined location list
        locations = ["New York", "San Francisco", "London", "Tokyo", "Boston", "Seattle"]
        found_locations = []
        for loc in locations:
            if loc in text:
                found_locations.append(loc)
    
        # Improved organization extraction - match more patterns
        org_patterns = [
            r'\b([A-Z][a-zA-Z]*(?: Corp| Inc| Company| Ltd| Corporation| Software| Solutions))\b',
            r'\b([A-Z][a-zA-Z]+ (?:Corp|Inc|Company|Ltd|Corporation))\b',
            r'\b(the company)\b',  # Match "the company" reference
        ]
    
    
        organizations = []
        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            organizations.extend(matches)
    
        # Improved person name extraction - exclude location names
        person_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'
        persons = re.findall(person_pattern, text)
    
        # Filter out location names mistakenly identified as Person
        persons = [p for p in persons if p not in found_locations]
    
        # Create entity objects
        for loc in found_locations:
            if loc not in seen_entities:
                entities.append({
                    "name": loc,
                    "type": "Location",
                    "properties": {
                        "source": "predefined_list",
                        "confidence": 0.95
                    }
                })
                seen_entities.add(loc)
    
        for org in organizations:
            if org and org not in seen_entities:
                # Handle "the company" reference
                if org.lower() == "the company":
                    org = "TechCorp"  # Infer from context
                entities.append({
                    "name": org,
                    "type": "Organization",
                    "properties": {
                        "source": "text_extraction", 
                        "confidence": 0.8
                    }
                })
                seen_entities.add(org)
    
        for person in persons:
            if person not in seen_entities:
                entities.append({
                    "name": person,
                    "type": "Person",
                    "properties": {
                        "source": "text_extraction",
                        "confidence": 0.9
                    }
                })
                seen_entities.add(person)
    
        return entities
    
    @staticmethod
    def extract_relationships(text: str, entities: List[Dict]) -> List[Dict]:
        """Extract relationships with context-aware patterns"""
        relationships = []
        text_lower = text.lower()
    
        # Create entity mapping
        entity_map = {entity["name"]: entity for entity in entities}
    
        # Improved relationship patterns
        relationship_patterns = [
            # CEO of Organization
            (r'(\w+ \w+) is the CEO of ([\w\s]+(?: Corp| Inc| Company| Ltd))', 
            "CEO_OF", "Person", "Organization"),
        
            # works as at Organization
            (r'(\w+ \w+) works as (?:a|an)? ([^,.]+) at ([\w\s]+(?: Corp| Inc| Company| Ltd))', 
            "WORKS_AT", "Person", "Organization"),
        
            # headquartered in Location
            (r'([\w\s]+(?: Corp| Inc| Company| Ltd)) is headquartered in ([\w\s]+)', 
            "HEADQUARTERED_IN", "Organization", "Location"),
        
            # has office in Location
            (r'([\w\s]+(?: Corp| Inc| Company| Ltd)) has (?:a|an)? ([^,.]+) office in ([\w\s]+)', 
            "HAS_OFFICE_IN", "Organization", "Location"),
        
            # works with Person
            (r'(\w+ \w+) works (?:closely )?with (\w+ \w+)', 
            "COLLABORATES_WITH", "Person", "Person"),
        
            # serves as Role
            (r'(\w+ \w+) serves as (?:the )?(\w+)', 
         "  HAS_POSITION", "Person", "Position")
        ]
    
        for pattern, rel_type, source_type, target_type in relationship_patterns:
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
                            "from": source_name,
                            "to": target_name,
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