from neo4j import GraphDatabase
from config import settings
from typing import List, Dict
import uuid

class KnowledgeGraphService:
    """
    Service for storing and querying knowledge in Neo4j
    """
    
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def create_entity(self, entity: Dict) -> str:
        """Create an entity node in Neo4j"""
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_entity_node, 
                entity
            )
            return result
    
    def _create_entity_node(self, tx, entity: Dict):
        """Internal method to create entity node"""
        query = """
        MERGE (e:Entity {name: $name, type: $type})
        SET e += $properties,
            e.id = $id,
            e.created_at = timestamp()
        RETURN e.id
        """
        
        entity_id = str(uuid.uuid4())
        result = tx.run(
            query,
            name=entity["name"],
            type=entity["type"],
            properties=entity.get("properties", {}),
            id=entity_id
        )
        
        return result.single()[0]
    
    def create_relationship(self, relationship: Dict):
        """Create a relationship between entities"""
        try:
            with self.driver.session() as session:
                result = session.execute_write(
                    self._create_relationship_edge,
                    relationship
                )
                return result
        except Exception as e:
            print(f"ERROR creating relationship: {e}")
            print(f"Relationship data: {relationship}")
            return None

    def _create_relationship_edge(self, tx, relationship: Dict):
        """Internal method to create relationship with error handling"""
        try:
            query = """
            MATCH (a:Entity {name: $from_name}), (b:Entity {name: $to_name})
            MERGE (a)-[r:RELATIONSHIP {type: $rel_type}]->(b)
            SET r += $properties,
                r.id = $rel_id,
                r.created_at = timestamp()
            RETURN r.id
            """
        
            rel_id = str(uuid.uuid4())
            result = tx.run(
                query,
                from_name=relationship["from"],
                to_name=relationship["to"], 
                rel_type=relationship["type"],
                properties=relationship.get("properties", {}),
                rel_id=rel_id
            )
        
            record = result.single()
            return record[0] if record else None
        
        except Exception as e:
            print(f"Error in relationship transaction: {e}")
            return None
    
    def store_extraction_result(self, extraction_result: Dict):
        """Store complete extraction result in Neo4j"""
        entity_ids = []
        
        # Store entities
        for entity in extraction_result["entities"]:
            entity_id = self.create_entity(entity)
            entity_ids.append(entity_id)
        
        # Store relationships
        for relationship in extraction_result["relationships"]:
            self.create_relationship(relationship)
        
        return {
            "stored_entities": len(extraction_result["entities"]),
            "stored_relationships": len(extraction_result["relationships"]),
            "entity_ids": entity_ids
        }
    
    def search_entities(self, keyword: str, limit: int = 50) -> List[Dict]:
        """Search entities by keyword"""
        with self.driver.session() as session:
            result = session.execute_read(
                self._search_entities_query,
                keyword, limit
            )
            return result
    
    def _search_entities_query(self, tx, keyword: str, limit: int):
        query = """
        MATCH (e:Entity)
        WHERE e.name CONTAINS $keyword OR e.type CONTAINS $keyword
        RETURN e.name as name, e.type as type, e.id as id
        LIMIT $limit
        """
        
        result = tx.run(query, keyword=keyword, limit=limit)
        return [dict(record) for record in result]
    
    def get_graph_data(self, limit: int = 100) -> Dict:
        """Get graph data for visualization"""
        with self.driver.session() as session:
            nodes = session.execute_read(self._get_nodes_query, limit)
            links = session.execute_read(self._get_relationships_query, limit)
            
            return {
                "nodes": nodes,
                "links": links
            }
    
    def _get_nodes_query(self, tx, limit: int):
        query = """
        MATCH (e:Entity)
        RETURN e.id as id, e.name as name, e.type as type
        LIMIT $limit
        """
        result = tx.run(query, limit=limit)
        return [dict(record) for record in result]
    
    def _get_relationships_query(self, tx, limit: int):
        query = """
        MATCH (a:Entity)-[r:RELATIONSHIP]->(b:Entity)
        RETURN a.id as source, b.id as target, r.type as type
        LIMIT $limit
        """
        result = tx.run(query, limit=limit)
        return [dict(record) for record in result]

# Global instance
kg_service = KnowledgeGraphService()