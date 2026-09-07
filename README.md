## 项目预览

`mcp_weather_demo` — 基于 **uv** 管理环境的 MCP (Model Context Protocol) 天气服务端，提供三种实现方式：

- 纯 stdio / JSON-RPC 2.0 实现（`original_stdio.py`，数据源 Open-Meteo）
- FastMCP 官方库实现，stdio 传输（`fastmcp_stdio.py`，数据源 Open-Meteo）
- FastMCP Streamable HTTP 传输（`fastmcp_http.py`，数据源 uapis.cn）

三者均以 MCP Tool 形式暴露 `get_current_weather` 接口，入参统一为 `city` / `state` / `country`，返回中文天气信息。

## 项目结构

```
mcp-weather-demo/
├── src/
│   └── mcp_weather_demo/
│       ├── __init__.py              # 包入口（脚手架占位 main，仅打印欢迎语）
│       ├── original_stdio.py        # 纯 JSON-RPC 2.0 / stdio 实现
│       ├── fastmcp_stdio.py         # FastMCP 官方库实现（stdio 传输）
│       └── fastmcp_http.py          # FastMCP 官方库实现（Streamable HTTP 传输）
├── pyproject.toml                   # uv 项目元信息、依赖与脚本入口声明（Python >= 3.13）
├── uv.lock                          # uv 依赖锁定
├── requirements.txt                 # pip 依赖（可选，兼容其他环境）
├── logs/                            # original_stdio.py 运行日志（log-<时间戳>.txt）
└── .venv/                           # uv 管理的虚拟环境
```

## 技术栈

- **语言**: Python >= 3.13
- **依赖管理**: uv
- **HTTP 客户端**: httpx
- **MCP 框架**: fastmcp（官方库，>= 4.0.3）
- **协议**: MCP (JSON-RPC 2.0) over stdio / Streamable HTTP
- **天气数据源**: Open-Meteo（`original_stdio.py` / `fastmcp_stdio.py`）、uapis.cn（`fastmcp_http.py`）

## Setup & Development

使用 uv 管理项目环境：

```bash
# 安装依赖并同步环境（首次运行，会自动创建 .venv）
uv sync
```

## 运行方式

`pyproject.toml` 通过 `[project.scripts]` 声明了以下入口：

```bash
# 纯 JSON-RPC / stdio 服务端（等待 stdin 的 JSON-RPC 消息）
uv run original-stdio

# FastMCP 官方库，stdio 传输
uv run fastmcp-stdio

# FastMCP Streamable HTTP 传输，默认 http://0.0.0.0:8000/mcp
uv run fastmcp-http

# 脚手架占位入口（仅打印 "Hello from mcp-weather-demo!"）
uv run weather-mcp
```

## 实现逻辑

### 数据流（original_stdio.py / fastmcp_stdio.py，Open-Meteo）

1. `geocode_city(city)` 调用 Open-Meteo Geocoding API，按英文城市名解析经纬度；
2. `_pick_best_result()` 匹配多个候选结果：无歧义直接返回；传入了 `state` / `country` 时，按 `admin1` / `country` 字段择优；
3. 携带经纬度请求 Open-Meteo forecast API（参数含 `temperature_2m`、`relative_humidity_2m`、`apparent_temperature`、`weather_code`、`wind_speed_10m`、`wind_direction_10m`、`precipitation`，时区固定 `Asia/Shanghai`）；
4. 将 `weather_code` 映射为中文天气描述，并对佛山五区/部分省份做英文→中文名称映射，组装格式化文本返回。

其中 `original_stdio.py` 通过 `@log_call` 装饰器把每次工具触发的输入/输出/异常记录到 `logs/log-<启动时间戳>.txt`。

### 数据流（fastmcp_http.py，uapis.cn）

直接以 `city`（支持中文或英文）请求 `https://uapis.cn/api/v1/misc/weather`（`extended=true`），返回含省份、城市、天气、气温、体感、湿度、风向/风力、降水及可选 AQI 的文本。

### MCP 协议层差异

| 实现                | 协议处理                                                                                                                     |
|---------------------|------------------------------------------------------------------------------------------------------------------------------|
| `original_stdio.py` | 手写 JSON-RPC 2.0 分发：`initialize`、`notifications/initialized`、`ping`、`tools/list`、`tools/call`，逐行读写 stdin/stdout |
| `fastmcp_stdio.py`  | FastMCP 内置协议处理，`transport="stdio"`                                                                                    |
| `fastmcp_http.py`   | FastMCP 内置协议处理，`transport="streamable-http"`，监听 `0.0.0.0:8000`                                                     |

### Tool: `get_current_weather`

| 参数      | 必填 | 说明                                                                         |
|-----------|------|------------------------------------------------------------------------------|
| `city`    | 是   | 城市名。Open-Meteo 实现需英文名（如 Nanhai/Foshan）；uapis.cn 实现中英文均可 |
| `state`   | 否   | 省/州英文名（如 Guangdong），用于候选消歧；uapis.cn 实现中为保留参数         |
| `country` | 否   | 国家英文名（如 China），用于候选消歧；uapis.cn 实现中为保留参数              |

## 测试方式

使用任意 MCP 客户端连接，或通过 echo/管道发送 JSON-RPC 消息测试：

```bash
# stdio 服务（original-stdio）
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run original-stdio

# 调用天气工具（original-stdio，参数需经 JSON 转义）
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_current_weather","arguments":{"city":"Foshan","state":"Guangdong"}}}' | uv run original-stdio

# HTTP 服务
uv run fastmcp-http   # 然后连接 http://0.0.0.0:8000/mcp
```
