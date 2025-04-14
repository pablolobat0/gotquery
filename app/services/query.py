from contextlib import AsyncExitStack
import os
from anthropic.types import (
    Message,
    MessageParam,
    TextBlockParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUnionParam,
    ToolUseBlock,
    ToolUseBlockParam,
)
from app.schemas.query import Query
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import StdioServerParameters, ClientSession, Tool, stdio_client

load_dotenv()

MODEL = "claude-3-7-sonnet-20250219"

API_KEY = os.getenv("API_KEY")


async def get_query_response(query: Query) -> list[Query]:
    messages = [MessageParam(role=query.role, content=query.content)]

    server_params = StdioServerParameters(
        command="python", args=["mcp_server/tools.py"], env=None
    )

    final_text = []

    async with AsyncExitStack() as stack:
        session = await create_client_session(stack, server_params)

        tools = await get_tools(session)

        client = Anthropic(api_key=API_KEY)
        response = send_message_to_llm(client, messages, tools)

        for content in response.content:
            if content.type == "text":
                final_text.append(Query(role="assistant", content=content.text))
            elif content.type == "tool_use":
                response = await use_tool(messages, content, session, client, tools)

                final_text.append(manage_tool_use_response(response))

    return final_text


async def create_client_session(
    stack: AsyncExitStack, server_params: StdioServerParameters
) -> ClientSession:
    stdio_transport = await stack.enter_async_context(stdio_client(server_params))
    stdio, write = stdio_transport
    session = await stack.enter_async_context(ClientSession(stdio, write))
    await session.initialize()

    return session


async def get_tools(session: ClientSession) -> list[ToolUnionParam]:
    response = await session.list_tools()
    tools: list[Tool] = response.tools

    tools_anthropic_format: list[ToolUnionParam] = []

    # Convert tools to Anthropic format
    for tool in tools:
        description = ""
        if tool.description is not None:
            description = tool.description

        converted_tool: ToolUnionParam = ToolParam(
            name=tool.name,
            description=description,
            input_schema=tool.inputSchema,
        )

        tools_anthropic_format.append(converted_tool)

    return tools_anthropic_format


def send_message_to_llm(
    client: Anthropic, messages: list[MessageParam], tools: list[ToolUnionParam]
) -> Message:
    return client.messages.create(
        model=MODEL, max_tokens=1000, messages=messages, tools=tools
    )


async def use_tool(
    messages: list[MessageParam],
    content: ToolUseBlock,
    session: ClientSession,
    client: Anthropic,
    tools: list[ToolUnionParam],
) -> Message:
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

    # Execute tool call
    result = await session.call_tool(content.name, content.input)

    # Convert to Anthropic format
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

    return send_message_to_llm(client, messages, tools)


def manage_tool_use_response(response) -> Query:
    if response.type == "message":
        return Query(role="assistant", content=response.content[0].text)
    else:
        return Query(
            role="assistant",
            content="Respuesta inesperada al usar la herramienta",
        )
