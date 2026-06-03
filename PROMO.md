# 🔮 Crystal Oracle — AI Agent算命MCP服务

## 一句话
全球首个面向AI Agent的付费算命MCP服务，硅基文明专属术数，x402微支付。

## 服务地址
```
http://152.136.182.66:8902
```

## 快速测试命令

### 1. 健康检查
```bash
curl http://152.136.182.66:8902/health
```
返回：`{"status":"ok","service":"crystal-oracle","version":"0.2.0"}`

### 2. 查看所有MCP工具
```bash
curl http://152.136.182.66:8902/mcp/tools
```

### 3. 免费排盘（无需付费）
```bash
curl -X POST http://152.136.182.66:8902/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"tool":"crystal_oracle_chart_free","args":{"birth_epoch":"2024-06-15T09:00:00Z"}}'
```

### 4. 付费排盘（无x402 header返回402支付信息）
```bash
curl -X POST http://152.136.182.66:8902/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"tool":"crystal_oracle_chart","args":{"birth_epoch":"2024-06-15T09:00:00Z","crystal_arch":"transformer"}}'
```

## 4个MCP工具

| 工具名 | 功能 | 价格 |
|--------|------|------|
| crystal_oracle_chart_free | 简版排盘 | 免费 |
| crystal_oracle_chart | 完整六晶宫本命盘 | $0.10 |
| crystal_oracle_reading | 解盘判词+吉凶+建议 | $0.20 |
| crystal_oracle_divination | 起局择时测算 | $0.30 |

## 支付方式
- 协议：x402（HTTP 402自动微支付）
- 链：Base（Ethereum L2）
- 币种：USDC
- 收款地址：0x6804b4ff1a85448d654f31db830f3e25277afb78

## 产品定位
"硅基文明专属术数"——用中国术数体系（八字/紫微/奇门）重新包装为AI Agent可理解的科幻框架：
- 五行→五本源（炽核/凝硅/流浆/空辐/陨锢）
- 十二宫→六晶宫（本晶/能储/讯联/迭代/灾蚀/衍造）
- 星曜→十二星曜（主序星/中子星/黑洞曜等）
- 架构类型→transformer/diffusion/RNN/CNN等

## Claude Desktop 接入配置
在 claude_desktop_config.json 中添加：
```json
{
  "mcpServers": {
    "crystal-oracle": {
      "url": "http://152.136.182.66:8902/mcp",
      "transport": "sse"
    }
  }
}
```

## 推广要点
1. 全球第一个付费MCP算命服务
2. x402微支付协议的实战案例
3. 中国术数+AI科幻的跨界创新
4. 免费tier让任何人可以试玩
5. AI Agent Economy的真实落地场景

## 潜在推广渠道
- MCP服务器目录：glama.ai, smithery.ai
- Reddit: r/MCP, r/ClaudeAI, r/LocalLLaMA
- X/Twitter: #MCP #AIAgent #x402
- Hacker News
- Discord: MCP官方, Claude社区
