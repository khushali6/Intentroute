import asyncio
from agent.mcp_client import mcp_session

async def main():
    async with mcp_session() as session:
        res = await session.call_tool("search_dish_catalog", {"query": "chicken"})
        print(res)

asyncio.run(main())
