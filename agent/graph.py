import os
import json
from typing import Optional, List
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Initialize LLMs
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

primary_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=os.environ.get("GROQ_API_KEY", "mock"))
fallback_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0, api_key=os.environ.get("GEMINI_API_KEY", "mock"))
llm = primary_llm.with_fallbacks([fallback_llm])

from .state import AgentState
from .mcp_client import mcp_session

class IntentExtraction(BaseModel):
    keyword: str = Field(description="A single broad keyword representing the food intent (e.g. 'chicken', 'pasta', 'beef', 'salad')")
    dietary_flags: List[str] = Field(description="list of strings like 'spicy', 'sweet', 'vegan', 'authentic', etc.")
    max_calories: Optional[int] = Field(description="Max calories inferred from intent (e.g. 'light', 'cutting', 'under 500' -> 500, 'diet' -> 400)")
    min_protein: Optional[int] = Field(description="Min protein inferred from intent (e.g. 'gains', 'gym', 'high protein' -> 30)")
    max_sodium: Optional[int] = Field(description="Max sodium inferred from intent (e.g. 'bloated', 'low sodium' -> 500)")

async def parse_intent(state: AgentState) -> AgentState:
    prompt = f"""Extract food and dietary intent from this user prompt: "{state['user_prompt']}"
    Translate fuzzy constraints into explicit numerical nutritional targets. 
    For example:
    - "I feel bloated" -> max_sodium = 500
    - "I'm on a cut" or "light snack" -> max_calories = 500
    - "I just worked out" -> min_protein = 30
    """
    try:
        structured_llm = llm.with_structured_output(IntentExtraction)
        result = await structured_llm.ainvoke(prompt)
        state["nutrition_hint"] = result.model_dump()
        state["raw_entities"] = state["nutrition_hint"]
    except Exception as e:
        print(f"Fallback intent parse due to: {e}")
        state["nutrition_hint"] = {"keyword": "snack", "dietary_flags": [], "max_calories": None, "min_protein": None, "max_sodium": None}
        state["raw_entities"] = state["nutrition_hint"]
    
    # Initialize some defaults
    state.setdefault("retry_count", 0)
    state.setdefault("rejected_reasons", [])
    
    return state

async def enrich_context(state: AgentState) -> AgentState:
    async with mcp_session() as session:
        # Pass dummy lat/lon for now or extract from state
        lat = state.get("lat", 40.7128)
        lon = state.get("lon", -74.0060)
        result = await session.call_tool(
            "get_weather_context", {"lat": lat, "lon": lon}
        )
        if result.content:
            state["weather"] = json.loads(result.content[0].text)
        else:
            state["weather"] = {"error": "No weather data"}
    return state

async def search_catalog(state: AgentState) -> AgentState:
    keyword = state["nutrition_hint"].get("keyword", "snack")
    
    if state.get("retry_count", 0) > 0 and state.get("rejected_reasons"):
        last_reason = state["rejected_reasons"][-1]
        if "no matches" in last_reason or "violate" in last_reason:
            keyword = "chicken" if keyword != "chicken" else "beef"
            state["nutrition_hint"]["keyword"] = keyword
            
    async with mcp_session() as session:
        result = await session.call_tool("search_dish_catalog", {"query": keyword})
        if result.content:
            data = json.loads(result.content[0].text)
            state["candidates"] = data.get("candidates", [])[:5]
        else:
            state["candidates"] = []
    return state

async def map_constraints(state: AgentState) -> AgentState:
    async with mcp_session() as session:
        for candidate in state.get("candidates", []):
            try:
                result = await session.call_tool(
                    "get_nutrition_info", {"query": candidate["name"]}
                )
                if result.content:
                    data = json.loads(result.content[0].text)
                    foods = data.get("candidates", [])
                    if foods:
                        food = foods[0]
                        nutrients = food.get("foodNutrients", [])
                        macros = {"calories": 0, "protein": 0, "sodium": 0}
                        for n in nutrients:
                            name = n.get("nutrientName", "").lower()
                            if "energy" in name: macros["calories"] = n.get("value", 0)
                            elif "protein" in name: macros["protein"] = n.get("value", 0)
                            elif "sodium" in name: macros["sodium"] = n.get("value", 0)
                        candidate["macros"] = macros
                    else:
                        candidate["macros"] = {"error": "No nutritional data found"}
            except Exception as e:
                candidate["macros"] = {"error": str(e)}
    return state

async def verify(state: AgentState) -> AgentState:
    if not state["candidates"]:
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["rejected_reasons"].append(
            f"no matches for '{state['nutrition_hint']['keyword']}', broadening search"
        )
        # Skip budget check if no candidates
        return state
        
    valid_candidates = []
    hint = state.get("nutrition_hint", {})
    max_cal = hint.get("max_calories")
    min_prot = hint.get("min_protein")
    max_sod = hint.get("max_sodium")
    
    for c in state["candidates"]:
        macros = c.get("macros", {})
        if "error" in macros: continue
        
        cal = macros.get("calories", 0)
        prot = macros.get("protein", 0)
        sod = macros.get("sodium", 0)
        
        # Drop if USDA data is missing (0 calories)
        if cal == 0: continue
        
        if max_cal and cal > max_cal: continue
        if min_prot and prot < min_prot: continue
        if max_sod and sod > max_sod: continue
        
        score = prot - (cal * 0.1) - (sod * 0.05)
        c["score"] = score
        valid_candidates.append(c)
        
    if not valid_candidates:
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["rejected_reasons"].append("Candidates violated nutritional constraints")
        state["candidates"] = []
        return state
        
    valid_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    state["candidates"] = valid_candidates
        
    # Budget Check
    if state["candidates"] and "error" not in state["candidates"][0]:
        async with mcp_session() as session:
            budget_result = await session.call_tool("check_wallet_balance", {"user_id": "user_123"})
            try:
                wallet_balance = float(budget_result.content[0].text)
                # Just mock a price check since TheMealDB has no prices
                item_price = 10.0 # Mock price
                if item_price > wallet_balance:
                    state["retry_count"] = state.get("retry_count", 0) + 1
                    state["rejected_reasons"].append("Selected item exceeds budget.")
                    state["candidates"] = [] # Force retry
            except:
                pass
                
    return state

def should_retry(state: AgentState) -> str:
    if not state["candidates"] and state.get("retry_count", 0) <= 2:
        return "search_catalog" # loop back to search_catalog
    return "checkout"

async def checkout(state: AgentState) -> AgentState:
    if state["candidates"] and "error" not in state["candidates"][0]:
        state["final_order"] = {
            "item": state["candidates"][0],
            "weather_context": state.get("weather"),
            "reasoning_trail": state.get("rejected_reasons"),
            "status": "Order placed successfully"
        }
    else:
        state["final_order"] = {"error": "No matching items found after retries."}
    return state

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("parse_intent", parse_intent)
    graph.add_node("enrich_context", enrich_context)
    graph.add_node("map_constraints", map_constraints)
    graph.add_node("search_catalog", search_catalog)
    graph.add_node("verify", verify)
    graph.add_node("checkout", checkout)

    graph.set_entry_point("parse_intent")
    graph.add_edge("parse_intent", "enrich_context")
    graph.add_edge("enrich_context", "search_catalog")
    graph.add_edge("search_catalog", "map_constraints")
    graph.add_edge("map_constraints", "verify")
    graph.add_conditional_edges(
        "verify",
        should_retry,
        {"search_catalog": "search_catalog", "checkout": "checkout"},
    )
    graph.add_edge("checkout", END)

    return graph.compile()
