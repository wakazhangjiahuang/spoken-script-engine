"""Read-only stdio MCP server for a private spoken-script knowledge checkout."""
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from knowledge import REGISTRY, Snapshot

mcp = FastMCP("spoken-script-knowledge")
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
snapshot = Snapshot(
    Path(os.environ["SPOKEN_KB_CHECKOUT"]), os.environ.get("SPOKEN_KB_REGISTRY_REF", "HEAD"),
    registry_path=os.environ.get("SPOKEN_KB_REGISTRY_PATH", REGISTRY),
    project_scopes=[scope for scope in os.environ.get("SPOKEN_KB_AUTHORIZED_PROJECTS", "").split(",") if scope],
)


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def knowledge_status() -> dict[str, Any]:
    """Verify the pinned manifest and indexed files and return the immutable version and evidence counts."""
    return snapshot.status()


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def search_knowledge(query: str, platform: str = "", domain: str = "", kind: str = "",
                     status: str = "", limit: int = 6, adapter_id: str = "", industry_tag: str = "",
                     business_model: str = "", buyer_role: str = "", content_goal: str = "",
                     project_scope: str = "") -> dict[str, Any]:
    """Search the pinned registry. Query the selected adapter and shared methods separately."""
    return snapshot.search(query, platform, domain, kind, status, limit, adapter_id=adapter_id,
                           industry_tag=industry_tag, business_model=business_model,
                           buyer_role=buyer_role, content_goal=content_goal, project_scope=project_scope)


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def read_knowledge(asset_id: str, offset: int = 0, project_scope: str = "",
                   include_history: bool = False) -> dict[str, Any]:
    """Read one entry with citation, source locator and next_offset."""
    return snapshot.read(asset_id, offset, project_scope=project_scope, include_history=include_history)


if __name__ == "__main__":
    mcp.run(transport="stdio")
