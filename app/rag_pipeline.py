from langchain_unstructured import UnstructuredLoader
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chat_models import init_chat_model
from langchain import hub
from langchain_core.documents import Document
from typing_extensions import List, TypedDict, Annotated
from langgraph.graph import StateGraph, START
from dotenv import load_dotenv
import os

# local fallback
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")

print("OpenAI key loaded:", bool(OPENAI_API_KEY))
print("LangSmith key loaded:", bool(LANGSMITH_API_KEY))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
file_path = DATA_DIR / "lancet_eat_2025.pdf"  # TODO: pull from query/other endpoint

loader = UnstructuredLoader(
    file_path=file_path,
    strategy="hi_res",
    infer_table_structure=True,
)

docs = []

for doc in loader.lazy_load():
    docs.append(doc)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
    separators=["\n\n", "\n", ".", "!", "?", " ", ""],
)

chunks = text_splitter.split_documents(docs)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large"
)  # TODO: pull model from config
vector_store = FAISS.from_documents(chunks, embeddings)

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
        page_number = doc.metadata.get("page_number", "N/A")
        text = doc.page_content
        sources.append(f"Source: page {page_number}/nText:{text}\n\n")

    flattened_sources = "".join(source for source in sources)

    return {"answer": response.content + "\n\n" + flattened_sources}


graph_builder = StateGraph(State).add_sequence([analyze_query, retrieve, generate])
graph_builder.add_edge(START, "analyze_query")
graph = graph_builder.compile()


def answer_question(question: str):
    result = graph.invoke({"question": question})

    return {"answer": result["answer"]}
