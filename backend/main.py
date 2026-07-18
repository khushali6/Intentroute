"""
FastAPI backend for IntentRoute.

Run with:
    uvicorn backend.main:app --reload --port 8000

Then GET http://localhost:8000/chat?prompt=... (see frontend/index.html
for a working example that consumes the SSE stream).
"""

import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from agent.graph import build_graph

app = FastAPI(title="IntentRoute")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/chat")
async def chat(prompt: str, lat: float = 12.9716, lon: float = 77.5946):
    """
    Streams each LangGraph node's output as it completes, using Server-Sent
    Events, so the frontend can show the agent's state machine moving live.
    Default lat/lon is Bengaluru -- pass your own to test other locations.
    """
    initial_state = {
        "user_prompt": prompt,
        "lat": lat,
        "lon": lon,
        "weather": None,
        "nutrition_hint": None,
        "candidates": [],
        "rejected_reasons": [],
        "retry_count": 0,
        "final_order": None,
    }

    async def event_stream():
        async for event in graph.astream(initial_state):
            node_name, node_state = next(iter(event.items()))
            payload = {"node": node_name, "state": node_state}
            yield f"data: {json.dumps(payload, default=str)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
