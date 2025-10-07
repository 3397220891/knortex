import os
from typing import Optional

class Settings:
    # Tasks:
    # - Read environment variables with os.getenv()
    # - Add default values for development
    # - Ensure essential configuration exists
    
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Additional configurations:
    # - UPLOAD_DIR: str (file upload path)
    # - OPENAI_API_KEY: Optional[str] (for future AI functionality)
    # - DEBUG: bool (development mode)

settings = Settings()