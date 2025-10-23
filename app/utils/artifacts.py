import shutil
from pathlib import Path
from huggingface_hub import snapshot_download, HfFileSystem
import json
import os

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
ART_DIR = BASE_DIR / "artifacts"
DOC_DIR = ART_DIR / "documents"
WEB_DIR = DATA_DIR / "web"
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO")


def _copy_if_missing(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


def _check_for_pdfs(remote_fs):
    """
    Compare local pdfs to those in the remote dataset repo.

    Return a list of remote paths of pdfs missing locally
    """

    local_pdf_names = [pdf.stem for pdf in PDF_DIR.glob("*")]
    remote_pdf_files = [
        Path(pdf)
        for pdf in remote_fs.glob(f"datasets/{HF_DATASET_REPO}/source_docs/pdf/*")
    ]
    missing_pdf_paths = [
        Path(*pdf.parts[3:])
        for pdf in remote_pdf_files
        if pdf.stem not in local_pdf_names
    ]
    return missing_pdf_paths


def _check_for_urls(remote_fs):
    """
    Compare local web urls to those in the remote dataset repo.

    Return a list of urls (str) missing locally
    """
    try:
        with open(WEB_DIR / "urls.json", "r") as f:
            local_urls = json.load(f)["urls"]
    except FileNotFoundError:
        local_urls = []
    with remote_fs.open(
        f"datasets/{HF_DATASET_REPO}/source_docs/web/urls.json", "r"
    ) as f:
        remote_urls = json.load(f)["urls"]
    missing_urls = [url for url in remote_urls if url not in local_urls]
    return missing_urls


def _check_for_docs(remote_fs):
    """
    Compare local documents to those in the remote dataset repo.

    Return a list of remote paths of documents missing locally
    """

    local_docs_subdirs_names = [subdir.stem for subdir in DOC_DIR.glob("*/")]
    remote_docs_subdirs = [
        Path(subdir)
        for subdir in remote_fs.glob(
            f"datasets/{HF_DATASET_REPO}/vector_stores/documents/*/"
        )
    ]
    missing_docs_paths = [
        Path(*subdir.parts[3:]) / "documents.jsonl"
        for subdir in remote_docs_subdirs
        if subdir.stem not in local_docs_subdirs_names
    ]
    return missing_docs_paths


def ensure_corpus_assets(
    repo_id: str,
    revision: str = "main",
    want_sources: bool = True,
) -> Path:
    """
    Ensure FAISS index artifacts exist under artifacts/faiss/
    (this location implies a merged vector store).
    Ensure document artifacts exist under artifacts/documents
    Optionally, ensure pdfs exist under data/pdf and web urls under data/web

    If missing, download from HF dataset repo

    Returns:
        (faiss_dir, doc_dir)
    """
    faiss_dir = ART_DIR / "faiss"
    index_faiss_path = faiss_dir / "index.faiss"
    index_pkl_path = faiss_dir / "index.pkl"
    manifest_path = faiss_dir / "manifest.json"
    doc_dir = ART_DIR / "documents"

    # if already present, nothing to do
    have_faiss = (
        index_faiss_path.exists() and index_pkl_path.exists() and manifest_path.exists()
    )
    have_docs = doc_dir.exists()

    if have_faiss and have_docs and not want_sources:
        return faiss_dir, doc_dir

    remote_filesystem = HfFileSystem()

    patterns = []
    if not have_faiss:
        vector_store_patterns = [
            "vector_stores/faiss/index.faiss",
            "vector_stores/faiss/index.pkl",
            "vector_stores/faiss/manifest.json",
        ]
        patterns.extend(vector_store_patterns)

    doc_patterns = [str(p) for p in _check_for_docs(remote_filesystem)]
    patterns.extend(doc_patterns)

    if want_sources:
        pdfs_to_download = [str(p) for p in _check_for_pdfs(remote_filesystem)]
        if pdfs_to_download:
            patterns.extend(pdfs_to_download)
        urls_to_copy = _check_for_urls(remote_filesystem)
        if urls_to_copy:
            try:
                with open(WEB_DIR / "urls.json", "r+") as f:
                    urls = json.load(f)
                    urls["urls"].extend(urls_to_copy)
                    json.dump(urls, f)
            except FileNotFoundError:
                WEB_DIR.mkdir(parents=True, exist_ok=True)
                with open(WEB_DIR / "urls.json", "w") as f:
                    urls = {"urls": urls_to_copy}
                    json.dump(urls, f)

    print(f"[artifacts] Downloading missing assets from '{repo_id}' ({revision})...")

    cache_dir = Path(
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            revision=revision,
            allow_patterns=patterns,
        )
    )

    cache_dirs = [cache_dir / path for path in patterns]
    dest_dirs = [index_faiss_path, index_pkl_path, manifest_path]
    dest_dirs.extend(
        [DOC_DIR / f"{p.split('/')[-2]}/documents.jsonl" for p in doc_patterns]
    )
    dest_dirs.extend([PDF_DIR / f"{p.split('/')[-1]}" for p in pdfs_to_download])

    for src, dst in zip(cache_dirs, dest_dirs):
        _copy_if_missing(src, dst)

    print(f"[artifacts] Ready: {faiss_dir}")
    return faiss_dir, doc_dir


#  TODO: add download/sync with other file types
