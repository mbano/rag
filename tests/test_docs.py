import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from langchain_core.documents import Document
from app.utils.docs import (
    clean_pdf_doc,
    _clean_text,
    filter_web_docs,
    clean_web_doc,
    load_docs,
)


class TestDocsUtils:
    """Test cases for document utility functions."""

    def test_clean_pdf_doc_composite_element(self):
        """Test clean_pdf_doc with CompositeElement category."""
        doc = Document(
            page_content="Test content with special chars: @#$%",
            metadata={
                "category": "CompositeElement",
                "filename": "test.pdf",
                "page_number": 1,
                "extra_field": "should_be_removed",
            },
        )

        result = clean_pdf_doc(doc)

        assert result.page_content == "Test content with special chars: @#$%"
        assert "filename" in result.metadata
        assert "page_number" in result.metadata
        assert "extra_field" not in result.metadata
        assert result.metadata["filename"] == "test.pdf"
        assert result.metadata["page_number"] == 1

    def test_clean_pdf_doc_other_category(self):
        """Test clean_pdf_doc with non-CompositeElement category."""
        doc = Document(
            page_content="Test content",
            metadata={
                "category": "TableChunk",
                "filename": "test.pdf",
                "page_number": 1,
            },
        )

        result = clean_pdf_doc(doc)

        # Should return empty document for non-CompositeElement
        assert result.page_content == ""
        assert result.metadata == {}

    def test_clean_pdf_doc_missing_metadata(self):
        """Test clean_pdf_doc with missing metadata fields."""
        doc = Document(
            page_content="Test content",
            metadata={
                "category": "CompositeElement"
                # Missing filename and page_number
            },
        )

        result = clean_pdf_doc(doc)

        assert result.page_content == "Test content"
        assert result.metadata == {}

    def test_clean_text(self):
        """Test _clean_text function."""
        # Test with text that needs fixing
        test_text = "This is a test with some special characters: @#$%"
        result = _clean_text(test_text)

        # Should return cleaned text (ftfy handles various text issues)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_clean_text_empty_string(self):
        """Test _clean_text with empty string."""
        result = _clean_text("")
        assert result == ""

    def test_clean_text_unicode(self):
        """Test _clean_text with unicode characters."""
        test_text = "Test with unicode: café, naïve, résumé"
        result = _clean_text(test_text)

        assert isinstance(result, str)
        assert "café" in result or "cafe" in result  # ftfy might normalize

    def test_filter_web_docs(self):
        """Test filter_web_docs function."""
        docs = [
            Document(
                page_content="Narrative text content",
                metadata={"category": "NarrativeText", "url": "http://example1.com"},
            ),
            Document(
                page_content="Table content",
                metadata={"category": "Table", "url": "http://example2.com"},
            ),
            Document(
                page_content="Another narrative",
                metadata={"category": "NarrativeText", "url": "http://example3.com"},
            ),
            Document(
                page_content="Image content",
                metadata={"category": "Image", "url": "http://example4.com"},
            ),
        ]

        result = filter_web_docs(docs)

        # Should only keep NarrativeText documents
        assert len(result) == 2
        for doc in result:
            assert doc.metadata["category"] == "NarrativeText"

    def test_filter_web_docs_empty_list(self):
        """Test filter_web_docs with empty list."""
        result = filter_web_docs([])
        assert result == []

    def test_filter_web_docs_no_matching_categories(self):
        """Test filter_web_docs with no matching categories."""
        docs = [
            Document(
                page_content="Table content",
                metadata={"category": "Table", "url": "http://example1.com"},
            ),
            Document(
                page_content="Image content",
                metadata={"category": "Image", "url": "http://example2.com"},
            ),
        ]

        result = filter_web_docs(docs)
        assert result == []

    def test_clean_web_doc(self):
        """Test clean_web_doc function."""
        doc = Document(
            page_content="Web content with special chars: @#$%",
            metadata={
                "url": "http://example.com",
                "title": "Test Title",
                "extra_field": "should_be_removed",
            },
        )

        result = clean_web_doc(doc)

        assert result.page_content == "Web content with special chars: @#$%"
        assert "url" in result.metadata
        assert "title" not in result.metadata
        assert "extra_field" not in result.metadata
        assert result.metadata["url"] == "http://example.com"

    def test_clean_web_doc_missing_url(self):
        """Test clean_web_doc with missing url metadata."""
        doc = Document(page_content="Web content", metadata={"title": "Test Title"})

        result = clean_web_doc(doc)

        assert result.page_content == "Web content"
        assert result.metadata == {}

    @pytest.mark.allow_real_io
    def test_load_docs_single_directory(self):
        """Test load_docs with a single document directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_dir = Path(temp_dir) / "documents"
            subdir = doc_dir / "test_doc"
            subdir.mkdir(parents=True)

            # Create a documents.jsonl file
            doc_data = {
                "page_content": "Test content",
                "metadata": {"filename": "test.pdf", "page_number": 1},
            }

            with open(subdir / "documents.jsonl", "w") as f:
                f.write(json.dumps(doc_data) + "\n")

            with patch("app.utils.docs.DOC_DIR", doc_dir):
                result = load_docs(doc_dir)

                assert len(result) == 1
                assert isinstance(result[0], Document)
                assert result[0].page_content == "Test content"
                assert result[0].metadata["filename"] == "test.pdf"
                assert str(doc_dir).startswith(
                    temp_dir
                ), "Test attempted to write outside the temp directory!"

    @pytest.mark.allow_real_io
    def test_load_docs_multiple_directories(self):
        """Test load_docs with multiple document directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_dir = Path(temp_dir) / "documents"

            # Create first document directory
            subdir1 = doc_dir / "doc1"
            subdir1.mkdir(parents=True)
            doc_data1 = {
                "page_content": "Content 1",
                "metadata": {"filename": "doc1.pdf"},
            }
            with open(subdir1 / "documents.jsonl", "w") as f:
                f.write(json.dumps(doc_data1) + "\n")

            # Create second document directory
            subdir2 = doc_dir / "doc2"
            subdir2.mkdir(parents=True)
            doc_data2 = {
                "page_content": "Content 2",
                "metadata": {"filename": "doc2.pdf"},
            }
            with open(subdir2 / "documents.jsonl", "w") as f:
                f.write(json.dumps(doc_data2) + "\n")

            with patch("app.utils.docs.DOC_DIR", doc_dir):
                result = load_docs(doc_dir)

                assert len(result) == 2
                contents = [doc.page_content for doc in result]
                assert "Content 1" in contents
                assert "Content 2" in contents
                assert str(doc_dir).startswith(
                    temp_dir
                ), "Test attempted to write outside the temp directory!"

    @pytest.mark.allow_real_io
    def test_load_docs_multiple_lines_per_file(self):
        """Test load_docs with multiple documents per file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_dir = Path(temp_dir) / "documents"
            subdir = doc_dir / "test_doc"
            subdir.mkdir(parents=True)

            # Create documents.jsonl with multiple documents
            doc_data1 = {
                "page_content": "Content 1",
                "metadata": {"filename": "test.pdf", "page_number": 1},
            }
            doc_data2 = {
                "page_content": "Content 2",
                "metadata": {"filename": "test.pdf", "page_number": 2},
            }

            with open(subdir / "documents.jsonl", "w") as f:
                f.write(json.dumps(doc_data1) + "\n")
                f.write(json.dumps(doc_data2) + "\n")

            with patch("app.utils.docs.DOC_DIR", doc_dir):
                result = load_docs(doc_dir)

                assert len(result) == 2
                contents = [doc.page_content for doc in result]
                assert "Content 1" in contents
                assert "Content 2" in contents
                assert str(doc_dir).startswith(
                    temp_dir
                ), "Test attempted to write outside the temp directory!"

    def test_load_docs_empty_directory(self):
        """Test load_docs with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_dir = Path(temp_dir) / "documents"
            doc_dir.mkdir(parents=True)

            with patch("app.utils.docs.DOC_DIR", doc_dir):
                result = load_docs()
                assert result == []

    #  TODO
    def _test_load_docs_invalid_json(self):
        """Test load_docs with invalid JSON in documents.jsonl."""
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_dir = Path(temp_dir) / "documents"
            subdir = doc_dir / "test_doc"
            subdir.mkdir(parents=True)

            # Create invalid JSON
            with open(subdir / "documents.jsonl", "w") as f:
                f.write("invalid json\n")

            with patch("app.utils.docs.DOC_DIR", doc_dir):
                # Should handle invalid JSON gracefully
                with pytest.raises(json.JSONDecodeError):
                    load_docs()

    #  TODO
    def _test_load_docs_specific_filename(self):
        """Test load_docs with specific filename parameter."""
        # Note: The current implementation doesn't support filename filtering
        # This test documents the current behavior
        with tempfile.TemporaryDirectory() as temp_dir:
            doc_dir = Path(temp_dir) / "documents"
            subdir = doc_dir / "test_doc"
            subdir.mkdir(parents=True)

            doc_data = {
                "page_content": "Test content",
                "metadata": {"filename": "test.pdf"},
            }
            with open(subdir / "documents.jsonl", "w") as f:
                f.write(json.dumps(doc_data) + "\n")

            with patch("app.utils.docs.DOC_DIR", doc_dir):
                # Currently ignores filename parameter
                result = load_docs(filename="test.pdf")
                assert len(result) == 1
