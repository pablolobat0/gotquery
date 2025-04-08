import os
from anthropic.types import MessageParam
from fastapi import APIRouter, status
from app.schemas.query import Query
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-3-7-sonnet-20250219"

API_KEY = os.getenv("API_KEY")

query_router = APIRouter()


@query_router.post("/query", response_model=list[Query], status_code=status.HTTP_200_OK)
async def get_response(query: Query):
    messages = [MessageParam(role=query.role, content=query.content)]

    response = Anthropic(api_key=API_KEY).messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=messages,
    )

    final_text: list[Query] = []
    assistant_message_content = []

    for content in response.content:
        final_text.append(Query(role="assistant", content=content.text))
        assistant_message_content.append(content.text)

    return final_text
