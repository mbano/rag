from app.config import IngestionConfig
from ingestion.db_ingestors.db_rise import RiseDBIngestor
from typing import Any


DB_INGESTOR_REGISTRY: dict[str, Any] = {
    "rise": RiseDBIngestor,
}


def get_db_ingestor(db_name: str, config: IngestionConfig) -> RiseDBIngestor:
    ingestor = DB_INGESTOR_REGISTRY[db_name](config)
    return ingestor
