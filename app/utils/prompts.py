from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_PATH = PROJECT_ROOT / "prompts"


def get_chat_prompt_template(prompt_filename: str) -> ChatPromptTemplate:
    path = PROMPTS_PATH / prompt_filename
    text = path.read_text(encoding="utf-8")
    prompt = ChatPromptTemplate.from_template(text)

    return prompt
