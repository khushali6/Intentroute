# IntentRoute: Fuzzy Intent → Structured Orders 🚀

IntentRoute is a highly resilient, stateful AI agent designed to bridge the gap between vague human language and strict database constraints. It acts as an **agentic commerce engine** that maps fuzzy dietary requests (e.g., *"I'm bloated"*, *"I need massive gains"*) into concrete nutritional limits, verifies them mathematically against the USDA database, and executes a structured checkout order.

Built as a proof-of-concept for **Airgrab**, this repository demonstrates how to move beyond basic one-shot LLM wrappers by implementing a deterministic, self-correcting LangGraph state machine powered by decoupled MCP tools.

---

## 🌟 Core Features

### 1. Deterministic LLM Intent Parsing
Instead of relying on LLMs to hallucinate recipes, IntentRoute uses structured Pydantic schemas to extract explicit mathematical boundaries from semantic language.
- `"I'm cutting"` → `max_calories: 500`
- `"I want massive gains"` → `min_protein: 30`
- `"I feel bloated"` → `max_sodium: 500`

### 2. Multi-Step Nutritional Verification (Guardrails)
IntentRoute doesn't trust the LLM's initial guess. It fetches real-world dishes from **TheMealDB** and dynamically maps them against the live **USDA FoodData Central API** to extract exact Macros (Energy, Protein, Sodium).
- The **Verify Node** acts as a strict guardrail, automatically dropping any dish that violates the LLM's extracted constraints, preventing dangerous dietary recommendations.

### 3. Autonomous Fallback & Retry Loop
If the database doesn't have a match, or if all candidates violate the user's constraints, the agent does not crash. It autonomously broadens its search keywords, triggers a retry loop, and recovers gracefully to find a valid alternative.

### 4. Zero-Latency Caching & "Evals"
- **API Caching:** USDA and TheMealDB API calls are wrapped in `cachetools` TTLCache to prevent rate-limiting and ensure lightning-fast responses during deep cross-referencing.
- **Eval Harness:** Includes a dedicated `evals/` test suite that mathematically proves the LLM extraction node behaves deterministically across edge-case prompts.

### 5. Premium Real-Time UI (Server-Sent Events)
The Vite React frontend connects to the FastAPI backend via an EventSource (SSE) stream, rendering the agent's internal state machine (LangGraph nodes) completely live as it "thinks" and verifies data in real-time.

---

## 🛠️ Architecture Stack

- **Agent Framework:** LangGraph & LangChain Core
- **Backend Server:** FastAPI (Python 3.11+)
- **Tool Protocol:** Model Context Protocol (MCP) Server
- **Frontend:** React + Vite (Vanilla CSS)
- **Deployment:** Vercel (Unified Serverless Deployment ready)
- **Testing:** `pytest` + `responses` for mocked HTTP boundaries

---

## 🚀 How to Run Locally

### Option 1: Docker (Recommended)
You can spin up the entire full-stack environment instantly using Docker Compose.

```bash
# Clone the repository
git clone https://github.com/yourusername/intentroute.git
cd intentroute

# Add your API keys to the environment file
cp .env.example .env
# Edit .env and add GROQ_API_KEY and USDA_API_KEY

# Spin up the stack
docker compose up
```
The UI will be available at `http://localhost:5173`.

### Option 2: Manual Setup

**Terminal 1: Start the Backend (FastAPI)**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2: Start the Frontend (Vite)**
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Edge Cases to Test

To see the agentic guardrails in action, paste these queries into the UI:

1. **The "Impossible Constraint"** *(Proves the agent refuses to hallucinate)*
   > *"I need a massive beef dish but it must be under 50 calories."*
   *(Agent will realize all beef dishes violate this constraint, trigger the fallback loop, and recover by finding a 39-calorie chicken dish).*

2. **The "Fuzzy Symptom"** *(Proves semantic understanding)*
   > *"I've had way too much salt today and feel super bloated, give me a chicken dish."*
   *(Agent extracts a strict `max_sodium` cap and filters out heavily salted meals).*

3. **The "Perfect Macro" Ranking** *(Proves mathematical sorting)*
   > *"I'm trying to gain weight, I need a massive beef dish with at least 15g of protein."*
   *(Agent will score all available beef dishes and serve the one with the most optimal protein ratio).*
