from mcp.server.fastmcp import FastMCP
from app.db.crud import get_subtititle_by_query

# Initialize FastMCP server
mcp = FastMCP("got")

@mcp.tool()
def get_subtitles(query: str):
    """Get subtitles related to a query.

    Args:
        query: User text.
    """
    return get_subtititle_by_query(query)
