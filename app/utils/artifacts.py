import shutil
from pathlib import Path
from typing import Iterable, Tuple, Optional
from huggingface_hub import snapshot_download
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DATA_DIR = Path(os.getenv("APP_DATA_DIR", str(PROJECT_ROOT / "data")))
APP_ARTIFACTS_DIR = Path(
    os.getenv("APP_ARTIFACTS_DIR", str(PROJECT_ROOT / "artifacts"))
)


def _copy_if_missing(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


def ensure_corpus_assets(
    corpus_name: str,
    repo_id: str,
    revision: str = "main",
    want_pdf: bool = True,
) -> Tuple[Path, Optional[Path]]:
    """
    Ensure FAISS index (and optional PDF) for `corpus_name` exist under artifacts/faiss/{corpus_name}.
    If missing, download from HF dataset repo into the local hub cache, then copy into artifacts.

    Returns:
        (faiss_dir, pdf_path) where pdf_path may be None if want_pdf=False
    """
    faiss_dir = APP_ARTIFACTS_DIR / "faiss" / corpus_name
    index_faiss_path = faiss_dir / "index.faiss"
    index_pkl_path = faiss_dir / "index.pkl"
    manifest_path = faiss_dir / "manifest.json"
    pdf_dest = APP_DATA_DIR / f"{corpus_name}.pdf"

    # if already present, nothing to do
    have_faiss = (
        index_faiss_path.exists() and index_pkl_path.exists() and manifest_path.exists()
    )
    have_pdf = (not want_pdf) or pdf_dest.exists()
    if have_faiss and have_pdf:
        return faiss_dir, (pdf_dest if want_pdf else None)

    # otherwise only download missing files
    # #  TODO: will need to modify HF repo structure to allow indices for other corpora
    patterns: Iterable[str] = [
        "indices/faiss/index.faiss",
        "indices/faiss/index.pkl",
        "indices/faiss/manifest.json",
    ]
    if want_pdf:
        patterns = list(patterns) + [f"source_docs/pdf/{corpus_name}.pdf"]

    print(
        f"[artifacts] Downloading missing assets for '{corpus_name}'"
        f"from '{repo_id}' ({revision})..."
    )

    cache_dir = Path(
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            revision=revision,
            allow_patterns=list(patterns),
        )
    )

    _copy_if_missing(cache_dir / "indices" / "faiss" / "index.faiss", index_faiss_path)
    _copy_if_missing(cache_dir / "indices" / "faiss" / "index.pkl", index_pkl_path)
    _copy_if_missing(cache_dir / "indices" / "faiss" / "manifest.json", manifest_path)

    if want_pdf:
        src_pdf = cache_dir / "source_docs" / "pdf" / f"{corpus_name}.pdf"
        _copy_if_missing(src_pdf, pdf_dest)

    print(f"[artifacts] Ready: {faiss_dir}")
    return faiss_dir, (pdf_dest if want_pdf else None)
