from contextlib import AsyncExitStack
import os
from anthropic.types import (
    MessageParam,
    TextBlockParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUnionParam,
    ToolUseBlockParam,
)
from fastapi import APIRouter, status
from app.schemas.query import Query
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import StdioServerParameters, ClientSession, Tool, stdio_client

load_dotenv()

MODEL = "claude-3-7-sonnet-20250219"

API_KEY = os.getenv("API_KEY")

query_router = APIRouter()


@query_router.post("/query", response_model=list[Query], status_code=status.HTTP_200_OK)
async def get_response(query: Query):
    messages = [MessageParam(role=query.role, content=query.content)]

    server_params = StdioServerParameters(
        command="python", args=["mcp_server/tools.py"], env=None
    )

    final_text = []

    async with AsyncExitStack() as stack:
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()

        # List available tools
        response = await session.list_tools()
        tools: list[Tool] = response.tools

        tools_conv: list[ToolUnionParam] = []
        for tool in tools:
            description = ""
            if tool.description is not None:
                description = tool.description

            converted_tool: ToolUnionParam = ToolParam(
                name=tool.name,
                description=description,
                input_schema=tool.inputSchema,
            )

            tools_conv.append(converted_tool)

        llm = Anthropic(api_key=API_KEY)
        response = llm.messages.create(
            model=MODEL, max_tokens=1000, messages=messages, tools=tools_conv
        )

        assistant_message_content = []

        for content in response.content:
            if content.type == "text":
                final_text.append(Query(role="assistant", content=content.text))
                assistant_message_content.append(content.text)
            elif content.type == "tool_use":
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await session.call_tool(tool_name, tool_args)
                final_text.append(
                    Query(
                        role="assistant",
                        content=f"[Calling tool {tool_name} with args {tool_args}]",
                    )
                )

                messages.append(
                    MessageParam(
                        role="assistant",
                        content=[
                            ToolUseBlockParam(
                                id=content.id,
                                type=content.type,
                                name=content.name,
                                input=content.input,
                            )
                        ],
                    )
                )

                converted_content: list[TextBlockParam] = [
                    TextBlockParam(type="text", text=tc.text) for tc in result.content
                ]

                messages.append(
                    MessageParam(
                        role="user",
                        content=[
                            ToolResultBlockParam(
                                tool_use_id=content.id,
                                type="tool_result",
                                content=converted_content,
                            ),
                        ],
                    ),
                )

                # Get next response from Claude
                response = llm.messages.create(
                    model=MODEL, max_tokens=1000, messages=messages, tools=tools_conv
                )

                print(response)

                if response.type == "message":
                    final_text.append(
                        Query(role="assistant", content=response.content[0].text)
                    )
                else:
                    final_text.append(
                        Query(
                            role="assistant",
                            content="[Respuesta inesperada al usar la herramienta]",
                        )
                    )

        return final_text
