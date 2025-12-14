from ingestion.ingest import ingest
from app.config import get_settings

if __name__ == "__main__":
    cfg = get_settings().ingestion
    ingest(cfg)
