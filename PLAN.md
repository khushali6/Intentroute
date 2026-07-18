# IntentRoute — An Agentic "Fuzzy Intent → Structured Order" Engine

*A portfolio project for the Airgrab (Software Engineer, AI/ML) application*

---

## 1. Why This Project (and not a generic chatbot)

Airgrab's whole bet is that people shouldn't have to *search and browse* — they should just *say what they want* and get it. That only works if there's a system that can turn a fuzzy human sentence into a structured, checkout-ready order, reliably, across edge cases.

Most applicants (especially freshers) will submit:
- A single-prompt LLM wrapper ("send query to GPT, return JSON")
- No state, no memory, no correction loop, no tool decoupling

This project is deliberately built to demonstrate the *opposite* — a real agentic architecture with:

- **Stateful, multi-step reasoning** (LangGraph) instead of one-shot prompting
- **Decoupled, swappable tools** (MCP) instead of hardcoded API calls glued into the prompt
- **A correction/retry loop** so bad results don't just get returned to the user
- **Production concerns** — streaming, observability, a real backend (FastAPI) — not just a notebook

Importantly, this is framed around a **different vertical and different example prompts** than Airgrab's own landing page, so it reads as *"I understood the underlying problem and built my own take on it"* rather than *"I copied your marketing copy into a repo."*

---

## 2. The Concept

**IntentRoute** is a chat agent for a fictional "ambient commerce" use case of your choosing — recommended: **a study/work-day snack & drink ordering assistant** (different vertical from food-delivery-for-mood, but same underlying hard problem: mapping vague human state → concrete catalog items).

