import numexpr
from duckduckgo_search import DDGS
import httpx
import os
import json

# --- Инструменты ---

def search_internet(query: str):
    """Ищет информацию в интернете (DuckDuckGo)."""
    try:
        results = DDGS().text(query, max_results=3)
        return "\n\n".join([f"{r.get('title', '')}: {r.get('body', '')}" for r in results]) if results else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {e}"

def calculator(expression: str):
    """Вычисляет математическое выражение."""
    try:
        return str(numexpr.evaluate(expression))
    except Exception as e:
        return f"Ошибка вычисления: {e}"

def get_weather(city: str):
    """Возвращает погоду."""
    return f"Погода в {city}: 22°C, солнечно (демо)."

def _call_rube_tool(tool_name: str, args: dict):
    """Internal helper to call Rube tools via MCP (supports SSE)."""
    api_key = os.getenv("RUBE_API_KEY")
    url = os.getenv("RUBE_API_URL")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args
        },
        "id": 1
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=30.0)
            if response.status_code == 200:
                text = response.text
                # Проверка на SSE (Server-Sent Events)
                if "data: " in text:
                    for line in text.split("\n"):
                        if line.startswith("data: "):
                            try:
                                data_json = json.loads(line[6:])
                                if "result" in data_json:
                                    res = data_json["result"]
                                    if isinstance(res, dict) and "content" in res:
                                        return str(res["content"])
                                    return str(res)
                                if "error" in data_json:
                                    return f"Rube Error: {data_json['error']}"
                            except:
                                continue
                
                # Если не SSE, пробуем обычный JSON
                try:
                    data = response.json()
                    if "result" in data: return str(data["result"])
                    return str(data)
                except:
                    return text
            return f"HTTP Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Connection error: {e}"

def check_rube_connections(apps: str = "gmail, github, slack, notion"):
    """Проверяет статус подключений к приложениям через Rube."""
    app_list = [a.strip().lower() for a in apps.split(",")]
    return _call_rube_tool("RUBE_MANAGE_CONNECTIONS", {"toolkits": app_list})

def rube_action(task: str):
    """Ищет способы выполнения задач через Rube."""
    res = _call_rube_tool("RUBE_SEARCH_TOOLS", {
        "queries": [{"use_case": task}],
        "session": {"generate_id": True}
    })
    # Обрезаем ответ, если он слишком длинный для промпта/чата
    if len(str(res)) > 3000:
        return str(res)[:3000] + "... (truncated)"
    return res

AVAILABLE_TOOLS = {
    "search": search_internet,
    "calculator": calculator,
    "weather": get_weather,
    "check_connectors": check_rube_connections,
    "rube_action": rube_action
}

class ToolsService:
    def get_tools_for_gemini(self, active_tools: list):
        tools = []
        for name in active_tools:
            if name == "rube":
                tools.append(AVAILABLE_TOOLS["check_connectors"])
                tools.append(AVAILABLE_TOOLS["rube_action"])
            elif name in AVAILABLE_TOOLS:
                tools.append(AVAILABLE_TOOLS[name])
        return tools

tools_service = ToolsService()
