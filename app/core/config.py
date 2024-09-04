from passlib.context import CryptContext

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    allow_credentials: bool = True
    allowed_methods: list[str] = ["*"]
    allowed_origins: list[str] = ["*"]
    app_name: str = "Health Planner API"
    app_version: str = "0.0.1"
    database_url: str = "sqlite:///./test.db"
    debug: bool = True
    jwt_algorithm: str = "HS256"
    jwt_expires_in_days: int = 7
    jwt_secret_key: str
    openai_key: str
    openai_max_tokens: int = 250
    openai_model: str
    openai_organization_id: str
    openai_project_id: str
    session_expire_days: int = 7
    session_same_site: str = "lax"
    session_secret_key: str
    session_secure: bool = False

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
