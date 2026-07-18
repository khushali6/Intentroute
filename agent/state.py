from typing import TypedDict, Optional, Any


class AgentState(TypedDict):
    user_prompt: str
    lat: float
    lon: float
    weather: Optional[dict]
    nutrition_hint: Optional[dict]
    raw_entities: Optional[dict]
    current_step: Optional[str]
    candidates: list
    rejected_reasons: list
    retry_count: int
    final_order: Optional[dict]
