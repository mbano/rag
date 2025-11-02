"""
Pytest configuration and shared fixtures for RAG application tests.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "test-openai-key",
            "COHERE_API_KEY": "test-cohere-key",
            "LANGSMITH_API_KEY": "test-langsmith-key",
            "LANGSMITH_TRACING": "true",
            "LANGSMITH_PROJECT": "test-project",
            "LANGSMITH_ENDPOINT": "https://api.langsmith.com",
            "HF_DATASET_REPO": "test-repo",
            "HF_DATASET_REVISION": "main",
        },
    ):
        yield


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    from langchain_core.documents import Document

    return [
        Document(
            page_content="This is a test document about artificial intelligence.",
            metadata={"filename": "test1.pdf", "page_number": 1},
        ),
        Document(
            page_content="Machine learning is a subset of AI.",
            metadata={"filename": "test2.pdf", "page_number": 2},
        ),
        Document(
            page_content="Deep learning uses neural networks.",
            metadata={"url": "https://example.com", "page_number": 1},
        ),
    ]


@pytest.fixture
def sample_config():
    """Create sample configuration for testing."""
    return {
        "embedding_model": "text-embedding-3-large",
        "vector_store": "faiss",
        "chunk_size": 1000,
        "chunk_overlap": 100,
        "retriever_params": {"k": 10},
        "reranker_params": {"model": "rerank-v3.5", "top_n": 4},
        "sparse_retriever_params": {"k": 8},
    }


# @pytest.fixture(autouse=True)
# def mock_file_operations():
#     """Automatically mock file operations to prevent tests from modifying real files."""
#     with patch('builtins.open', new_callable=mock_open) as mock_file:
#         # Mock JSON file reads to return safe defaults
#         mock_file.return_value.__enter__.return_value.read.return_value = '{"urls": []}'
#         yield mock_file


@pytest.fixture(autouse=True)
def mock_file_operations(request):
    """Automatically mock file operations to prevent tests from modifying real files."""
    # Skip mocking if test is marked to allow real I/O
    if request.node.get_closest_marker("allow_real_io"):
        yield
        return

    with patch("builtins.open", new_callable=mock_open) as mock_file:
        mock_file.return_value.__enter__.return_value.read.return_value = '{"urls": []}'
        yield mock_file
