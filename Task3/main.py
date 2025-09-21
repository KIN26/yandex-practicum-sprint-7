import shutil
from dataclasses import dataclass, field

import more_itertools as mi
import typer
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from logger import logger
from settings import get_settings, AppSettings


@dataclass(slots=True)
class SearchDB:
    settings: AppSettings = field(default_factory=get_settings)

    def init(self, chunk_size) -> None:
        logger.info("Start initialize database and index")

        model = self.load_model()
        total = []
        chunks_meta = []

        logger.info("Start preparing chunks")
        for file in self.settings.knowledge_base_source_folder_path.rglob("*.txt"):
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            title = file.stem.replace("_", " ")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=50,
                length_function=len,
                separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " "],
                add_start_index=True,
            )
            chunks = text_splitter.create_documents([content])

            if not chunks:
                logger.error("Не могу разбить файл на чанки")

            for chunk_id, chunk in enumerate(chunks, start=1):
                enhanced = f"Заголовок: {title}\n\n{chunk.page_content}"
                total.append(enhanced)
                chunks_meta.append(
                    {
                        "source": str(file),
                        "title": title,
                        "chunk_id": chunk_id,
                        "start_index": chunk.metadata.get('start_index', 1),
                        "content_length": len(chunk.page_content),
                    }
                )

        logger.info("Generate embeddings")
        chunk_embeddings = model.encode(
            total,
            show_progress_bar=False,
            batch_size=16,
            convert_to_numpy=True,
            normalize_embeddings=True,
            device="cpu",
        )

        if self.settings.index_folder_path.exists():
            shutil.rmtree(self.settings.index_folder_path)

        logger.info("Create vector index")
        chromadb_client = chromadb.PersistentClient(path=self.settings.index_folder_path)
        collection = chromadb_client.get_or_create_collection(
            name=self.settings.database_collection_name,
            metadata={
                "hnsw:space": "cosine",
                "model": self.settings.model_name,
                "chunk_size": str(chunk_size),
                "embedding_dim": str(model.get_sentence_embedding_dimension())
            }
        )

        logger.info("Add data to the index")

        data = zip(
            mi.chunked([f'chunk_{i+1}' for i in range(len(total))], self.settings.batch_size),
            mi.chunked(chunk_embeddings.tolist(), self.settings.batch_size),
            mi.chunked(chunks_meta, self.settings.batch_size),
            mi.chunked(total, self.settings.batch_size),
        )

        for batch_data in data:
            ids, embeddings, meta, documents = batch_data
            collection.add(embeddings=embeddings, metadatas=meta, documents=documents, ids=ids)

        logger.info("Index initialized successfully.")

    def load_model(self) -> SentenceTransformer:
        logger.info("Start loading model...")
        model = SentenceTransformer(self.settings.model_name)
        logger.info("Model downloaded successfully...")
        return model

    def search(self, search_str: str) -> None:
        logger.info("Start searching: \"%s\"", search_str)
        model = self.load_model()
        chromadb_client = chromadb.PersistentClient(path=self.settings.index_folder_path)
        collection = chromadb_client.get_collection(name=self.settings.database_collection_name)

        query =  collection.query(
            query_embeddings=model.encode([search_str]).tolist(),
            n_results=5,
            include=["metadatas", "documents", "distances"],
        )

        result = {}
        if query.get("documents", [None])[0]:
            for item in zip(query["documents"][0], query["metadatas"][0], query["distances"][0]):
                doc, metadata, dis = item

                if metadata["source"] not in result:
                    result[metadata["source"]] = []

                result[metadata["source"]].append({"quality": 1 - dis, "snippet": doc[doc.find("\n\n") + 2:200]})

            for file_name, search_results in result.items():
                logger.info("==" * 20)
                logger.info("File: %s", file_name)
                for idx, data in enumerate(search_results, start=1):
                    logger.info("Result %s, Quality: %s", idx, data["quality"])
                    logger.info("Snippet: %s", data["snippet"])

app = typer.Typer()
search_db = SearchDB()


@app.command(name="init", help="Initialize the index")
def init(chunk_size: int = 384):
    search_db.init(chunk_size)

@app.command(name="search", help="Train the model")
def search(search_str: str) -> None:
    search_db.search(search_str)


if __name__ == "__main__":
    app()

