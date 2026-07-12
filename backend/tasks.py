from typing import Dict

from celery_app import celery_app
from models.knowledge_models import ExtractionResult
from services import document_store as document_store_module
from services import knowledge_graph as knowledge_graph_module
from services.document_parser import DocumentParser
from services.information_extractor import get_extractor


@celery_app.task(name="process_document")
def process_document_task(file_path: str, filename: str, file_extension: str) -> Dict:
    """Parse a saved file, run extraction, and persist it to PostgreSQL + Neo4j.

    Runs in a Celery worker so the upload request can return immediately after
    the file is saved to disk, instead of blocking on parsing/NER/two DB writes.
    """
    if file_extension == "pdf":
        parsed_data = DocumentParser.parse_pdf(file_path)
    elif file_extension == "docx":
        parsed_data = DocumentParser.parse_docx(file_path)
    else:
        parsed_data = DocumentParser.parse_txt(file_path)

    extraction_result = get_extractor().process_text(parsed_data["content"])
    # Fail fast if the extractor's output ever drifts from the contract downstream
    # code relies on, regardless of which extraction strategy produced it.
    ExtractionResult.model_validate(extraction_result)

    # PostgreSQL is the source of truth: it assigns the entity/relation ids
    # that Neo4j then reuses to key its graph projection.
    pg_result = document_store_module.document_store.save_extraction(
        filename=filename,
        file_type=parsed_data["file_type"],
        saved_path=file_path,
        content=parsed_data["content"],
        status=parsed_data.get("status", "success"),
        extraction_result=extraction_result,
    )

    try:
        storage_result = knowledge_graph_module.kg_service.store_extraction_result(
            extraction_result, pg_result["entity_ids"]
        )
    except Exception as e:
        storage_result = {"error": str(e)}

    return {
        "document_id": pg_result["document_id"],
        "filename": filename,
        "saved_path": file_path,
        "content_length": len(parsed_data["content"]),
        "file_type": parsed_data["file_type"],
        "status": parsed_data.get("status", "success"),
        "extraction_result": extraction_result,
        "storage_result": storage_result,
        "message": "File uploaded and parsed successfully",
    }
