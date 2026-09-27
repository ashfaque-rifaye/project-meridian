"""
MCP smoke test: launches the Meridian MCP server over stdio exactly like Bob
does, lists its tools and calls two of them.

    python tests/mcp_smoke.py
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


async def main() -> int:
    # Import the SDK before the project root is on sys.path (a local folder named `mcp` would shadow it).
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "mcp-server" / "meridian_mcp.py")],
                                   cwd=str(ROOT))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"{len(names)} tools:", ", ".join(names))
            result = await session.call_tool("get_untested_edges", {"environment": "prod"})
            text = result.content[0].text if result.content else json.dumps(result.structuredContent)
            data = json.loads(text)
            edges = data.get("data") or data.get("result", {}).get("data")
            print("untested in prod:", [(e["edge_id"], e["state"]) for e in edges])
            result = await session.call_tool("get_first_divergence", {"environment": "prod"})
            text = result.content[0].text
            print("first divergence:", json.loads(text)["data"]["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
