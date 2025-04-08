from pydantic import BaseModel
from typing import Literal


class Query(BaseModel):
    role: Literal["user", "assistant"]
    content: str
