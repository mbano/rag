# RAG Backend

An end-to-end Retrieval-Augmented Generation (RAG) system built with LangChain, FastAPI, and LangGraph. This system provides intelligent question-answering capabilities by combining dense and sparse retrieval methods with large language models.

## Features

- **Hybrid Retrieval**: Combines dense vector search (FAISS/OpenSearch) with sparse BM25 retrieval for optimal results
- **Reranking**: Optional Cohere reranking for improved relevance
- **Multi-Source Ingestion**: Support for PDFs, web pages, and SQL databases
- **Flexible Configuration**: YAML-based configuration for easy customization
- **Vector Store Support**: FAISS (local) and OpenSearch (production)
- **LLM Integration**: OpenAI GPT models with support for query analysis and answer generation
- **Evaluation Framework**: Built-in evaluation using LangSmith
- **Production Ready**: Docker support, AWS infrastructure (Terraform), CI/CD pipeline
- **Monitoring**: LangSmith integration for tracing and debugging

## Architecture

The RAG pipeline consists of three main stages:

1. **Query Analysis**: Uses an LLM to analyze and refine the user's question
2. **Retrieval**: Hybrid retrieval combining:
   - Dense retrieval (semantic search using embeddings)
   - Sparse retrieval (BM25 keyword search)
   - Optional reranking with Cohere
3. **Generation**: LLM generates answers based on retrieved context

## Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)
- OpenAI API key
- Cohere API key (optional, for reranking)
- AWS credentials (for production deployment with OpenSearch)

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd rag
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install development dependencies (optional):
```bash
pip install -r requirements-dev.txt
```

5. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key
COHERE_API_KEY=your_cohere_api_key  # Optional
LANGSMITH_API_KEY=your_langsmith_key  # Optional
LANGSMITH_TRACING=true  # Optional
LANGSMITH_PROJECT=your_project_name  # Optional
HF_DATASET_REPO=your_huggingface_repo  # Optional
```

### Docker Setup

1. Build the Docker image:
```bash
docker-compose build
```

2. Run the container:
```bash
docker-compose up
```

The API will be available at `http://localhost:8000`.

## Configuration

The system is configured via `config.yaml`. Key configuration sections:

### Vector Stores
Configure FAISS (local) or OpenSearch (production):
```yaml
vector_stores:
  faiss:
    type: "faiss"
    embedding_model: "text-embedding-3-large"
    embedding_dimension: 3072
```

### LLMs
Define language models:
```yaml
llms:
  gpt_4o_mini:
    model_name: "gpt-4o-mini"
    model_provider: "openai"
```

### Nodes
Configure each stage of the RAG pipeline:
```yaml
nodes:
  analyze_query:
    llm: "gpt_4o_mini"
    params:
      temperature: 0.2
  retrieve:
    dense:
      params:
        k: 10
    sparse:
      params:
        k: 4
    reranker:
      type: "cohere"
      params:
        model: "rerank-v3.5"
        top_n: 4
  generate:
    llm: "gpt_4o_mini"
    params:
      temperature: 0.7
```

## Usage

### Starting the API

Run the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or with Docker:
```bash
docker-compose up
```

### API Endpoints

#### Ask a Question
```bash
POST /ask
Content-Type: application/json

{
  "question": "What is your question?"
}
```

Example with curl:
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'
```

#### Health Check
```bash
GET /

Response: {"message": "status OK"}
```

### Frontend

A Next.js frontend is available at `frontend/nextjs-app/`. **Note: The frontend is currently only supported when the backend is run locally.**

To run the frontend:
```bash
cd frontend/nextjs-app
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Data Ingestion

**Important**: Before using the application for the first time, you must run the ingestion script to create the vector store indices. This is required for the system to function properly.

Data ingestion requires placing source files or web URLs in their corresponding folders within `/data`, then running the ingestion script:

```bash
python scripts/ingest.py
```

#### PDF Documents

Place PDF files in the `/data/pdf` directory. The system will automatically process them during ingestion.

#### Web Pages

Create a `/data/web/urls.json` file with the following structure:

```json
{
    "urls": [
        "https://first.web.url",
        "https://second.web.url"
    ]
}
```

#### SQL Databases

SQL database ingestion requires creating a custom ingestor for each database. To add a new database source:

1. Create a new Python file under `/ingestion/db_ingestors/`
2. Add an entry to `DB_INGESTOR_REGISTRY` in `app/utils/db_ingestors.py`

#### FAISS Index Download

On startup, the application automatically attempts to download FAISS indices and source documents from the configured Hugging Face repository (if `HF_DATASET_REPO` is set).

### Evaluation

Run evaluations using LangSmith for tracking and analysis:

```bash
python evaluation/scripts/langsmith_eval.py
```

To generate evaluation datasets for testing:

```bash
python evaluation/scripts/populate_dataset.py
```

## Testing

Run tests with pytest:
```bash
pytest
```

Run specific test files:
```bash
pytest tests/test_rag_pipeline.py
pytest tests/test_vector_stores.py
```

## Scripts

### Data Ingestion
```bash
python scripts/ingest.py
```

Ingest data from PDFs, web pages, or SQL databases and create vector store indices. If OpenSearch is selected as the vector store, this script also uploads the processed files and document objects to their respective S3 buckets.


### Upload Source Files to S3
```bash
python ingestion/upload_src_files_to_s3.py
```

Upload source files to S3 for production deployment.

## Deployment

### AWS Deployment

Infrastructure is managed with Terraform. Configuration files are in `infra/terraform/`.

1. Navigate to the Terraform directory:
```bash
cd infra/terraform
```

2. Initialize Terraform:
```bash
terraform init
```

3. Plan the deployment:
```bash
terraform plan
```

4. Apply the configuration:
```bash
terraform apply
```

The infrastructure includes:
- ECS cluster for running the application
- OpenSearch for vector storage
- S3 for document storage
- ALB for load balancing
- VPC and security groups
- ECR for Docker images
- CloudWatch for logging

### CI/CD

GitHub Actions workflow is configured in `.github/workflows/ci.yml` for automated testing and deployment.

## Project Structure

```
.
├── app/                      # Main application code
│   ├── main.py              # FastAPI application
│   ├── rag_pipeline.py      # RAG pipeline implementation
│   ├── config.py            # Configuration management
│   └── utils/               # Utility modules
├── ingestion/               # Data ingestion scripts
├── evaluation/              # Evaluation framework
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── infra/                   # Infrastructure as code
│   └── terraform/           # Terraform configurations
├── frontend/                # Next.js frontend (local only)
├── prompts/                 # Prompt templates
├── config.yaml              # Main configuration file
├── requirements.txt         # Python dependencies
└── docker-compose.yml       # Docker composition
```

## Environment Variables

Required environment variables:

- `OPENAI_API_KEY`: OpenAI API key for embeddings and LLM
- `COHERE_API_KEY`: Cohere API key for reranking (optional)
- `LANGSMITH_API_KEY`: LangSmith API key for tracing (optional)
- `LANGSMITH_TRACING`: Enable LangSmith tracing (optional)
- `LANGSMITH_PROJECT`: LangSmith project name (optional)
- `HF_DATASET_REPO`: HuggingFace dataset repository (optional)
- `HF_DATASET_REVISION`: HuggingFace dataset revision (optional, default: main)

AWS-specific (for production):
- `AWS_REGION`: AWS region
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

## Contributing

1. Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

2. Run tests before committing:
```bash
pytest
```

3. Follow the existing code style and conventions

## License

[Your License Here]

## Support

For issues and questions, please open an issue on the repository.
