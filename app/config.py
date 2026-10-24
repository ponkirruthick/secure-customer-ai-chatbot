from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/customer_chatbot"
    jwt_secret: str = "CHANGE_THIS"
    access_token_minutes: int = 60
    otp_ttl_seconds: int = 300
    otp_resend_seconds: int = 60
    otp_max_attempts: int = 5
    dev_otp_delivery: bool = True
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "customer_records"
    ollama_url: str = "http://localhost:11434"
    ollama_chat_model: str = "mistral"
    ollama_embed_model: str = "nomic-embed-text"
    llm_timeout_seconds: int = 45
    history_limit: int = 12
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
if settings.app_env.lower() != "development" and settings.dev_otp_delivery:
    raise RuntimeError("Development OTP delivery must be disabled outside development")
