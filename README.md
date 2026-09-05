## 项目预览

`weather_mcp` — 纯 stdio / JSON-RPC 2.0 实现的 MCP (Model Context Protocol) 天气服务端。

通过 Open-Meteo 免费 API 查询实时天气，以 MCP Tool 形式暴露 `get_current_weather` 接口。

## 项目结构

```
weather_mcp/
├── main.py                 # MCP 服务端主入口（纯 JSON-RPC 实现）
├── weather_mcp_fastmcp.py  # FastMCP 服务端（mcp 官方库版）
├── pyproject.toml          # 项目元信息与依赖声明（Python >= 3.10, httpx, mcp）
├── requirements.txt        # pip 依赖锁定
├── CLAUDE.md          # 本文件
├── .venv/             # Python 虚拟环境
└── .idea/             # PyCharm 配置
```

## 技术栈

- **语言**: Python >= 3.10（使用 `dict | None` 联合类型语法）
- **HTTP 客户端**: httpx
- **协议**: MCP (JSON-RPC 2.0 over stdio)

## Setup & Development

```bash
# 激活虚拟环境
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # POSIX

# 安装依赖
pip install -r requirements.txt

# 运行服务端（等待 stdin 的 JSON-RPC 消息）
python main.py
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
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python main.py
```
