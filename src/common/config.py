"""
Centralized configuration for the platform.
All services (MCP servers, agents, orchestrator) read settings from here.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider (Groq)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Environment
    environment: str = "local"
    log_level: str = "INFO"

    # GraphRAG (Neo4j) — used starting in the GraphRAG step
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""


settings = Settings()