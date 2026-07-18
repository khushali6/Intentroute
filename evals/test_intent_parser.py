import pytest
from agent.graph import parse_intent

# Mock a basic AgentState
def make_state(prompt: str):
    return {"user_prompt": prompt}

@pytest.mark.asyncio
async def test_parse_intent_cutting():
    state = make_state("I'm cutting and need a light chicken dish under 400 calories")
    new_state = await parse_intent(state)
    hint = new_state["nutrition_hint"]
    
    assert hint["keyword"].lower() == "chicken"
    assert hint["max_calories"] is not None
    assert hint["max_calories"] <= 500

@pytest.mark.asyncio
async def test_parse_intent_bloated():
    state = make_state("I feel bloated today, give me a soup")
    new_state = await parse_intent(state)
    hint = new_state["nutrition_hint"]
    
    assert "soup" in hint["keyword"].lower()
    assert hint["max_sodium"] is not None

@pytest.mark.asyncio
async def test_parse_intent_gains():
    state = make_state("I just worked out, I need a beef dish with massive gains")
    new_state = await parse_intent(state)
    hint = new_state["nutrition_hint"]
    
    assert hint["keyword"].lower() == "beef"
    assert hint["min_protein"] is not None
    assert hint["min_protein"] >= 20
