import asyncio
import json
import httpx

async def run_test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Sending request for beef...")
        prompt = "I just finished a heavy gym session, give me a beef dish with massive gains"
        async with client.stream("GET", f"http://127.0.0.1:8000/chat?prompt={prompt}") as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "{}": continue
                    parsed = json.loads(data)
                    print(f"Step: {parsed.get('node')}")
                    if parsed.get('node') == "parse_intent":
                        print("INTENT:", json.dumps(parsed.get('state', {}).get('nutrition_hint', {}), indent=2))
                    if parsed.get('node') == "map_constraints":
                        print("CANDIDATES:", json.dumps(parsed.get('state', {}).get('candidates', []), indent=2))
                    if parsed.get('node') == "verify":
                        print("REJECTED REASONS:", parsed.get('state', {}).get('rejected_reasons', []))

if __name__ == "__main__":
    asyncio.run(run_test())
