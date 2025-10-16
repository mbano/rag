from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chat_models import init_chat_model
from langchain import hub
from langchain_core.documents import Document
from typing_extensions import List, TypedDict, Annotated
from langgraph.graph import StateGraph, START
from utils.artifacts import ensure_corpus_assets
from dotenv import load_dotenv
import json
import os

# local fallback
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO")
HF_REVISION = os.getenv("HF_DATASET_REVISION", "main")
RAG_CORPUS = os.getenv("RAG_CORPUS", "lancet_eat_2025")


print("OpenAI key loaded:", bool(OPENAI_API_KEY))
print("LangSmith key loaded:", bool(LANGSMITH_API_KEY))


#  TODO: remove hard-coding
# ART_DIR = (
#     Path(__file__).resolve().parents[1] / "artifacts" / "faiss" / "lancet_eat_2025"
# )

faiss_dir = ensure_corpus_assets(
    repo_id=HF_DATASET_REPO,
    revision=HF_REVISION,
    want_pdf=True,
)

with open(faiss_dir / "manifest.json", "r") as f:
    manifest = json.load(f)

embedding_model = manifest["embedding_model"]
embeddings = OpenAIEmbeddings(model=embedding_model)

vector_store = FAISS.load_local(
    str(faiss_dir),
    embeddings,
    allow_dangerous_deserialization=True,
)

prompt = hub.pull("rlm/rag-prompt")  # TODO: consider building own, pull from config
llm = init_chat_model("gpt-4o-mini", model_provider="openai")  # TODO: pull from config


class Search(TypedDict):
    """Search query"""

    query: Annotated[str, ..., "Search query to run."]


class State(TypedDict):
    question: str
    query: Search
    context: List[Document]
    answer: str


def analyze_query(state: State):
    structured_llm = llm.with_structured_output(Search)
    query = structured_llm.invoke(state["question"])

    return {"query": query}


def retrieve(state: State):
    query = state["query"]
    retrieved_docs = vector_store.similarity_search(
        query["query"]
    )  # TODO: pull k from config

    return {"context": retrieved_docs}


def generate(state: State):
    context = "".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": context})
    response = llm.invoke(messages)

    sources = []
    for doc in state["context"]:
        file_name = doc.metadata.get("filename", "N/A")
        page_number = doc.metadata.get("page_number", "N/A")
        text = doc.page_content
        sources.append(
            f"Source: file name: {file_name}/npage {page_number}/nText:{text}\n\n"
        )

    flattened_sources = "".join(source for source in sources)

    return {"answer": response.content + "\n\n" + flattened_sources}


graph_builder = StateGraph(State).add_sequence([analyze_query, retrieve, generate])
graph_builder.add_edge(START, "analyze_query")
graph = graph_builder.compile()


def answer_question(question: str):
    result = graph.invoke({"question": question})

    return {"answer": result["answer"]}
