## 项目预览

`mcp_weather_demo` — 基于 **uv** 管理环境的 MCP (Model Context Protocol) 天气服务端，提供三种运行方式：

- 纯 stdio / JSON-RPC 2.0 实现（`original_stdio.py`）
- FastMCP 官方库实现（`fastmcp_stdio.py`）
- FastMCP Streamable HTTP 传输（`fastmcp_http.py`）

通过免费天气 API 查询实时天气，以 MCP Tool 形式暴露 `get_current_weather` 接口。

## 项目结构

```
mcp-weather-demo/
├── src/
│   └── mcp_weather_demo/
│       ├── __init__.py              # 包入口
│       ├── main.py                  # 纯 JSON-RPC / stdio 实现
│       ├── weather_mcp_fastmcp.py   # FastMCP 官方库实现（stdio）
│       └── weather_mcp_http.py      # FastMCP Streamable HTTP 实现
├── pyproject.toml                   # uv 项目元信息与依赖声明（Python >= 3.13, fastmcp, httpx）
├── uv.lock                          # uv 依赖锁定
├── requirements.txt                 # pip 依赖（可选，兼容其他环境）
├── logs/                            # main.py 运行日志
└── .venv/                           # uv 管理的虚拟环境
```

## 技术栈

- **语言**: Python >= 3.13（使用 `dict | None` 联合类型语法）
- **依赖管理**: uv
- **HTTP 客户端**: httpx
- **MCP 框架**: fastmcp（官方库）
- **协议**: MCP (JSON-RPC 2.0) over stdio / Streamable HTTP

## Setup & Development

使用 uv 管理项目环境：

```bash
# 安装依赖并同步环境（首次运行，会自动创建 .venv）
uv sync
```

## 运行方式

项目在 `pyproject.toml` 中声明了多个脚本入口：

```bash
# 纯 JSON-RPC / stdio 服务端（等待 stdin 的 JSON-RPC 消息）
uv run mcp-weather-stdio

# FastMCP 官方库，stdio 传输
uv run fastmcp-stdio

# FastMCP Streamable HTTP 传输，默认 http://0.0.0.0:8000/mcp
uv run fastmcp-http
```

## MCP 协议支持

| 方法 | 说明 |
|------|------|
| `initialize` | 握手，返回 server capabilities |
| `notifications/initialized` | 客户端初始化完成通知 |
| `ping` | 心跳检测 |
| `tools/list` | 列出可用工具（get_current_weather） |
| `tools/call` | 调用天气查询工具 |

## 测试方式

使用任意 MCP 客户端连接，或通过 echo/管道发送 JSON-RPC 消息测试：

```bash
# stdio 服务
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run mcp-weather-stdio

# HTTP 服务
uv run fastmcp-http   # 然后连接 http://0.0.0.0:8000/mcp
```
