from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    index_folder_path: Path = "./index"
    knowledge_base_source_folder_path: Path = "./knowledge_base"
    database_collection_name: str = "knowledge_base"
    embed_model_name: str = "default"
    batch_size: int = 2000
    chunk_size: int = 256

    llm_model_name: str = "default"
    query_retrieve_count: int = 5
    template_folder: Path = "./templates"
    ollama_host: str = "localhost"
    ollama_port: int = 8080

    model_config = SettingsConfigDict(env_file=".env", frozen=True, extra="ignore")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()