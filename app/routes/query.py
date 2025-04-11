from contextlib import AsyncExitStack
import os
from anthropic.types import MessageParam
from fastapi import APIRouter, status
from app.schemas.query import Query
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import StdioServerParameters, ClientSession, stdio_client

load_dotenv()

MODEL = "claude-3-7-sonnet-20250219"

API_KEY = os.getenv("API_KEY")

query_router = APIRouter()


@query_router.post("/query", response_model=list[Query], status_code=status.HTTP_200_OK)
async def get_response(query: Query):
    messages = [MessageParam(role=query.role, content=query.content)]

    server_params = StdioServerParameters(command="python", args["../mcp/tools.py"], env=None)

    exit = AsyncExitStack()

    stdio_transport = await exit.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await exit(ClientSession(stdio, write))

    await session.initialize()

    # List available tools
    response = await session.list_tools()
    tools = response.tools


    response = Anthropic(api_key=API_KEY).messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=messages,
        tools=tools
    )

    final_text: list[Query] = []
    assistant_message_content = []

    for content in response.content:
        if content.type =="text":
            final_text.append(Query(role="assistant", content=content.text))
            assistant_message_content.append(content.text)
        elif content.type == "tool_use":
            tool_name = content.name
            tool_args = content.input

            # Execute tool call
            result = await session.call_tool(tool_name, tool_args)
            final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

            assistant_message_content.append(content)
            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    }
                ]
            })

            # Get next response from Claude
            response = Anthropic(api_key=API_KEY).messages.create(
                model=MODEL,
                max_tokens=1000,
                messages=messages,
                tools=tools
            )

            final_text.append(response.content[0].text)

    return final_text
