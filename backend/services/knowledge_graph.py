from neo4j import GraphDatabase
from config import settings
from typing import List, Dict

class KnowledgeGraphService:
    """
    Service for storing and querying the graph projection in Neo4j.

    PostgreSQL (see services/document_store.py) is the source of truth for
    documents, chunks and extraction results. Neo4j only stores the minimal
    fields needed for relationship traversal, keyed by the same entity ids
    PostgreSQL already assigned - it never duplicates document content.
    """

    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            # Fail fast if Neo4j is unreachable instead of blocking the caller
            # (an upload request, or now a Celery worker) for the ~60s default.
            connection_timeout=5,
            connection_acquisition_timeout=5,
            max_transaction_retry_time=5,
        )

    def close(self):
        self.driver.close()

    def create_entity(self, entity: Dict, entity_id: str) -> str:
        """Create an entity node in Neo4j, keyed by its PostgreSQL entity id"""
        with self.driver.session() as session:
            result = session.execute_write(
                self._create_entity_node,
                entity,
                entity_id
            )
            return result

    def _create_entity_node(self, tx, entity: Dict, entity_id: str):
        """Internal method to create entity node"""
        query = """
        MERGE (e:Entity {name: $name, type: $type})
        SET e += $properties,
            e.id = $id,
            e.created_at = timestamp()
        RETURN e.id
        """

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
    
    def store_extraction_result(self, extraction_result: Dict, entity_ids: Dict[str, str]):
        """Project an extraction result into Neo4j.

        entity_ids maps entity name -> PostgreSQL entities.id, as returned by
        DocumentStore.save_extraction. Entities without a PG id (e.g. virtual
        entities that were never persisted) are skipped.
        """
        stored_ids = []

        for entity in extraction_result["entities"]:
            pg_id = entity_ids.get(entity["name"])
            if not pg_id:
                continue
            self.create_entity(entity, pg_id)
            stored_ids.append(pg_id)

        for relationship in extraction_result["relationships"]:
            self.create_relationship(relationship)

        return {
            "stored_entities": len(stored_ids),
            "stored_relationships": len(extraction_result["relationships"]),
            "entity_ids": stored_ids
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