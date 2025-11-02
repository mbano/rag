# RAG Application Tests

This directory contains comprehensive tests for the RAG (Retrieval-Augmented Generation) application.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_main.py             # Tests for FastAPI endpoints
├── test_rag_pipeline.py     # Tests for RAG pipeline functions
├── test_artifacts.py        # Tests for artifact management utilities
├── test_docs.py             # Tests for document processing utilities
├── test_text.py             # Tests for text processing utilities
├── test_urls.py             # Tests for URL processing utilities
├── test_config.py           # Tests for configuration utilities
├── test_api.py              # Legacy API tests (for backward compatibility)
└── README.md                # This file
```

## Test Categories

### Unit Tests
- **test_main.py**: FastAPI endpoint tests
- **test_rag_pipeline.py**: RAG pipeline function tests
- **test_artifacts.py**: Artifact management tests
- **test_docs.py**: Document processing tests
- **test_text.py**: Text processing tests
- **test_urls.py**: URL processing tests
- **test_config.py**: Configuration loading tests

### Integration Tests
- Tests that verify the interaction between different components
- End-to-end workflow tests
- API integration tests

## Running Tests

### Using the Test Runner Script
```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py -v

# Run with coverage report
python run_tests.py -c

# Run tests in parallel
python run_tests.py -p

# Run specific test file
python run_tests.py tests/test_main.py

# Run specific test files
python run_tests.py tests/test_main.py
```

### Using pytest directly
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py

# Run specific test function
pytest tests/test_main.py::TestMainAPI::test_root_endpoint

# Run with coverage
pytest --cov=app --cov-report=html

# Run in parallel
pytest -n auto
```

### Running specific test categories
```bash
# Run API tests
pytest tests/test_main.py

# Run utility tests
pytest tests/test_artifacts.py tests/test_docs.py tests/test_text.py tests/test_urls.py tests/test_config.py

# Run pipeline tests
pytest tests/test_rag_pipeline.py

# Run all tests except slow ones (if you add slow markers later)
pytest -m "not slow"
```

## Test Coverage

The tests aim to achieve comprehensive coverage of:

1. **API Endpoints** (`test_main.py`)
   - GET `/` status endpoint
   - POST `/ask` question endpoint
   - Error handling
   - Request validation

2. **RAG Pipeline** (`test_rag_pipeline.py`)
   - Query analysis
   - Document retrieval
   - Answer generation
   - State management

3. **Artifact Management** (`test_artifacts.py`)
   - File copying utilities
   - Asset synchronization
   - Hugging Face integration
   - Local/remote comparison

4. **Document Processing** (`test_docs.py`)
   - PDF document cleaning
   - Web document filtering
   - Document loading
   - Metadata handling

5. **Text Processing** (`test_text.py`)
   - Token cleaning
   - Stopword removal
   - Punctuation handling
   - Unicode support

6. **URL Processing** (`test_urls.py`)
   - URL to resource name conversion
   - Special character handling
   - Hash generation
   - Consistency checks

7. **Configuration** (`test_config.py`)
   - YAML loading
   - Configuration validation
   - Error handling
   - File path resolution

## Fixtures

The `conftest.py` file provides shared fixtures:

- `temp_dir`: Temporary directory for test files
- `mock_env_vars`: Mocked environment variables
- `sample_documents`: Sample Document objects
- `sample_config`: Sample configuration data

## Mocking Strategy

Tests use extensive mocking to:
- Avoid external API calls
- Isolate units under test
- Provide predictable test data
- Speed up test execution

Key mocking patterns:
- Environment variables
- File system operations
- External API calls
- LangChain components
- Hugging Face operations

## Test Data

Tests use:
- Synthetic data for predictable results
- Temporary files for file operations
- Mock objects for external dependencies
- Fixtures for reusable test data

## Continuous Integration

Tests are designed to run in CI environments:
- No external dependencies
- Deterministic results
- Fast execution
- Clear error messages

## Adding New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py`
2. Use descriptive test names
3. Add appropriate markers
4. Include docstrings
5. Use fixtures when possible
6. Mock external dependencies
7. Test both success and failure cases

## Debugging Tests

To debug failing tests:

```bash
# Run with maximum verbosity
pytest -vvv

# Run with print statements
pytest -s

# Run specific test with debugging
pytest tests/test_main.py::TestMainAPI::test_root_endpoint -vvv -s

# Use pytest debugging features
pytest --pdb  # Drop into debugger on failure
pytest --pdb-trace  # Drop into debugger on first failure
```

## Performance Considerations

- Tests use mocking to avoid slow operations
- Temporary files are cleaned up automatically
- Parallel execution is supported
- Timeout settings prevent hanging tests

## Dependencies

Test dependencies are listed in `requirements-dev.txt`:
- pytest
- pytest-cov
- pytest-xdist (for parallel execution)
- pytest-mock
- fastapi[test]
- langchain (for testing)
- langchain-core
- langchain-community
- langchain-openai
- langchain-cohere
- langgraph
- huggingface-hub
- ftfy
- nltk
- yaml
