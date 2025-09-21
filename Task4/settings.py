from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    index_folder_path: Path = "./index"
    database_collection_name: str = "knowledge_base"
    embed_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    llm_model_name: str = "llama3"
    query_retrieve_count: int = 15
    query_include: list = ["documents"]
    template_folder: Path = "./templates"
    answer_template: str = "answer.txt"
    ollama_host: str = "http://localhost"
    ollama_port: int = 11434
    use_cot: bool = False

    model_config = SettingsConfigDict(env_file=".env", frozen=True, extra="ignore")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()