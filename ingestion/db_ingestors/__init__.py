import importlib
import pkgutil

DB_INGESTORS = {}

for _, name, _ in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f"{__name__}.{name}")
    if hasattr(module, "DB_NAME") and hasattr(module, "ingest"):
        DB_INGESTORS[module.DB_NAME] = module.ingest
