"""Read-only stdio MCP server for a private spoken-script knowledge checkout."""
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from knowledge import Snapshot

mcp = FastMCP("spoken-script-knowledge")
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
snapshot = Snapshot(Path(os.environ["SPOKEN_KB_CHECKOUT"]), os.environ.get("SPOKEN_KB_REGISTRY_REF", "HEAD"))


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def knowledge_status() -> dict[str, Any]:
    """Verify the pinned manifest and indexed files and return the immutable version and evidence counts."""
    return snapshot.status()


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def search_knowledge(query: str, platform: str = "", domain: str = "", kind: str = "",
                     status: str = "", limit: int = 6) -> dict[str, Any]:
    """Find relevant guides, platform rules or samples. Use explicit platform, domain or evidence filters when possible.

    Platform: xiaohongshu, douyin, channels, shared. Domain: ai_video, illustration, shared.
    Historical archives require kind=archive or status=historical_only.
    """
    return snapshot.search(query, platform, domain, kind, status, limit)


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def read_knowledge(asset_id: str, offset: int = 0) -> dict[str, Any]:
    """Read an asset by returned ID, with source locator, evidence status and next_offset for longer entries."""
    return snapshot.read(asset_id, offset)


if __name__ == "__main__":
    mcp.run(transport="stdio")
