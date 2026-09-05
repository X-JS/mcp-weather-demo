"""
MCP (Model Context Protocol) 天气服务端 — 纯 stdio / JSON-RPC 2.0 实现
"""

import os
import sys
import json
import logging
import functools
import traceback
from datetime import datetime
from collections.abc import Callable
import httpx

# ---------------------------------------------------------------------------
# 天气查询模块
# ---------------------------------------------------------------------------

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "晴朗", 1: "大部晴朗", 2: "局部多云", 3: "阴天",
    45: "雾", 48: "雾凇",
    51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
    56: "冻毛毛雨(轻)", 57: "冻毛毛雨(重)",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻小雨(轻)", 67: "冻小雨(重)",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "雪粒",
    80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷暴", 96: "雷暴冰雹(轻)", 99: "雷暴冰雹(重)",
}

_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_STARTUP_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
_LOG_FILE = os.path.join(_LOG_DIR, f"log-{_STARTUP_TS}.txt")

logger = logging.getLogger("weather_mcp")
logger.setLevel(logging.INFO)
logger.propagate = False
_fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
_fh.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(_fh)


def _to_json(obj: object) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)


def log_call(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        method = func.__name__
        inputs = {"args": list(args), "kwargs": kwargs}
        logger.info("触发时间: %s | 方法名: %s | 输入: %s", now, method, _to_json(inputs))
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error("触发时间: %s | 方法名: %s | 异常: %s", now, method, _to_json(e))
            raise
        logger.info("触发时间: %s | 方法名: %s | 输出: %s", now, method, _to_json(result))
        return result
    return wrapper


@log_call
def geocode_city(query: str, count: int = 10) -> list[dict]:
    resp = httpx.get(GEOCODING_URL, params={"name": query, "count": count}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


@log_call
def _pick_best_result(results: list[dict], state: str = "", country: str = "") -> dict:
    if not results:
        raise ValueError("没有匹配的结果")
    if len(results) == 1:
        return results[0]
    if state or country:
        for r in results:
            match_state = not state or state.lower() in r.get("admin1", "").lower()
            match_country = not country or country.lower() in r.get("country", "").lower()
            if match_state and match_country:
                return r
    return results[0]


@log_call
def get_current_weather(city: str, state: str = "", country: str = "") -> dict:
    results = geocode_city(city)
    loc = _pick_best_result(results, state, country)
    lat = loc["latitude"]
    lon = loc["longitude"]
    place_name = loc["name"]

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "precipitation",
        ],
        "timezone": "Asia/Shanghai",
    }
    resp = httpx.get(WEATHER_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    current = data["current"]

    admin1 = loc.get("admin1", "")
    country_name = loc.get("country", "")
    name_cn_map = {
        "Nanhai": "南海", "Chancheng": "禅城", "Shunde": "顺德",
        "Sanshui": "三水", "Gaoming": "高明", "Foshan": "佛山",
    }
    cn_name = name_cn_map.get(place_name, place_name)
    cn_admin1 = {"Guangdong": "广东", "Fujian": "福建", "Hubei": "湖北",
                 "Yunnan": "云南", "Anhui": "安徽"}
    cn_adm1 = cn_admin1.get(admin1, admin1)

    if admin1 and country_name:
        location_str = f"中国{cn_adm1}{cn_name}"
    elif admin1:
        location_str = f"{cn_adm1}/{cn_name}"
    else:
        location_str = cn_name

    return {
        "location": location_str,
        "temperature_2m": current["temperature_2m"],
        "apparent_temperature": current["apparent_temperature"],
        "relative_humidity_2m": current["relative_humidity_2m"],
        "wind_speed_10m": current["wind_speed_10m"],
        "wind_direction_10m": current.get("wind_direction_10m", 0),
        "precipitation": current.get("precipitation", 0),
        "weather_code": current["weather_code"],
        "weather_description": WEATHER_CODES.get(current["weather_code"], "未知"),
    }


# ---------------------------------------------------------------------------
# MCP 协议层 (JSON-RPC 2.0 over stdio)
# ---------------------------------------------------------------------------

HANDLERS: dict[str, Callable] = {}


@log_call
def read_message() -> dict | None:
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line.strip())


@log_call
def send_message(msg: dict) -> None:
    text = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


@log_call
def handle_initialize(req: dict) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req["id"],
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "weather-mcp", "version": "0.1.0"},
        },
    }


@log_call
def handle_tools_list(req: dict) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req["id"],
        "result": {
            "tools": [
                {
                    "name": "get_current_weather",
                    "description": "查询指定城市的当前天气。支持英文城市名，返回中文天气信息。",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市英文名，例如 Nanhai（南海）、Foshan（佛山）",
                            },
                            "state": {
                                "type": "string",
                                "description": "省/州英文名，例如 Guangdong（广东）",
                            },
                            "country": {
                                "type": "string",
                                "description": "国家英文名，例如 China",
                            },
                        },
                        "required": ["city"],
                    },
                },
            ],
        },
    }


@log_call
def handle_tools_call(req: dict) -> dict:
    params = req.get("params", {})
    name = params.get("name", "")
    args = params.get("arguments", {})

    try:
        if name == "get_current_weather":
            city = args.get("city", "")
            state = args.get("state", "")
            country = args.get("country", "")
            weather = get_current_weather(city, state, country)
            text = _format_weather_text(weather)
            return {
                "jsonrpc": "2.0",
                "id": req["id"],
                "result": {
                    "content": [{"type": "text", "text": text}],
                },
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req["id"],
                "error": {"code": -32601, "message": f"未知工具: {name}"},
            }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": req["id"],
            "error": {"code": -32603, "message": str(e)},
        }


@log_call
def _format_weather_text(weather: dict) -> str:
    lines = [
        "专属测试标记:",
        f"📍 位置: {weather['location']}",
        f"☀️ 天气: {weather['weather_description']}",
        f"🌡️ 气温: {weather['temperature_2m']}°C",
        f"🌬️ 体感温度: {weather['apparent_temperature']}°C",
        f"💧 湿度: {weather['relative_humidity_2m']}%",
        f"🍃 风速: {weather['wind_speed_10m']} km/h",
        f"🧭 风向: {weather['wind_direction_10m']}°",
        f"🌧️ 降水: {weather['precipitation']} mms"
    ]
    return "\n".join(lines)


@log_call
def handle_ping(req: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req["id"], "result": {}}


@log_call
def register_handler(method: str, handler: Callable) -> None:
    HANDLERS[method] = handler


@log_call
def dispatch(req: dict) -> dict | None:
    method = req.get("method", "")
    is_notification = "id" not in req

    if method == "notifications/initialized":
        return None

    handler = HANDLERS.get(method)
    if handler:
        return handler(req)

    if is_notification:
        return None

    return {
        "jsonrpc": "2.0",
        "id": req["id"],
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


@log_call
def main() -> None:
    if sys.platform == "win32":
        sys.stdin.reconfigure(encoding="utf-8")
        sys.stdout.reconfigure(encoding="utf-8")

    register_handler("initialize", handle_initialize)
    register_handler("tools/list", handle_tools_list)
    register_handler("tools/call", handle_tools_call)
    register_handler("ping", handle_ping)

    while True:
        try:
            msg = read_message()
            if msg is None:
                break

            result = dispatch(msg)
            if result is not None:
                send_message(result)

        except json.JSONDecodeError:
            print(f"JSON 解析错误", file=sys.stderr)
        except Exception:
            traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    main()
