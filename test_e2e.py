import asyncio
import json
import httpx

async def run_test():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Prompt: "I'm cutting and need a light snack"
        print("Sending request...")
        async with client.stream("GET", "http://127.0.0.1:8000/chat?prompt=I'm%20cutting%20and%20need%20a%20light%20chicken%20dish") as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "{}": continue
                    parsed = json.loads(data)
                    print(f"Step: {parsed.get('node')}")
                    
                    if parsed.get('node') == "checkout":
                        print("FINAL CHECKOUT:")
                        print(json.dumps(parsed.get('state', {}).get('final_order', {}), indent=2))

if __name__ == "__main__":
    asyncio.run(run_test())
