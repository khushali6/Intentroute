"""
IntentRoute MCP Server
-----------------------
Exposes 4 tools over the Model Context Protocol:

  - get_weather_context   -> Open-Meteo   (free, no API key)
  - get_nutrition_info    -> USDA FoodData Central (free API key)
  - search_dish_catalog   -> TheMealDB    (free, no API key)
  - check_wallet_balance  -> mocked (no public API exists for personal wallets)

Run standalone for testing:
    python -m mcp_server.server
"""

import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from cachetools import cached, TTLCache

load_dotenv()
USDA_API_KEY = os.environ.get("USDA_API_KEY", "")

mcp = FastMCP("intentroute-tools")

# Cache setups (1 hour TTL)
weather_cache = TTLCache(maxsize=100, ttl=3600)
nutrition_cache = TTLCache(maxsize=1000, ttl=3600)
catalog_cache = TTLCache(maxsize=1000, ttl=3600)

@mcp.tool()
@cached(cache=weather_cache)
def get_weather_context(lat: float, lon: float) -> dict:
    """Pull real current weather to infer situational context (hot/cold/rainy)."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current_weather": True},
            timeout=5,
        )
        resp.raise_for_status()
        weather = resp.json().get("current_weather", {})
        if not weather:
            return {"error": "Empty weather data from Open-Meteo."}
            
        return {
            "temperature_c": weather.get("temperature"),
            "windspeed": weather.get("windspeed"),
            "weathercode": weather.get("weathercode"),
        }
    except requests.RequestException as e:
        return {"error": f"Failed to reach Open-Meteo: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
@cached(cache=nutrition_cache)
def get_nutrition_info(query: str) -> dict:
    """Look up real nutrition data for a food keyword to map vague phrases
    (e.g. 'keep me awake') to concrete nutrient filters (caffeine, protein)."""
    if not USDA_API_KEY:
        return {"error": "USDA_API_KEY not set in .env", "candidates": []}
    try:
        resp = requests.get(
            "https://api.nal.usda.gov/fdc/v1/foods/search",
            params={"api_key": USDA_API_KEY, "query": query, "pageSize": 5},
            timeout=5,
        )
        resp.raise_for_status()
        foods = resp.json().get("foods", [])
        return {"candidates": foods}
    except requests.RequestException as e:
        return {"error": f"Failed to reach USDA API: {str(e)}", "candidates": []}
    except Exception as e:
        return {"error": str(e), "candidates": []}

@mcp.tool()
@cached(cache=catalog_cache)
def search_dish_catalog(query: str) -> dict:
    """Search a real, live dish catalog by name or main ingredient."""
    try:
        resp = requests.get(
            "https://www.themealdb.com/api/json/v1/1/search.php",
            params={"s": query},
            timeout=5,
        )
        resp.raise_for_status()
        meals = resp.json().get("meals") or []
        if not meals:
            return {"candidates": []} # No results found
            
        return {"candidates": [
            {"name": m["strMeal"], "category": m["strCategory"], "id": m["idMeal"]}
            for m in meals
        ]}
    except requests.RequestException as e:
        return {"error": f"Failed to reach TheMealDB API: {str(e)}", "candidates": []}
    except Exception as e:
        return {"error": str(e), "candidates": []}

@mcp.tool()
def check_wallet_balance(user_id: str) -> float:
    """No public API exists for personal wallet balances — mock this one,
    and note in your README it would call a real payments/wallet service
    (e.g. Razorpay, Stripe) in production."""
    return 250.0

if __name__ == "__main__":
    mcp.run()
