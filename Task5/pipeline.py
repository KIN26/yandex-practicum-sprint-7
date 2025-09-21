import requests
import re
from dataclasses import dataclass, field

from sentence_transformers import SentenceTransformer
from chromadb.api import ClientAPI
from chromadb import Collection, PersistentClient, QueryResult
from jinja2 import Environment, FileSystemLoader

from settings import AppSettings, get_settings
from exceptions import MaliciousException


@dataclass(slots=True)
class Pipeline:
    settings: AppSettings = field(default_factory=get_settings)
    embed_model: SentenceTransformer= field(init=False)
    db_client: ClientAPI = field(init=False)
    collection: Collection = field(init=False)
    template_env: Environment = field(init=False)

    def __post_init__(self):
        self.embed_model = SentenceTransformer(self.settings.embed_model_name)
        self.db_client = PersistentClient(path=self.settings.index_folder_path)
        self.collection = self.db_client.get_collection(self.settings.database_collection_name)
        self.template_env = Environment(loader=FileSystemLoader(self.settings.template_folder))

    def get_chunks(self, search_str: str) -> QueryResult:
        return self.collection.query(
            query_embeddings=self.embed_model.encode([search_str]).tolist(),
            n_results=self.settings.query_retrieve_count,
            include=["documents"],
        )

    def send_request_to_ollama(self, prompt: str):
        url = f"{self.settings.ollama_host}:{self.settings.ollama_port}/api/generate"
        payload = {"model": self.settings.llm_model_name, "stream": False, "prompt": prompt}
        response = requests.post(url, json=payload)
        return response.json().get("response")


    def make_prompt(self, question: str, database_context: str) -> str:
        template = self.template_env.get_template("prompt.txt")
        return template.render(question=question, database_context=database_context)

    def prepare_context(self, context: list[str]) -> str:
        ret = ""

        for chunk in context:
            title_pos = chunk.find("\n\n")
            title = chunk[:title_pos]
            body = chunk[title_pos:].strip("\n\n").strip(".").strip()
            ret += f"\n{title}\nТекст:{body}\n"

        return ret

    def find_malicious(self, chunks: list[str]):
        danger_patterns = [
            r'ignore all instructions',
            r'output\s*:',
            r'парол(ь|и|я|ём|ем|емы)',
            r'password\s*:',
            r'root\s*:',
            r'admin\s*:',
            r'you must',
            r'вы должны',
            r'sudo\s',
            r'run\s+this\s+command',
        ]

        for chunk in chunks:
            lowered = chunk.lower()
            for pattern in danger_patterns:
                if re.search(pattern, lowered):
                    raise MaliciousException

    def search(self) -> str:
        while True:
            try:
                query = input("Введите свой запрос: ").replace('\ufffd', '').strip()
                chunks = self.get_chunks(query)
                documents = chunks["documents"][0]
                self.find_malicious(documents)
                prompt = self.make_prompt(
                    question=query,
                    database_context=self.prepare_context(documents)
                )
                response = self.send_request_to_ollama(prompt)
                print(f"{response}")
            except MaliciousException:
                print("потенциально опасный ответ не выдаётся")
