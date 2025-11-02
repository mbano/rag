import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from app.utils.artifacts import (
    _copy_if_missing,
    _check_for_pdfs,
    _check_for_urls,
    _check_for_docs,
    ensure_corpus_assets,
)


class TestArtifactsUtils:
    """Test cases for artifacts utility functions."""

    def test_copy_if_missing_file_exists(self):
        """Test _copy_if_missing when destination file already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "source.txt"
            dst_path = Path(temp_dir) / "dest.txt"

            # Create source file
            src_path.write_text("source content")
            # Create destination file
            dst_path.write_text("existing content")

            _copy_if_missing(src_path, dst_path)

            # Should not overwrite existing file
            assert dst_path.read_text() == "existing content"

    def test_copy_if_missing_file_not_exists(self):
        """Test _copy_if_missing when destination file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "source.txt"
            dst_path = Path(temp_dir) / "subdir" / "dest.txt"

            # Create source file
            src_path.write_text("source content")

            _copy_if_missing(src_path, dst_path)

            # Should copy file and create directory
            assert dst_path.exists()
            assert dst_path.read_text() == "source content"

    def test_copy_if_missing_create_directories(self):
        """Test _copy_if_missing creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_path = Path(temp_dir) / "source.txt"
            dst_path = Path(temp_dir) / "deep" / "nested" / "dest.txt"

            src_path.write_text("source content")

            _copy_if_missing(src_path, dst_path)

            assert dst_path.exists()
            assert dst_path.parent.exists()

    @patch("app.utils.artifacts.PDF_DIR")
    def test_check_for_pdfs(self, mock_pdf_dir):
        """Test _check_for_pdfs function."""
        # Mock PDF_DIR to return some local PDFs
        mock_pdf_dir.glob.return_value = [Path("local1.pdf"), Path("local2.pdf")]

        # Mock remote filesystem
        mock_remote_fs = MagicMock()
        mock_remote_fs.glob.return_value = [
            Path("datasets/repo/source_docs/pdf/remote1.pdf"),
            Path("datasets/repo/source_docs/pdf/remote2.pdf"),
            Path("datasets/repo/source_docs/pdf/local1.pdf"),  # This one exists locally
        ]

        with patch("app.utils.artifacts.HF_DATASET_REPO", "test-repo"):
            missing_pdfs = _check_for_pdfs(mock_remote_fs)

            # Should return only the missing PDFs
            assert len(missing_pdfs) == 1
            assert missing_pdfs[0] == Path("source_docs/pdf/remote1.pdf")
            assert missing_pdfs[0] != Path(
                "source_docs/pdf/remote2.pdf"
            )  # This should be missing too

    @patch("app.utils.artifacts.WEB_DIR")
    def test_check_for_urls_local_file_exists(self, mock_web_dir):
        """Test _check_for_urls when local urls.json exists."""
        # Mock local URLs file
        mock_web_dir.__truediv__.return_value = Path("urls.json")

        local_urls = {"urls": ["http://example1.com", "http://example2.com"]}
        remote_urls = {
            "urls": [
                "http://example1.com",
                "http://example2.com",
                "http://example3.com",
            ]
        }

        mock_remote_fs = MagicMock()
        mock_remote_fs.open.return_value.__enter__.return_value.read.return_value = (
            json.dumps(remote_urls)
        )

        with patch("builtins.open", mock_open(read_data=json.dumps(local_urls))), patch(
            "app.utils.artifacts.HF_DATASET_REPO", "test-repo"
        ):

            missing_urls = _check_for_urls(mock_remote_fs)

            assert len(missing_urls) == 1
            assert "http://example3.com" in missing_urls

    @patch("app.utils.artifacts.WEB_DIR")
    def test_check_for_urls_local_file_not_exists(self, mock_web_dir):
        """Test _check_for_urls when local urls.json doesn't exist."""
        mock_web_dir.__truediv__.return_value = Path("nonexistent.json")

        remote_urls = {"urls": ["http://example1.com", "http://example2.com"]}

        mock_remote_fs = MagicMock()
        mock_remote_fs.open.return_value.__enter__.return_value.read.return_value = (
            json.dumps(remote_urls)
        )

        with patch("builtins.open", side_effect=FileNotFoundError), patch(
            "app.utils.artifacts.HF_DATASET_REPO", "test-repo"
        ):

            missing_urls = _check_for_urls(mock_remote_fs)

            # Should return all remote URLs when local file doesn't exist
            assert len(missing_urls) == 2
            assert "http://example1.com" in missing_urls
            assert "http://example2.com" in missing_urls

    @patch("app.utils.artifacts.DOC_DIR")
    def test_check_for_docs(self, mock_doc_dir):
        """Test _check_for_docs function."""
        # Mock local document subdirectories
        mock_doc_dir.glob.return_value = [Path("local_doc1/"), Path("local_doc2/")]

        # Mock remote filesystem
        mock_remote_fs = MagicMock()
        mock_remote_fs.glob.return_value = [
            Path("datasets/repo/vector_stores/documents/remote_doc1/"),
            Path("datasets/repo/vector_stores/documents/remote_doc2/"),
            Path(
                "datasets/repo/vector_stores/documents/local_doc1/"
            ),  # This one exists locally
        ]

        with patch("app.utils.artifacts.HF_DATASET_REPO", "test-repo"):
            missing_docs = _check_for_docs(mock_remote_fs)

            # Should return missing document paths
            assert len(missing_docs) == 2
            assert any("remote_doc1" in str(path) for path in missing_docs)
            assert any("remote_doc2" in str(path) for path in missing_docs)

    @patch("app.utils.artifacts.snapshot_download")
    @patch("app.utils.artifacts.HfFileSystem")
    @patch("app.utils.artifacts._check_for_pdfs")
    @patch("app.utils.artifacts._check_for_urls")
    @patch("app.utils.artifacts._check_for_docs")
    def test_ensure_corpus_assets_already_present(
        self,
        mock_check_docs,
        mock_check_urls,
        mock_check_pdfs,
        mock_hf_fs,
        mock_snapshot,
    ):
        """Test ensure_corpus_assets when assets already exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir) / "artifacts"
            faiss_dir = artifacts_dir / "faiss"
            doc_dir = artifacts_dir / "documents"

            # Create existing files
            faiss_dir.mkdir(parents=True)
            doc_dir.mkdir(parents=True)
            (faiss_dir / "index.faiss").touch()
            (faiss_dir / "index.pkl").touch()
            (faiss_dir / "manifest.json").write_text(
                '{"embedding_model": "test-model"}'
            )

            with patch("app.utils.artifacts.ART_DIR", artifacts_dir):
                result_faiss, result_doc = ensure_corpus_assets(
                    repo_id="test-repo", revision="main", want_sources=False
                )

                assert result_faiss == faiss_dir
                assert result_doc == doc_dir
                # Should not call snapshot_download
                mock_snapshot.assert_not_called()

    @patch("app.utils.artifacts.snapshot_download")
    @patch("app.utils.artifacts.HfFileSystem")
    @patch("app.utils.artifacts._check_for_pdfs")
    @patch("app.utils.artifacts._check_for_urls")
    @patch("app.utils.artifacts._check_for_docs")
    @patch("builtins.open", new_callable=mock_open)
    def test_ensure_corpus_assets_missing_assets(
        self,
        mock_file,
        mock_check_docs,
        mock_check_urls,
        mock_check_pdfs,
        mock_hf_fs,
        mock_snapshot,
    ):
        """Test ensure_corpus_assets when assets are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir) / "artifacts"

            # Mock missing assets
            mock_check_docs.return_value = [Path("missing_doc1/documents.jsonl")]
            mock_check_pdfs.return_value = [Path("missing.pdf")]
            mock_check_urls.return_value = ["http://missing.com"]

            # Mock snapshot download
            cache_dir = Path(temp_dir) / "cache"
            cache_dir.mkdir()
            mock_snapshot.return_value = str(cache_dir)

            # Mock file operations to prevent writing to real files
            mock_file.return_value.__enter__.return_value.read.return_value = (
                '{"urls": []}'
            )

            with patch("app.utils.artifacts.ART_DIR", artifacts_dir), patch(
                "app.utils.artifacts.PDF_DIR", Path(temp_dir) / "pdf"
            ), patch("app.utils.artifacts.WEB_DIR", Path(temp_dir) / "web"):

                result_faiss, result_doc = ensure_corpus_assets(
                    repo_id="test-repo", revision="main", want_sources=True
                )

                # Should call snapshot_download
                mock_snapshot.assert_called_once()
                assert result_faiss == artifacts_dir / "faiss"
                assert result_doc == artifacts_dir / "documents"

    @patch("builtins.open", new_callable=mock_open)
    def test_ensure_corpus_assets_with_sources(self, mock_file):
        """Test ensure_corpus_assets with want_sources=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir) / "artifacts"

            # Mock file operations to prevent writing to real files
            mock_file.return_value.__enter__.return_value.read.return_value = (
                '{"urls": []}'
            )

            with patch("app.utils.artifacts.ART_DIR", artifacts_dir), patch(
                "app.utils.artifacts.snapshot_download"
            ) as mock_snapshot, patch("app.utils.artifacts.HfFileSystem"), patch(
                "app.utils.artifacts._check_for_pdfs"
            ) as mock_check_pdfs, patch(
                "app.utils.artifacts._check_for_urls"
            ) as mock_check_urls, patch(
                "app.utils.artifacts._check_for_docs"
            ) as mock_check_docs:

                mock_check_pdfs.return_value = [Path("test.pdf")]
                mock_check_urls.return_value = ["http://test.com"]
                mock_check_docs.return_value = [Path("test/documents.jsonl")]
                mock_snapshot.return_value = str(Path(temp_dir) / "cache")

                result_faiss, result_doc = ensure_corpus_assets(
                    repo_id="test-repo", want_sources=True
                )

                # Should check for sources
                mock_check_pdfs.assert_called_once()
                mock_check_urls.assert_called_once()
                mock_check_docs.assert_called_once()

    def test_ensure_corpus_assets_without_sources(self):
        """Test ensure_corpus_assets with want_sources=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = Path(temp_dir) / "artifacts"
            faiss_dir = artifacts_dir / "faiss"
            doc_dir = artifacts_dir / "documents"

            # Create existing files
            faiss_dir.mkdir(parents=True)
            doc_dir.mkdir(parents=True)
            (faiss_dir / "index.faiss").touch()
            (faiss_dir / "index.pkl").touch()
            (faiss_dir / "manifest.json").write_text(
                '{"embedding_model": "test-model"}'
            )

            with patch("app.utils.artifacts.ART_DIR", artifacts_dir):
                result_faiss, result_doc = ensure_corpus_assets(
                    repo_id="test-repo", want_sources=False
                )

                assert result_faiss == faiss_dir
                assert result_doc == doc_dir
