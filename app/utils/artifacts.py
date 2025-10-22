import shutil
from pathlib import Path
from typing import Iterable, Tuple, Optional
from huggingface_hub import snapshot_download, HfApi
import json

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
ART_DIR = BASE_DIR / "artifacts"
DOC_DIR = ART_DIR / "documents"


def _copy_if_missing(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


def _copy_pdfs(repo_id, cache_dir):
    """
    Compares HF dataset repo's source_docs/pdf contents with
    local /data/pdf and downloads any missing files
    """
    hf_api = HfApi()
    files = hf_api.list_repo_files(
        repo_id=repo_id, repo_type="dataset", revision="main"
    )
    pdfs = [file for file in files if ".pdf" in file]

    for pdf in pdfs:
        file_name = pdf.split("/")[-1]
        dst = PDF_DIR / file_name
        _copy_if_missing(cache_dir / "source_docs" / "pdf" / file_name, dst)


def _check_for_pdfs():
    """
    Checks if every folder in ART_DIR/faiss that was built from a pdf
    has a corresponding file in DATA_DIR/pdf

    Returns a list of pdfs to download
    """
    faiss_dir = ART_DIR / "faiss"
    vs_subdirs = [path for path in faiss_dir.iterdir() if path.is_dir()]
    pdfs_to_look_for = []

    for dir in vs_subdirs:
        with open(dir / "manifest.json", "r") as f:
            manifest = json.load(f)
        if ".pdf" in manifest.get("source_file", "N/A"):
            pdfs_to_look_for.append(manifest.get("source_file"))

    local_pdfs = [pdf.name for pdf in Path(PDF_DIR).glob("*.pdf")]
    pdfs_to_download = list(set(pdfs_to_look_for).difference(set(local_pdfs)))

    return pdfs_to_download


def _check_for_docs():
    """
    Checks if every folder in ART_DIR/faiss that was built from a pdf
    has a corresponding folder and documents.jsonl file in DATA_DIR/documents

    Returns a list of file or resource names whose documents are missing locally
    """
    faiss_dir = ART_DIR / "faiss"
    missing_docs = []
    for subdir in faiss_dir.glob("*/"):
        if not (DOC_DIR / subdir.stem / "documents.jsonl").exists():
            missing_docs.append(subdir.stem)
    return missing_docs


def ensure_corpus_assets(
    repo_id: str,
    revision: str = "main",
    want_docs: bool = True,
    want_pdf: bool = True,
) -> Tuple[Path, Optional[Path]]:
    """
    Ensure FAISS vector store (and optional PDF) exists under artifacts/faiss/
    (this location implies a merged vector store).
    If missing, download from HF dataset repo into the local hub cache, then copy into artifacts.

    Returns:
        (faiss_dir, pdf_path) where pdf_path may be None if want_pdf=False
    """
    faiss_dir = ART_DIR / "faiss"
    index_faiss_path = faiss_dir / "index.faiss"
    index_pkl_path = faiss_dir / "index.pkl"
    manifest_path = faiss_dir / "manifest.json"
    docs_path = ART_DIR / "documents"

    # if already present, nothing to do
    have_faiss = (
        index_faiss_path.exists() and index_pkl_path.exists() and manifest_path.exists()
    )

    if have_faiss and not want_docs and not want_pdf:
        return faiss_dir

    # otherwise only download missing vector store files
    # #  TODO: will need to modify HF repo structure to allow indices for other corpora
    patterns: Iterable[str] = []
    if not have_faiss:
        vector_store_patterns = [
            "vector_stores/faiss/index.faiss",
            "vector_stores/faiss/index.pkl",
            "vector_stores/faiss/manifest.json",
        ]
        patterns = list(patterns) + vector_store_patterns

    print(f"[artifacts] Downloading missing assets from '{repo_id}' ({revision})...")

    cache_dir = Path(
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            revision=revision,
            allow_patterns=list(patterns),
        )
    )

    _copy_if_missing(
        cache_dir / "vector_stores" / "faiss" / "index.faiss", index_faiss_path
    )
    _copy_if_missing(
        cache_dir / "vector_stores" / "faiss" / "index.pkl", index_pkl_path
    )
    _copy_if_missing(
        cache_dir / "vector_stores" / "faiss" / "manifest.json", manifest_path
    )

    # only download missing docs and pdfs

    patterns = []
    docs_to_download = _check_for_docs()
    if docs_to_download:
        doc_patterns = [
            f"vector_stores/documents/{doc}/documents.jsonl" for doc in docs_to_download
        ]
        patterns = patterns + doc_patterns

    if want_pdf:
        pdfs_to_download = _check_for_pdfs()
        if pdfs_to_download:
            pdf_pattern = "source_docs/pdf/*.pdf"
            patterns = patterns + [pdf_pattern]

    if patterns:
        cache_dir = Path(
            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                revision=revision,
                allow_patterns=list(patterns),
            )
        )

        print(f"Downloading docs: {docs_to_download}")
        for src, name in zip(doc_patterns, docs_to_download):
            dst = docs_path / name / "documents.jsonl"
            _copy_if_missing(cache_dir / src, dst)

        print(f"Downloading pdfs: {pdfs_to_download}")
        _copy_pdfs(repo_id, cache_dir)

    print(f"[artifacts] Ready: {faiss_dir}")
    return faiss_dir


#  TODO: add download/sync with other file types
