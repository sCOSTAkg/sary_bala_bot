import numexpr
from duckduckgo_search import DDGS
import httpx
import os
import json

# --- Инструменты ---

def search_internet(query: str):
    """Ищет информацию в интернете (DuckDuckGo). Полезно для актуальных новостей."""
    try:
        # duckduckgo-search 6.0+ возвращает список словарей
        # Используем синхронный API
        results = DDGS().text(query, max_results=3)
        if not results:
            return "Ничего не найдено."
        return "\n\n".join([f"{r.get('title', '')}: {r.get('body', '')} ({r.get('href', '')})" for r in results])
    except Exception as e:
        return f"Ошибка поиска: {e}"

def calculator(expression: str):
    """Вычисляет математическое выражение. Например: '2 + 2 * 2'."""
    try:
        return str(numexpr.evaluate(expression))
    except Exception as e:
        return f"Ошибка вычисления: {e}"

def get_weather(city: str):
    """Возвращает погоду в указанном городе (эмуляция)."""
    import random
    temps = {"London": 15, "Moscow": 20, "Bishkek": 25, "New York": 18}
    temp = temps.get(city, random.randint(10, 30))
    return f"Погода в {city}: {temp}°C, ясно."

def ask_rube(query: str):
    """Запрашивает информацию у Rube (MCP). Синхронная версия для совместимости."""
    api_key = os.getenv("RUBE_API_KEY")
    url = os.getenv("RUBE_API_URL")
    
    if not api_key or not url:
        return "Ошибка: Rube API не настроен."
    
    try:
        # Используем синхронный клиент
        with httpx.Client() as client:
            # Попытка 1: Простой REST
            response = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={"query": query},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if "content" in data: return data["content"]
                if "answer" in data: return data["answer"]
                return str(data)
                
            return f"Ошибка Rube API: {response.status_code}"
            
    except Exception as e:
        return f"Ошибка соединения с Rube: {e}"

AVAILABLE_TOOLS = {
    "search": search_internet,
    "calculator": calculator,
    "weather": get_weather,
    "rube": ask_rube 
}

class ToolsService:
    def get_tools_for_gemini(self, active_tools: list):
        """Возвращает список функций для Gemini API на основе активных флагов."""
        tools = []
        for name in active_tools:
            if name in AVAILABLE_TOOLS:
                tools.append(AVAILABLE_TOOLS[name])
        return tools

tools_service = ToolsService()