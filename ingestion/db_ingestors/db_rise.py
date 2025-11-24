import pandas as pd
from sqlalchemy import create_engine
from app.config import IngestionConfig
from app.utils.vector_stores import VS_REGISTRY
from app.utils.docs import save_docs
from datetime import datetime, timezone
from langchain_core.documents import Document
from dotenv import load_dotenv
import os
from app.utils.paths import BASE_DIR, ART_DIR, DOC_DIR
from pathlib import Path


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DB_NAME = "rise.db"
RISE_DB_PATH = f"sqlite:///{BASE_DIR}/data/sql/{DB_NAME}"


class RiseDBIngestor:

    def __init__(self, config: IngestionConfig):
        self.config = config

    def ingest(self):
        """
        Create and store a vector store index for the PDF file_path, along with
        the corresponding Documents and a manifest.
        """

        VS_DIR = ART_DIR / self.config.vector_store.type

        engine = create_engine(RISE_DB_PATH)
        query = """
        SELECT FoodCat3Name, GHGTotalValue, RegionName, ProductionTypeEng
        FROM rise_co2
        """
        df = pd.read_sql_query(query, engine)
        docs = []

        for i, row in df.iterrows():
            text = (
                f"Foods or ingredients of type {row['FoodCat3Name']}, "
                f"when sourced from {row['RegionName']} "
                f"and produced with {row['ProductionTypeEng']} methods, "
                f"produce approximately {row['GHGTotalValue'].replace(',', '.')} kg of CO2 per kg."
            )
            metadata = {
                "doc_id": f"db:{DB_NAME}",
                "chunk_id": f"db:{DB_NAME}::chunk-{i}",
                "chunk_index": i,
                "source": DB_NAME,
                "filetype": "sql",
                "filename": DB_NAME,
                "language": "en",
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "tenant_id": "default",
                "pipeline_version": self.config.pipeline_version,
                "tags": [],
                "doc_title": Path(DB_NAME).stem,
            }
            doc = Document(page_content=text, metadata=metadata)
            docs.append(doc)

        art_dest_dir = f"{VS_DIR}/{DB_NAME.split('.')[0]}"
        doc_dest_dir = f"{DOC_DIR}/{DB_NAME.split('.')[0]}"

        manifest = {
            "vector_store": self.config.vector_store.type,
            "embedding_model": self.config.vector_store.embedding_model,
            "loader_name": self.config.sql.loader.type,
            "source_file": DB_NAME,
            "last_indexed": datetime.now(timezone.utc).isoformat(),
        }

        save_docs(
            docs,
            manifest,
            self.config.vector_store,
            doc_save_dir=doc_dest_dir,
            manifest_save_dir=art_dest_dir,
        )

        vs_builder = VS_REGISTRY[self.config.vector_store.type]["create"]
        vs_builder(docs, self.config.vector_store, save_dir=art_dest_dir)

        print(
            f"[{DB_NAME}_ingestor] Saved {self.config.vector_store.type} vector store to {VS_DIR}"
        )
