from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints.documents import router as documents_router
from api.endpoints.tasks import router as tasks_router
from api.endpoints.upload import router as upload_router
from config import settings
from db.base import Base, engine
from db import models  # noqa: F401  (registers ORM models on Base before create_all)
from services.knowledge_graph import kg_service

app = FastAPI(title="Knortex - Document Intelligence Knowledge Graph Platform")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(documents_router)
app.include_router(tasks_router)


@app.get("/")
def read_root():
    return {"message": "Knortex API is running successfully!"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "Neo4j"}


@app.get("/search")
async def search_entities(q: str = ""):
    """Search entities in knowledge graph"""
    if not q:
        return {"results": []}

    try:
        results = kg_service.search_entities(q)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}


@app.get("/graph")
async def get_graph_data(limit: int = 100):
    """Get graph data for visualization"""
    try:
        return kg_service.get_graph_data(limit)
    except Exception as e:
        return {"nodes": [], "links": [], "error": str(e)}


@app.get("/entities")
async def get_entities(limit: int = 50):
    """Get all entities"""
    try:
        results = kg_service.search_entities("", limit)
        return {"entities": results}
    except Exception as e:
        return {"entities": [], "error": str(e)}


@app.post("/mcp/tools/{tool_name}")
async def mcp_tool_call(tool_name: str, arguments: dict):
    """Call MCP tools"""
    try:
        if tool_name == "search_entities":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 50)
            results = kg_service.search_entities(query, limit)
            return {"result": results}
        elif tool_name == "get_graph_visualization":
            limit = arguments.get("limit", 100)
            graph_data = kg_service.get_graph_data(limit)
            return {"result": graph_data}
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
