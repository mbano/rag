from pathlib import Path
from dotenv import load_dotenv
import json
import os
from app.config import settings, IngestionConfig
from app.utils.opensearch import get_opensearch_langchain_kwargs
from opensearchpy import OpenSearch
import boto3
from app.utils.vector_stores import VS_REGISTRY, VectorStoreType
from datetime import datetime, timezone
from app.utils.urls import url_to_resource_name
from ingestion.pdf_ingestor import ingest_pdf
from ingestion.web_ingestor import ingest_web
from app.utils.db_ingestors import get_db_ingestor
from app.utils.paths import ART_DIR, DATA_DIR

# local fallback
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


#  TODO:  update remote repo too


def _check_for_vs(file_name, config: IngestionConfig):

    if config.vector_store.type == VectorStoreType.FAISS:

        VS_DIR = ART_DIR / config.vector_store.type

        for vs_path in Path(VS_DIR).glob("*"):
            if vs_path.stem == file_name:
                index_faiss_path = vs_path / "index.faiss"
                index_pkl_path = vs_path / "index.pkl"
                manifest_path = vs_path / "manifest.json"
                return all(
                    p.exists()
                    for p in [index_faiss_path, index_pkl_path, manifest_path]
                )

    elif config.vector_store.type == VectorStoreType.OPENSEARCH:

        endpoint = os.environ["OPENSEARCH_COLLECTION_ENDPOINT"]
        client = OpenSearch(endpoint, **get_opensearch_langchain_kwargs())
        index_exists = client.indices.exists(
            index=config.vector_store.kwargs.get("index_name")
        )

        s3 = boto3.client("s3")

        if not index_exists:
            s3.delete_object(
                Bucket=os.environ["AWS_S3_DOCS_BUCKET"],
                Key="manifests/manifests.json",
            )
            return False

        try:
            resp = s3.get_object(
                Bucket=os.environ["AWS_S3_DOCS_BUCKET"],
                Key="manifests/manifests.json",
            )
        except s3.exceptions.NoSuchKey:
            return False

        data = resp["Body"].read().decode("utf-8")
        manifests = json.loads(data)
        if file_name in manifests:
            print(f"[update_vectorstores] {file_name} already indexed.")
            return True

    return False


def _merge_vector_stores(config: IngestionConfig):

    VS_DIR = ART_DIR / config.vector_store.type

    vector_stores = []
    file_names = []

    for vs_path in Path(VS_DIR).glob("*/"):
        with open(vs_path / "manifest.json", "r") as f:
            manifest = json.load(f)
        source = manifest.get("source_file")
        source = manifest.get("source_url") if not source else source
        vector_store_name = manifest.get("vector_store", config.vector_store.type)
        embedding_model = manifest.get(
            "embedding_model", config.vector_store.embedding_model
        )
        file_names.append(source)

        vs_builder = VS_REGISTRY[config.vector_store.type]["load"]
        vector_store = vs_builder(
            config.vector_store,
            path=vs_path,
            embedding_model=embedding_model,
        )
        vector_stores.append(vector_store)

    main_vs = vector_stores[0]
    for vs in vector_stores[1:]:
        main_vs.merge_from(vs)
    main_vs.save_local(VS_DIR)

    manifest = {
        "embedding_model": embedding_model,
        "vector_store": vector_store_name,
        "loader_name": config.pdf.loader.type,
        "loader_params": config.pdf.loader.params,
        "source_files": file_names,
        "last_indexed": datetime.now(timezone.utc).isoformat(),
    }
    with open(Path(VS_DIR) / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def update_vector_stores(config: IngestionConfig):

    added_vs = False
    data_subdirs = [path for path in Path(DATA_DIR).iterdir() if path.is_dir()]

    for dir in data_subdirs:
        if dir.stem == "pdf":
            for file_path in dir.iterdir():
                pdf_name = file_path.stem
                has_vs = _check_for_vs(pdf_name, config=config)
                if not has_vs:
                    ingest_pdf(file_path=file_path, config=config)
                    added_vs = True
        if dir.stem == "web":
            # get each url and transform to resource name
            with open(dir / "urls.json", "r") as f:
                urls = json.load(f)["urls"]
            resource_names = [url_to_resource_name(url) for url in urls]
            for url, resource_name in zip(urls, resource_names):
                has_vs = _check_for_vs(resource_name, config=config)
                if not has_vs:
                    ingest_web(url=url, config=config)
                    added_vs = True
        if dir.stem == "sql":
            for file_path in dir.iterdir():
                db_name = file_path.stem
                has_vs = _check_for_vs(db_name, config=config)
                if not has_vs:
                    db_ingestor = get_db_ingestor(db_name, config)
                    db_ingestor.ingest()
                    added_vs = True

    if added_vs and config.vector_store.type == VectorStoreType.FAISS:
        _merge_vector_stores(config)
        print("Merged existing vector stores.")
    else:
        print("No new documents to add.")


if __name__ == "__main__":
    update_vector_stores(settings.ingestion)
