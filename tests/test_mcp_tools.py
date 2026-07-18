import pytest
import responses
from mcp_server.server import get_weather_context, search_dish_catalog, get_nutrition_info

@responses.activate
def test_get_weather_context():
    responses.add(
        responses.GET,
        "https://api.open-meteo.com/v1/forecast",
        json={"current_weather": {"temperature": 25.0, "windspeed": 10.0, "weathercode": 0}},
        status=200
    )
    result = get_weather_context(40.71, -74.00)
    assert result["temperature_c"] == 25.0
    assert result["windspeed"] == 10.0

@responses.activate
def test_search_dish_catalog():
    responses.add(
        responses.GET,
        "https://www.themealdb.com/api/json/v1/1/search.php",
        json={"meals": [{"strMeal": "Test Chicken", "strCategory": "Chicken", "idMeal": "123"}]},
        status=200
    )
    result = search_dish_catalog("chicken")
    assert "candidates" in result
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["name"] == "Test Chicken"

@responses.activate
def test_search_dish_catalog_empty():
    responses.add(
        responses.GET,
        "https://www.themealdb.com/api/json/v1/1/search.php",
        json={"meals": None},
        status=200
    )
    result = search_dish_catalog("nonexistent")
    assert result == {"candidates": []}

@responses.activate
def test_get_nutrition_info():
    responses.add(
        responses.GET,
        "https://api.nal.usda.gov/fdc/v1/foods/search",
        json={"foods": [{"description": "Test Food", "foodNutrients": []}]},
        status=200
    )
    result = get_nutrition_info("test")
    assert "candidates" in result
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["description"] == "Test Food"
