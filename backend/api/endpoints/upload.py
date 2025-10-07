from fastapi import UploadFile, File, HTTPException
import os
import uuid
from services.document_parser import DocumentParser
from services.information_extractor import InformationExtractor
from services.knowledge_graph import kg_service

async def handle_file_upload(file: UploadFile):
    """
    Handle file upload and processing
    """
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
        
        # Use absolute path within backend directory
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, saved_filename)
        
        print(f"DEBUG: Saving to {file_path}")
        
        # Save uploaded file
        file_content = await file.read()
        print(f"DEBUG: Read {len(file_content)} bytes from upload")
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        print(f"DEBUG: File saved successfully")
        print(f"DEBUG: File exists: {os.path.exists(file_path)}")
        print(f"DEBUG: File size: {os.path.getsize(file_path)} bytes")
        
        # Test file integrity before parsing
        print(f"DEBUG: Testing file integrity...")
        try:
            with open(file_path, 'rb') as f:
                file_header = f.read(10)
                print(f"DEBUG: File header: {file_header}")
        except Exception as e:
            print(f"DEBUG: File read test failed: {e}")
        
        # Parse document based on file type
        print(f"DEBUG: Starting document parsing...")
        if file.filename.endswith('.pdf'):
            parsed_data = DocumentParser.parse_pdf(file_path)
        elif file.filename.endswith('.docx'):
            parsed_data = DocumentParser.parse_docx(file_path)
        elif file.filename.endswith('.txt'):
            parsed_data = DocumentParser.parse_txt(file_path)
        else:
            parsed_data = DocumentParser.parse_docx(file_path)
        
        extraction_result = InformationExtractor.process_text(parsed_data["content"])
        print(f"DEBUG: Parsing completed successfully")
        storage_result = kg_service.store_extraction_result(extraction_result)

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
        print(f"DEBUG: Error occurred: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"File processing failed: {str(e)}"
        )