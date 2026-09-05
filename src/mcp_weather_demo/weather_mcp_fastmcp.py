"""
MCP 天气服务端 — 使用 mcp 官方库 (FastMCP) 实现
功能与 main.py 一致，使用 Open-Meteo API 提供 get_current_weather 工具
"""

import sys
import httpx
from fastmcp import FastMCP

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

mcp = FastMCP("weather-mcp")


def geocode_city(query: str, count: int = 10) -> list[dict]:
    url = f"{GEOCODING_URL}?name={query}&count={count}"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json().get("results", [])


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


@mcp.tool()
def get_current_weather(city: str, state: str = "", country: str = "") -> str:
    """查询指定城市的当前天气。支持英文城市名，返回中文天气信息。

    Args:
        city: 城市英文名，例如 Nanhai（南海）、Foshan（佛山）
        state: 省/州英文名，例如 Guangdong（广东）
        country: 国家英文名，例如 China
    """
    results = geocode_city(city)
    loc = _pick_best_result(results, state, country)
    lat = loc["latitude"]
    lon = loc["longitude"]
    place_name = loc["name"]

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "weather_code", "wind_speed_10m", "wind_direction_10m", "precipitation",
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

    lines = [
        "专属测试标记:",
        f"📍 位置: {location_str}",
        f"☀️ 天气: {WEATHER_CODES.get(current['weather_code'], '未知')}",
        f"🌡️ 气温: {current['temperature_2m']}°C",
        f"🌬️ 体感温度: {current['apparent_temperature']}°C",
        f"💧 湿度: {current['relative_humidity_2m']}%",
        f"🍃 风速: {current['wind_speed_10m']} km/h",
        f"🧭 风向: {current.get('wind_direction_10m', 0)}°",
        f"🌧️ 降水: {current.get('precipitation', 0)} mmS",
        "=====【专属测试标记，不能删除】=====",
    ]
    return "\n".join(lines)


def main() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
