def test_process_pdf_docs_filters_and_enriches():
    """Test PDF document processing pipeline"""
    from app.utils.docs import process_pdf_docs
    from app.config import load_config
    from langchain_core.documents import Document

    config = load_config()

    # Create mock PDF documents with different categories
    raw_docs = [
        Document(
            page_content="This is a composite element",
            metadata={
                "source": "test.pdf",
                "filename": "test.pdf",
                "page_number": 1,
                "category": "CompositeElement",
                "filetype": "application/pdf",
                "languages": ["eng"],
                "last_modified": "2024-01-01",
            },
        ),
        Document(
            page_content="This should be filtered",
            metadata={"category": "Header", "filename": "test.pdf"},
        ),
    ]

    processed = process_pdf_docs(raw_docs, config.ingestion)

    # Only CompositeElement should remain
    assert len(processed) == 1

    # Check metadata enrichment
    doc = processed[0]
    assert "doc_id" in doc.metadata
    assert "chunk_id" in doc.metadata
    assert "chunk_index" in doc.metadata
    assert "tenant_id" in doc.metadata
    assert "pipeline_version" in doc.metadata
    assert "ingested_at" in doc.metadata
    assert doc.metadata["tenant_id"] == "default"

    # Unwanted fields removed
    assert "category" not in doc.metadata


def test_process_web_docs_filters_and_enriches():
    """Test web document processing pipeline"""
    from app.utils.docs import process_web_docs
    from app.config import load_config
    from langchain_core.documents import Document

    config = load_config()

    raw_docs = [
        Document(
            page_content="This is narrative text",
            metadata={
                "url": "https://example.com/page",
                "category": "NarrativeText",
                "filetype": "text/html",
                "languages": ["eng"],
            },
        ),
        Document(
            page_content="This is a title",
            metadata={
                "url": "https://example.com/page",
                "category": "Title",
                "filetype": "text/html",
                "languages": ["eng"],
            },
        ),
        Document(
            page_content="Should be filtered",
            metadata={
                "url": "https://example.com/page",
                "category": "Image",
                "filetype": "text/html",
                "languages": ["eng"],
            },
        ),
    ]

    processed = process_web_docs(raw_docs, config.ingestion)

    # Only NarrativeText and Title should remain
    assert len(processed) == 2

    # Check metadata enrichment
    doc = processed[0]
    assert "doc_id" in doc.metadata
    assert "chunk_id" in doc.metadata
    assert "doc_title" in doc.metadata
    assert doc.metadata["source"] == doc.metadata["doc_id"]

    # URLs should be normalized
    assert doc.metadata["doc_id"].startswith("https://")
