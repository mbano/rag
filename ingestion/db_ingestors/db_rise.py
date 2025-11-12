from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from app.config import IngestionConfig, load_ingestion_config
from app.utils.vector_stores import VS_REGISTRY
from app.utils.docs import save_docs
from datetime import datetime, timezone
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
import json
import os


load_dotenv()

DB_NAME = "rise.db"  #  must match the name of the .db file

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parents[2]
ART_DIR = BASE_DIR / "artifacts"
cfg = load_ingestion_config()
VS_DIR = ART_DIR / cfg.vector_store.type
RISE_DB_PATH = f"sqlite:///{BASE_DIR}/data/sql/{DB_NAME}"
DOC_DIR = ART_DIR / "documents"


def ingest(config: IngestionConfig):
    """
    Create and store a vector store index for the PDF file_path, along with
    the corresponding Documents and a manifest.
    """

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
        metadata = {"type": "SQL", "filename": DB_NAME, "row": i}
        doc = Document(page_content=text, metadata=metadata)
        docs.append(doc)

    art_dest_dir = f"{VS_DIR}/{DB_NAME.split('.')[0]}"
    doc_dest_dir = f"{DOC_DIR}/{DB_NAME.split('.')[0]}"

    save_docs(docs, doc_dest_dir)

    manifest = {
        "vector_store": config.vector_store.type,
        "embedding_model": config.vector_store.embedding_model,
        "loader_name": config.sql.loader.type,
        "source_file": DB_NAME,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }

    embeddings = OpenAIEmbeddings(model=config.vector_store.embedding_model)
    vs_builder = VS_REGISTRY[config.vector_store.type]["create"]
    vs_builder(docs, embeddings, art_dest_dir)

    with open(f"{art_dest_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        print(
            f"[{DB_NAME}_ingestor] Saved {config.vector_store.type} vector store to {VS_DIR}"
        )
