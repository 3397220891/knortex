from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.document_parser import DocumentParser
from services.information_extractor import InformationExtractor
from services.knowledge_graph import kg_service
import os
import uuid
import asyncio

app = FastAPI(title="Knortex - Intelligent Knowledge Graph Platform")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Knortex API is running successfully!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "Neo4j"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and processing"""
    print(f"DEBUG: Starting file upload for {file.filename}")
    
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF, Word documents and text files are supported"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        saved_filename = f"{file_id}.{file_extension}"
        
        # Save file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, saved_filename)
        
        # Save uploaded file
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        print(f"DEBUG: File saved to {file_path}")
        
        # Parse document
        if file.filename.endswith('.pdf'):
            parsed_data = DocumentParser.parse_pdf(file_path)
        elif file.filename.endswith('.docx'):
            parsed_data = DocumentParser.parse_docx(file_path)
        else:  # txt
            parsed_data = DocumentParser.parse_txt(file_path)
        
        # Information extraction
        extraction_result = InformationExtractor.process_text(parsed_data["content"])
        
        # Store to Neo4j
        storage_result = None
        try:
            storage_result = kg_service.store_extraction_result(extraction_result)
        except Exception as e:
            print(f"WARNING: Failed to store in Neo4j: {e}")
            storage_result = {"error": str(e)}
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "saved_path": file_path,
            "content_length": len(parsed_data["content"]),
            "file_type": parsed_data["file_type"],
            "status": parsed_data.get("status", "success"),
            "extraction_result": extraction_result,
            "storage_result": storage_result,
            "message": "File uploaded and parsed successfully"
        }
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"File processing failed: {str(e)}"
        )

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
        graph_data = kg_service.get_graph_data(limit)
        return graph_data
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
        # This is a simplified version - in practice you'd use the actual MCP protocol
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