Example prompts it should handle (intentionally distinct from Airgrab's own examples):

- *"I have back-to-back calls till 6, give me something I can eat one-handed"*
- *"I pulled an all-nighter, need something that'll actually keep me awake"*
- *"It's humid and I feel bloated, nothing heavy please"*
- *"Cheap but filling, payday's still 3 days away"*

These map to the same underlying capability Airgrab needs (context enrichment → constraint mapping → catalog search → verification loop) without lifting their exact phrasing.

---

## 3. System Architecture

```
[ Frontend: React chat + live agent-state panel ]
                │
                ▼
[ Backend: FastAPI (SSE/WebSocket /chat endpoint) ]
                │
                ▼
[ Agent Core: LangGraph state machine ]
                │
                ▼  (tool calls via Model Context Protocol)
        [ MCP Server ]
          ├── context_enrichment_tool   (real: Open-Meteo weather API, no key needed)
          ├── constraint_mapping_tool   (real: USDA FoodData Central nutrition API)
          ├── catalog_search_tool       (real: TheMealDB — live dish/ingredient catalog)
          └── budget_tool               (mock wallet balance — no public API exists for this; call it out as "would be a real payments service in production")
```

**Stack**
- **Backend:** FastAPI
- **Agent core:** LangGraph (Python)
- **Tool layer:** Official MCP Python SDK, exposing 4 independent tools
- **Frontend:** React (or Streamlit if you need to move faster) — chat on one side, live graph-state visualization on the other
- **Data sources:** Real free APIs (Open-Meteo, TheMealDB, USDA FoodData Central) instead of mock data — see Section 5.1 for keys/setup. Only the wallet/budget check stays mocked, since no public API for that exists.

---

## 4. The LangGraph Workflow

| Node | Purpose |
|---|---|
| **1. Intent Parse** | Extract raw entities/constraints from the free-text prompt |
| **2. Context Enrichment** | Call MCP tool(s) to pull in situational context (time, "busyness," weather) that the user didn't explicitly state |
| **3. Constraint Mapping** | Convert enriched context + raw intent into concrete filters (calories, prep time, spice level, budget) |
| **4. Catalog Search** | Query the mock catalog with the derived filters |
| **5. Verification / Guardrail** | Check results actually satisfy the original constraints; if not, loop back to Constraint Mapping with feedback |
| **6. Checkout Object** | Emit a structured JSON order ready for a (mock) payment step |

State object to track (this is the part that actually signals engineering maturity — call this out explicitly in your repo README):

```python
class AgentState(TypedDict):
    user_prompt: str
    raw_entities: dict
    context: dict          # from context_enrichment_tool
    constraints: dict       # from constraint_mapping_tool
    candidates: list[dict]  # from catalog_search_tool
    rejected_reasons: list[str]
    retry_count: int
    final_order: dict | None
```

---

## 5. MCP Server — Tool Definitions (Live APIs)

### 5.1 Setup — API keys needed

| Service | Key required? | Get it here |
|---|---|---|
| Open-Meteo | No | Nothing to sign up for — just call the endpoint |
| TheMealDB | No (use free test key `1`) | `https://www.themealdb.com/api.php` |
| USDA FoodData Central | Yes, free instant key | `https://fdc.nal.usda.gov/api-guide.html` — sign up, get key in seconds |

Store keys in a `.env` file (`USDA_API_KEY=...`) and load with `python-dotenv` — never hardcode them, and don't commit `.env` to your repo.

### 5.2 Tool implementations

```python
# tools.py (served via MCP Python SDK)
import requests
import os

USDA_API_KEY = os.environ["USDA_API_KEY"]


def context_enrichment_tool(lat: float, lon: float) -> dict:
    """Pull real current weather to infer situational context (hot/cold/rainy)."""
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": True},
        timeout=5,
    )
    resp.raise_for_status()
    weather = resp.json()["current_weather"]
    return {
        "temperature_c": weather["temperature"],
        "windspeed": weather["windspeed"],
        "weathercode": weather["weathercode"],  # map to condition (rain/clear/etc.)
    }


def constraint_mapping_tool(query: str) -> dict:
    """Look up real nutrition data for a food keyword to map vague phrases
    (e.g. 'keep me awake') to concrete nutrient filters (caffeine, protein)."""
    resp = requests.get(
        "https://api.nal.usda.gov/fdc/v1/foods/search",
        params={"api_key": USDA_API_KEY, "query": query, "pageSize": 5},
        timeout=5,
    )
    resp.raise_for_status()
    foods = resp.json().get("foods", [])
    return {"candidates": foods}


def catalog_search_tool(query: str) -> list[dict]:
    """Search a real, live dish catalog by name or main ingredient."""
    resp = requests.get(
        "https://www.themealdb.com/api/json/v1/1/search.php",
        params={"s": query},
        timeout=5,
    )
    resp.raise_for_status()
    meals = resp.json().get("meals") or []
    return [
        {"name": m["strMeal"], "category": m["strCategory"], "id": m["idMeal"]}
        for m in meals
    ]


def budget_tool(user_id: str) -> float:
    """No public API exists for personal wallet balances — mock this one,
    and note in your README it would call a real payments/wallet service
    (e.g. Razorpay, Stripe) in production."""
    return 250.0  # mocked ₹ balance
```

Keep each tool genuinely independent and testable on its own — that's the whole point of MCP over a hardcoded function call. Since three of the four now hit real live services, add basic error handling (timeouts, empty results) — this is also a good, honest talking point in your Loom video: "here's how I handle a live API returning nothing."

---

## 6. Build Plan (Weekend-Sized, ~7–8 hours total)

**Phase 1 — MCP Server (2–2.5 hrs)**
- Scaffold with the official MCP Python SDK
- Sign up for a free USDA FoodData Central key (instant)
- Wire up the 3 real API tools (Open-Meteo, TheMealDB, USDA) + 1 mocked budget tool
- Add basic error handling for empty results / timeouts from live APIs

**Phase 2 — LangGraph State Machine (2–3 hrs)**
- Define `AgentState`
- Build the 6 nodes above with conditional edges (the retry loop is the part worth showing off — cap it at 2–3 retries)

**Phase 3 — FastAPI + Streaming (1.5–2 hrs)**
- Single `/chat` endpoint using SSE or WebSocket
- Stream intermediate node outputs, not just the final answer

**Phase 4 — Frontend (1–1.5 hrs)**
- Chat pane + a live side-panel showing which node is currently active and what state looks like at each step
- This visualization is what makes non-technical founders *feel* the engineering, not just read about it

---

## 7. What to Put in the README

- One paragraph: the problem (ambiguous human intent → structured commerce action)
- Architecture diagram (the one above, or your own SVG)
- A short "Why LangGraph, why MCP" section — 2–3 sentences each, framed around maintainability and tool-swap-ability, not buzzwords
- 3–4 example conversations with screenshots or GIFs of the state panel
- A "what I'd add for production" section (real payments, real catalog, auth, rate limiting) — this signals seniority beyond your years of experience

---

## 8. The Outreach Note (keep it short)

Don't lead with "I built something like your product." Lead with the underlying engineering problem:

> Subject: A working prototype — ambiguous-intent → structured order routing
>
> Hi [Founder name], I've been thinking about the hard part of "describe and get" commerce — turning a vague human sentence into a reliable, structured order without a human in the loop. I built a small end-to-end prototype (LangGraph + MCP + FastAPI) to explore exactly that problem on a toy catalog. Repo + 45s walkthrough here: [link]. Happy to talk through the design decisions.

Attach a 45–60 second Loom: show one query that works cleanly, then one query that triggers the retry loop, then the final structured JSON order. That retry-loop demo is the single most convincing 10 seconds of the whole video.

---

## 9. Notes on Positioning Against 2 YOE vs. Freshers

Since the JD is explicitly asking for 1–2 years of experience (not freshers), you don't need to "beat freshers" — you already meet the bar on paper. This project's job is just to make the *AI/ML and system-design* parts of your experience visible fast, since a resume alone won't show off state machines or tool architecture. Keep the repo, README, and Loom tight — the goal is a 5-minute total review time for a busy founder, not an exhaustive system.
