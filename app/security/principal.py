from pydantic import BaseModel
from typing import Any


class Principal(BaseModel):
    sub: str
    username: str | None = None
    groups: list[str] = []
    scopes: list[str] = []
    claims: dict[str, Any] = {}
