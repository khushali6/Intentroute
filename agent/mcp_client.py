"""
Spawns the IntentRoute MCP server as a subprocess and opens a client
session against it over stdio. This is the actual decoupling that MCP
buys you: the agent never imports the tool functions directly -- it only
knows tool *names* and JSON schemas, so the tool implementations could
be swapped or moved to a remote server without touching agent/graph.py.
"""

import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import os

env = os.environ.copy()
env["PYTHONPATH"] = os.pathsep.join(sys.path)

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-m", "mcp_server.server"],
    env=env
)


@asynccontextmanager
async def mcp_session():
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
