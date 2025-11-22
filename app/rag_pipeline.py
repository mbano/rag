from langchain.chat_models import init_chat_model
from langchain_cohere import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START
from app.utils.artifacts import ensure_corpus_assets
from app.utils.docs import load_docs
from app.utils.text import clean_tokens
from app.utils.prompts import get_chat_prompt_template
from app.config import RagConfig
from dotenv import load_dotenv
import json
import os
import time

# local fallback
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO")
HF_REVISION = os.getenv("HF_DATASET_REVISION", "main")

faiss_dir, doc_dir = ensure_corpus_assets(
    repo_id=HF_DATASET_REPO,
    revision=HF_REVISION,
    want_sources=True,
)


#  TODO: generalize to other vector stores
def _build_vector_store_from_manifest() -> FAISS:
    """
    Load FAISS index from disk using the manifest.json to get the embedding model.
    This keeps the embedding model in sync with the index, independent of config.
    """

    with open(faiss_dir / "manifest.json", "r") as f:
        manifest = json.load(f)

    embedding_model = manifest["embedding_model"]
    embeddings = OpenAIEmbeddings(model=embedding_model)

    vector_store = FAISS.load_local(
        str(faiss_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    return vector_store


def _build_retriever(
    config: RagConfig,
) -> ContextualCompressionRetriever | EnsembleRetriever:
    """
    Build the hybrid retriever (dense + sparse ensemble, optionally wrapped with a reranker)
    based on the retrieve-node section of the config.
    """

    retr_cfg = config.nodes.retrieve
    vector_store = _build_vector_store_from_manifest()
    #  TODO: build dict of search_kwargs manually
    dense_retriever = vector_store.as_retriever(search_kwargs=retr_cfg.dense_params)

    if retr_cfg.sparse_type.lower() != "bm25":
        raise ValueError(f"Unsupported sparse retriever type: {retr_cfg.sparse_type}")

    docs = load_docs(doc_dir)
    sparse_retriever = BM25Retriever.from_documents(
        docs,
        **retr_cfg.sparse_params,
        preprocess_func=clean_tokens,
    )

    hybrid_retriever = EnsembleRetriever(
        retrievers=[dense_retriever, sparse_retriever],
        weights=retr_cfg.ensemble_weights,
    )

    if retr_cfg.reranker_type.lower() == "cohere":
        reranker = CohereRerank(**retr_cfg.reranker_params)
        rerank_retriever = ContextualCompressionRetriever(
            base_compressor=reranker,
            base_retriever=hybrid_retriever,
        )
        return rerank_retriever

    if retr_cfg.reranker_type.lower() in ("none", "", "null"):
        return hybrid_retriever

    raise ValueError(f"Unsupported reranker type: {retr_cfg.reranker_type}")


def _build_llms(config: RagConfig):
    """
    Construct the LLMs for the analyze_query and generate nodes from config presets.
    Returns (query_analysis_llm, generate_llm).
    """

    aq_cfg = config.nodes.analyze_query
    aq_llm = config.llms[aq_cfg.llm_key]
    query_analysis_llm = init_chat_model(
        model=aq_llm.model_name,
        model_provider=aq_llm.model_provider,
        temperature=aq_cfg.temperature,
    )

    gen_cfg = config.nodes.generate
    gen_llm = config.llms[gen_cfg.llm_key]
    generate_llm = init_chat_model(
        model=gen_llm.model_name,
        model_provider=gen_llm.model_provider,
        temperature=gen_cfg.temperature,
    )

    return query_analysis_llm, generate_llm


def _build_prompts(config: RagConfig):
    """
    Load ChatPromptTemplates for the analyze_query and generate nodes
    using filenames from the config and get_chat_prompt_template().
    """

    aq_cfg = config.nodes.analyze_query
    analyze_query_prompt = (
        get_chat_prompt_template(aq_cfg.prompt) if aq_cfg.prompt is not None else None
    )

    gen_cfg = config.nodes.generate
    generate_prompt = (
        get_chat_prompt_template(gen_cfg.prompt) if gen_cfg.prompt is not None else None
    )

    return analyze_query_prompt, generate_prompt


class Search(TypedDict):
    """Search query"""

    query: Annotated[str, ..., "Search query to run."]


class State(TypedDict):
    question: str
    query: Search
    contexts: list[Document]
    answer: str
    metadata: dict


def build_graph(config: RagConfig, eval_mode: bool = False):
    if eval_mode:
        time.sleep(8)  #  prevent rate-limiting from Cohere when evaluating

    query_analysis_llm, generate_llm = _build_llms(config)
    analyze_query_prompt, generate_prompt = _build_prompts(config)
    retriever = _build_retriever(config)

    def analyze_query(state: State):
        structured_llm = query_analysis_llm.with_structured_output(Search)
        if analyze_query_prompt is not None:
            messages = analyze_query_prompt.invoke({"question": state["question"]})
            query = structured_llm.invoke(messages)
        else:
            query = structured_llm.invoke(state["question"])

        return {"query": query}

    def retrieve(state: State):
        query = state["query"]
        retrieved_docs = retriever.invoke(query["query"])

        return {"contexts": retrieved_docs}

    def generate(state: State):
        context = "".join(doc.page_content + " " for doc in state["contexts"])
        messages = generate_prompt.invoke(
            {"question": state["question"], "context": context}
        )
        response = generate_llm.invoke(messages)
        metadata = {"model_name": response.response_metadata["model_name"]}
        answer = {"answer": response.content, "metadata": metadata}

        return answer

    graph_builder = StateGraph(State).add_sequence([analyze_query, retrieve, generate])
    graph_builder.add_edge(START, "analyze_query")
    graph = graph_builder.compile()

    return graph


#  TODO: add download/sync with vector stores
