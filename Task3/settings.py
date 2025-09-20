from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    index_folder_path: Path = "./index"
    knowledge_base_source_folder_path: Path = "./knowledge_base"
    database_collection_name: str = "knowledge_base"
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 3500

    model_config = SettingsConfigDict(env_file=".env", frozen=True, extra="ignore")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()