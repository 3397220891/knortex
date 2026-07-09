from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    POSTGRES_URL: str = "postgresql+psycopg2://knortex:knortex@localhost:5432/knortex"

    REDIS_URL: str = "redis://localhost:6379/0"

    UPLOAD_DIR: str = "uploads"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
