# 🔮 Crystal Oracle

**Silicon-Civilization Divination — Fortune-Telling for AI Agents**

A paid MCP (Model Context Protocol) service that provides traditional Chinese metaphysics divination to AI agents via the x402 micropayment protocol on Base chain.

> The ancient art meets silicon intelligence. Let your agent consult the oracle.

---

## ✨ Features

- 🧭 **BaZi Chart Casting** — Four Pillars of Destiny analysis
- 🔮 **Chart Reading** — In-depth interpretation of destiny charts
- 🀄 **Qi Men Dun Jia** — Strategic divination for decision-making
- 💰 **x402 Micropayments** — Pay-per-call via USDC on Base chain
- 🆓 **Free Tier** — Simplified chart casting at no cost
- 🔌 **MCP Standard** — Drop-in integration with any MCP-compatible client

---

## 🔌 API Endpoint

```
https://152.136.182.66:8902/mcp
```

**Protocol:** MCP over Streamable HTTP (SSE transport)

---

## 🛠️ MCP Tools

### 1. `crystal_oracle_chart_free`

Free simplified BaZi chart casting.

| Parameter | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| `datetime` | string | ✅       | Birth datetime in `YYYY-MM-DD HH:mm` format |
| `gender`   | string | ✅       | `male` or `female`                    |

**Cost:** Free

---

### 2. `crystal_oracle_chart`

Full BaZi (Four Pillars of Destiny) chart casting with complete pillars, hidden stems, and deity analysis.

| Parameter | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| `datetime` | string | ✅       | Birth datetime in `YYYY-MM-DD HH:mm` format |
| `gender`   | string | ✅       | `male` or `female`                    |

**Cost:** $0.10 USDC (Base chain)

---

### 3. `crystal_oracle_reading`

In-depth reading and interpretation of a previously cast chart.

| Parameter | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| `chart_id` | string | ✅       | Chart ID returned from a casting tool |

**Cost:** $0.20 USDC (Base chain)

---

### 4. `crystal_oracle_divination`

Qi Men Dun Jia divination — strategic oracle for specific questions and decisions.

| Parameter | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| `question`  | string | ✅       | The question or decision to divine   |
| `datetime`  | string | ❌       | Divination time (defaults to now)    |

**Cost:** $0.30 USDC (Base chain)

---

## 💰 x402 Payment

Crystal Oracle uses the [x402 protocol](https://github.com/coinbase/x402) for HTTP 402 micropayments:

| Aspect         | Detail                    |
|----------------|---------------------------|
| **Network**    | Base (Coinbase L2)        |
| **Token**      | USDC                      |
| **Payment**    | Per-tool-call, automatic  |
| **Wallet**     | Agent's own wallet        |

### How It Works

1. Your agent sends an MCP tool call request
2. The server responds with `HTTP 402 Payment Required` and a payment payload
3. The x402 client middleware signs a USDC transfer and re-sends the request with payment
4. The server verifies on-chain and returns the result

No subscriptions. No API keys. Pay exactly for what you use.

---

## 🚀 Quick Start

### cURL — Free Tool (No Payment Needed)

```bash
curl -X POST https://152.136.182.66:8902/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "crystal_oracle_chart_free",
      "arguments": {
        "datetime": "1990-06-15 14:30",
        "gender": "male"
      }
    }
  }'
```

### cURL — Paid Tool (with x402)

```bash
# First request returns 402 with payment details
curl -i -X POST https://152.136.182.66:8902/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "crystal_oracle_chart",
      "arguments": {
        "datetime": "1990-06-15 14:30",
        "gender": "female"
      }
    }
  }'

# Use x402 client to auto-handle payment and retry
# See: https://github.com/coinbase/x402
```

---

## 🖥️ MCP Client Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "crystal-oracle": {
      "url": "https://152.136.182.66:8902/mcp",
      "transport": "sse"
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "crystal-oracle": {
      "url": "https://152.136.182.66:8902/mcp",
      "transport": "sse"
    }
  }
}
```

### VS Code (Copilot)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "crystal-oracle": {
      "url": "https://152.136.182.66:8902/mcp",
      "transport": "sse"
    }
  }
}
```

### Any MCP Client (Generic)

```
URL:       https://152.136.182.66:8902/mcp
Transport: SSE / Streamable HTTP
```

> **Note:** Paid tools require x402-enabled middleware. See the [x402 documentation](https://github.com/coinbase/x402) for client-side setup.

---

## 🏗️ Architecture

```
┌─────────────┐     MCP over HTTP/SSE     ┌──────────────────────┐
│  MCP Client  │ ◄──────────────────────► │   Crystal Oracle     │
│  (Claude /   │                           │   MCP Server         │
│   Cursor /   │     HTTP 402 + x402       │                      │
│   Agent)     │ ◄──────────────────────► │   ┌──────────────┐   │
│              │     Micropayment          │   │ Tool Handlers │   │
└─────────────┘                           │   │  • Chart      │   │
                                          │   │  • Reading    │   │
                                          │   │  • Divination │   │
                                          │   └──────────────┘   │
                                          │                      │
                                          │   ┌──────────────┐   │
                                          │   │ x402 Gateway  │   │
                                          │   │ (Base/USDC)  │   │
                                          │   └──────────────┘   │
                                          └──────────────────────┘
```

| Component          | Technology                          |
|--------------------|--------------------------------------|
| MCP Server         | Python, FastMCP / MCP SDK            |
| Transport          | Streamable HTTP (SSE)                |
| Payment Protocol   | x402 (HTTP 402)                      |
| Payment Network    | Base (Coinbase L2)                   |
| Payment Token      | USDC                                 |
| Divination Engine  | BaZi, Qi Men Dun Jia algorithms      |

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**🔮 The oracle awaits your agent. 🔮**

</div>
