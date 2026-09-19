from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuGauge"
    DATABASE_URL: str = "postgresql+asyncpg://app_user:app_secret@localhost:5432/docugauge_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM & Embedding settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_MODEL_NAME: str = "nomic-embed-text"
    LLM_MODEL_NAME: str = "llama3.2"
    EMBEDDING_DIM: int = 768

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
