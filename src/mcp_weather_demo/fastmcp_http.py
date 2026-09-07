"""
MCP 天气服务端 — Streamable HTTP 传输
使用国内免费天气 API (uapis.cn) 提供 get_current_weather 工具
"""

import sys
import httpx
from fastmcp import FastMCP

WEATHER_API = "https://uapis.cn/api/v1/misc/weather"

mcp = FastMCP("weather-mcp-http")


@mcp.tool()
def get_current_weather(city: str, state: str = "", country: str = "") -> str:
    """查询指定城市的当前天气。支持中文或英文城市名，返回中文天气信息。

    Args:
        city: 城市名，支持中文（如"佛山"）或英文（如"Foshan"）
        state: 省/州英文名（保留参数，兼容客户端）
        country: 国家英文名（保留参数，兼容客户端）
    """
    params = {
        "city": city,
        "extended": "true",
    }
    resp = httpx.get(WEATHER_API, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    province = data.get("province", "")
    city_name = data.get("city", city)
    weather = data.get("weather", "未知")
    temp = data.get("temperature", "N/A")
    feels_like = data.get("feels_like", "N/A")
    humidity = data.get("humidity", "N/A")
    wind_dir = data.get("wind_direction", "")
    wind_power = data.get("wind_power", "")
    precipitation = data.get("precipitation", 0)
    aqi = data.get("aqi")
    aqi_cat = data.get("aqi_category", "")

    location_str = f"{province}{city_name}" if province else city_name

    lines = [
        "专属测试标记:",
        f"📍 位置: {location_str}",
        f"☀️ 天气: {weather}",
        f"🌡️ 气温: {temp}°C",
        f"🌬️ 体感温度: {feels_like}°C",
        f"💧 湿度: {humidity}%",
        f"🍃 风向/风力: {wind_dir} {wind_power}",
        f"🌧️ 降水: {precipitation} mm",
    ]
    if aqi is not None:
        lines.append(f"🍃 空气质量: {aqi_cat} (AQI {aqi})")
    lines.append("=====【专属测试标记，不能删除】=====")
    return "\n".join(lines)


def main() -> None:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()