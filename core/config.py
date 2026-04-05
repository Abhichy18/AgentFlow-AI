from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    openrouter_fallback_models: str = (
        "mistralai/mistral-7b-instruct:free,google/gemma-2-9b-it:free"
    )
    openrouter_retries_per_model: int = 2
    openrouter_retry_backoff_seconds: float = 1.5
    app_env: str = "dev"
    database_url: str = "sqlite:///./agentflow.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
