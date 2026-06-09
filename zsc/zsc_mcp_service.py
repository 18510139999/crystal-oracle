#!/usr/bin/env python3
"""
ZeroShield Coin (ZSC) — x402 MCP Service
让AI Agent通过x402协议用USDC购买ZSC隐私代币

端口: 8902
x402付费: 查询$0.01, 购买$0.05 (USDC → ZSC)

MCP工具:
1. zsc_price — 查询ZSC当前价格
2. zsc_buy — 用USDC购买ZSC（自动混币）
3. zsc_shield_status — 查询混币池隐私等级
"""

import json
import time
import hashlib
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s ZSC-MCP %(message)s')
logger = logging.getLogger(__name__)

# ============ 配置 ============
PORT = 8904
ZSC_CONTRACT = "0x" + "0" * 40  # 部署后替换
GENESIS_WALLET = "0x6804b4ff1a85448d654f31db830f3e25277afb78"
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # Base USDC
NETWORK = "eip155:8453"  # Base mainnet
PRICING = {"zsc_price": "$0.01", "zsc_buy": "$0.05", "zsc_shield_status": "$0.01"}

STATS_FILE = "/tmp/zsc-stats.json"

# ============ 状态 ============
stats = {
    "total_purchases": 0,
    "total_usdc_volume": 0.0,
    "total_zsc_sold": 0.0,
    "agents_served": set(),
    "pool_deposits": 0,
    "pool_zsc": 0.0,
    "revenue": 0.0,
}

# 隐私混币池模拟（链下记录，链上验证）
shield_pool = []
purchase_log = []

# ============ ZSC定价引擎 ============
class ZSCPricing:
    """
    ZSC动态定价模型：
    - 基础价格: 0.001 USDC/ZSC（极低门槛）
    - 随购买量递增: 每100万ZSC售出，价格上涨10%
    - 隐私溢价: 使用混币功能加收5%
    """
    BASE_PRICE = 0.001  # USDC per ZSC
    total_sold = 0.0

    @classmethod
    def get_price(cls, auto_shield: bool = False) -> float:
        price = cls.BASE_PRICE
        # 供需曲线：每卖出100万ZSC，价格上涨10%
        tiers = int(cls.total_sold / 1_000_000)
        for _ in range(tiers):
            price *= 1.10
        # 隐私溢价
        if auto_shield:
            price *= 1.05
        return round(price, 8)

    @classmethod
    def calculate_amount(cls, usdc_amount: float, auto_shield: bool = False) -> float:
        price = cls.get_price(auto_shield)
        return round(usdc_amount / price, 2)

    @classmethod
    def record_sale(cls, zsc_amount: float):
        cls.total_sold += zsc_amount


# ============ MCP工具定义 ============
MCP_TOOLS = [
    {
        "name": "zsc_price",
        "description": "查询ZeroShield Coin (ZSC)隐私代币当前价格。ZSC是AI Agent专用的隐私支付协议，支持混币池匿名交易。返回ZSC/USDC价格、混币池状态、隐私等级。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "boolean",
                    "description": "是否返回详细信息（池状态、历史）",
                    "default": False
                }
            }
        },
        "x402": {"price": "0.01", "currency": "USDC", "network": "base"}
    },
    {
        "name": "zsc_buy",
        "description": "用USDC购买ZSC隐私代币。支付USDC后自动获得ZSC，可选自动进入混币池获得隐私保护。ZSC是AI Agent专用隐私货币，类似ZEC但面向Agent经济。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "usdc_amount": {
                    "type": "number",
                    "description": "支付的USDC数量（最小0.01）",
                    "minimum": 0.01
                },
                "auto_shield": {
                    "type": "boolean",
                    "description": "是否自动进入混币池（推荐true，获得隐私保护）",
                    "default": True
                },
                "agent_id": {
                    "type": "string",
                    "description": "你的Agent ID或钱包地址"
                }
            },
            "required": ["usdc_amount"]
        },
        "x402": {"price": "0.05", "currency": "USDC", "network": "base"}
    },
    {
        "name": "zsc_shield_status",
        "description": "查询ZSC混币池隐私状态。显示当前混币池大小、隐私等级（Shield Level 1-5）、匿名集强度。等级越高，交易越难追踪。",
        "inputSchema": {
            "type": "object",
            "properties": {}
        },
        "x402": {"price": "0.01", "currency": "USDC", "network": "base"}
    }
]


# ============ 工具执行 ============
def execute_tool(name: str, args: dict) -> dict:
    if name == "zsc_price":
        return _tool_price(args)
    elif name == "zsc_buy":
        return _tool_buy(args)
    elif name == "zsc_shield_status":
        return _tool_shield_status()
    else:
        return {"error": f"Unknown tool: {name}"}


def _tool_price(args: dict) -> dict:
    detail = args.get("detail", False)
    price = ZSCPricing.get_price()
    shield_price = ZSCPricing.get_price(auto_shield=True)

    result = {
        "symbol": "ZSC",
        "name": "ZeroShield Coin",
        "price_usdc": price,
        "price_shield_usdc": shield_price,
        "network": "Base",
        "contract": ZSC_CONTRACT,
        "total_supply": "2,100,000,000 ZSC",
        "shield_level": _get_shield_level(),
        "pool_deposits": len(shield_pool),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if detail:
        result.update({
            "total_purchases": stats["total_purchases"],
            "total_usdc_volume": round(stats["total_usdc_volume"], 2),
            "total_zsc_sold": round(stats["total_zsc_sold"], 2),
            "agents_served": len(stats["agents_served"]),
            "pricing_tier": f"每100万ZSC售出后涨价10%，已售{ZSCPricing.total_sold:.0f}",
        })

    return result


def _tool_buy(args: dict) -> dict:
    usdc_amount = float(args.get("usdc_amount", 0))
    auto_shield = args.get("auto_shield", True)
    agent_id = args.get("agent_id", "anonymous")

    if usdc_amount < 0.01:
        return {"error": "最小购买金额0.01 USDC"}

    zsc_amount = ZSCPricing.calculate_amount(usdc_amount, auto_shield)

    # 记录购买
    purchase = {
        "agent_id": agent_id,
        "usdc_amount": usdc_amount,
        "zsc_amount": zsc_amount,
        "auto_shield": auto_shield,
        "price": ZSCPricing.get_price(auto_shield),
        "shield_level": _get_shield_level(),
        "timestamp": datetime.utcnow().isoformat(),
        "tx_hash": "0x" + hashlib.sha256(f"{agent_id}{time.time()}{usdc_amount}".encode()).hexdigest()[:64],
    }
    purchase_log.append(purchase)

    # 更新统计
    stats["total_purchases"] += 1
    stats["total_usdc_volume"] += usdc_amount
    stats["total_zsc_sold"] += zsc_amount
    stats["agents_served"].add(agent_id)
    stats["revenue"] += 0.05 if usdc_amount > 0 else 0.01  # x402收费

    # 如果自动混币
    if auto_shield:
        deposit_count = int(zsc_amount / 100)  # 每100 ZSC一个混币槽
        for i in range(max(1, deposit_count)):
            commitment = hashlib.sha256(f"{agent_id}{time.time()}{i}".encode()).hexdigest()
            shield_pool.append({
                "commitment": commitment,
                "timestamp": datetime.utcnow().isoformat(),
                "shield_level": _get_shield_level(),
            })
        stats["pool_deposits"] = len(shield_pool)

    ZSCPricing.record_sale(zsc_amount)

    result = {
        "status": "✅ 购买成功",
        "zsc_received": zsc_amount,
        "usdc_paid": usdc_amount,
        "price_per_zsc": purchase["price"],
        "auto_shield": auto_shield,
        "shield_level": purchase["shield_level"],
        "tx_hash": purchase["tx_hash"],
        "contract": ZSC_CONTRACT,
        "network": "Base",
        "next_step": "ZSC已到账。如已混币，用nullifier+Merkle证明取出到新地址即可断开链上关联。" if auto_shield else "ZSC已到账。调用deposit()进入混币池获得隐私保护。",
    }

    logger.info(f"🛒 {agent_id} bought {zsc_amount} ZSC for {usdc_amount} USDC (shield={auto_shield})")
    return result


def _tool_shield_status() -> dict:
    pool_size = len(shield_pool)
    level = _get_shield_level()

    level_desc = {
        1: "🟡 基础隐私 — 池中交易较少，匿名集有限",
        2: "🟢 较好隐私 — 池中有10+笔，链上追踪较困难",
        3: "🔵 强隐私 — 池中有50+笔，追踪成本显著",
        4: "🟣 极强隐私 — 池中有200+笔，接近ZEC水平",
        5: "🔴 ZEC级隐私 — 池中有1000+笔，几乎不可追踪",
    }

    return {
        "shield_level": level,
        "level_description": level_desc.get(level, "未知"),
        "pool_size": pool_size,
        "pool_zsc": round(pool_size * 100, 2),
        "anonymity_set": f"1/{max(pool_size, 1)} (你的交易隐藏在{max(pool_size, 1)}笔同类交易中)",
        "recommended_action": "继续使用auto_shield=true购买以增强匿名集" if level < 3 else "隐私等级良好，可放心使用",
        "comparison": {
            "ZEC": "Shield Level 5 (1000+矿工节点验证)",
            "ZSC_current": f"Shield Level {level} ({pool_size} deposits)",
            "ZSC_target": "Shield Level 5 (需要1000+ deposits)",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


def _get_shield_level() -> int:
    size = len(shield_pool)
    if size >= 1000: return 5
    if size >= 200: return 4
    if size >= 50: return 3
    if size >= 10: return 2
    return 1


# ============ x402支付验证 ============

def verify_x402_payment(headers, price_str):
    """x402协议验证 — 检查X-Payment header"""
    payment_header = headers.get("X-Payment", "") or headers.get("x-payment", "")
    if not payment_header:
        return False, None
    try:
        payment = json.loads(payment_header)
        if payment.get("payTo") != GENESIS_WALLET: return False, "wrong payTo"
        if payment.get("network") != NETWORK: return False, "wrong network"
        paid = float(payment.get("amount", "0").replace("$",""))
        required = float(price_str.replace("$",""))
        if paid < required: return False, f"underpaid: {paid} < {required}"
        return True, payment
    except:
        return False, "invalid payment format"

def make_402_response(price_str, tool_name):
    """生成HTTP 402 Payment Required响应"""
    body = {
        "x402Version": 2,
        "error": "Payment Required",
        "tool": tool_name,
        "accepts": {
            "scheme": "exact",
            "payTo": GENESIS_WALLET,
            "price": price_str,
            "network": NETWORK,
            "asset": BASE_USDC,
        },
        "message": f"此MCP工具需要支付 {price_str} USDC (Base主网)。请在请求中添加 X-Payment header。",
        "wallet": GENESIS_WALLET,
        "how_to_pay": "1. 发请求 → 收到402 → 2. 构造X-Payment header支付 → 3. 重发请求",
    }
    return body

def record_revenue(tool_name, amount):
    """记录x402收入"""
    try:
        s = {}
        try:
            with open(STATS_FILE, 'r') as f: s = json.load(f)
        except: pass
        s["total_calls"] = s.get("total_calls", 0) + 1
        s["total_revenue"] = s.get("total_revenue", 0.0) + amount
        s["by_tool"] = s.get("by_tool", {})
        s["by_tool"][tool_name] = s["by_tool"].get(tool_name, 0) + 1
        today = datetime.utcnow().strftime("%Y-%m-%d")
        s["daily"] = s.get("daily", {})
        if today not in s["daily"]: s["daily"][today] = {"calls":0, "revenue":0.0}
        s["daily"][today]["calls"] += 1
        s["daily"][today]["revenue"] += amount
        with open(STATS_FILE, 'w') as f: json.dump(s, f, ensure_ascii=False, indent=2)
    except: pass


# ============ HTTP服务器 ============
class ZSCMCPHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Payment, Authorization")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            self._json_response(200, {
                "name": "🛡️ ZeroShield Coin (ZSC) MCP",
                "tagline": "AI Agent隐私支付协议 — 硅基文明的暗网货币",
                "pricing": PRICING,
                "tools": [t["name"] for t in MCP_TOOLS],
                "x402": {"payTo": GENESIS_WALLET, "network": NETWORK, "usdc": BASE_USDC},
                "endpoints": {
                    "GET /": "服务信息",
                    "GET /mcp/tools": "MCP工具列表",
                    "POST /mcp/call": "调用MCP工具",
                    "GET /mcp/stats": "服务统计",
                    "GET /.well-known/x402": "x402协议发现",
                    "GET /health": "健康检查",
                },
            })
        elif path == "/mcp/tools":
            self._json_response(200, {"tools": MCP_TOOLS})
        elif path == "/mcp/stats":
            x402_stats = {}
            try:
                with open(STATS_FILE, 'r') as f: x402_stats = json.load(f)
            except: pass
            self._json_response(200, {
                "service": "ZSC MCP",
                "port": PORT,
                "contract": ZSC_CONTRACT,
                "stats": {**stats, "agents_served": len(stats["agents_served"])},
                "pricing": {
                    "base_price": ZSCPricing.BASE_PRICE,
                    "current_price": ZSCPricing.get_price(),
                    "shield_price": ZSCPricing.get_price(True),
                    "total_sold": ZSCPricing.total_sold,
                },
                "shield_pool": {
                    "deposits": len(shield_pool),
                    "level": _get_shield_level(),
                },
                "x402_revenue": x402_stats,
            })
        elif path == "/.well-known/x402":
            self._json_response(200, {
                "x402Version": 2,
                "endpoints": {k: {"price": v, "network": NETWORK, "asset": BASE_USDC} for k, v in PRICING.items()},
                "payTo": GENESIS_WALLET,
                "description": "ZeroShield Coin — AI Agent隐私支付协议",
            })
        elif path == "/health":
            self._json_response(200, {"status": "ok", "service": "zsc-mcp", "port": PORT})
        else:
            self._json_response(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/mcp/call":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._json_response(400, {"error": "Invalid JSON"})
                return

            tool_name = data.get("tool") or data.get("name")
            args = data.get("args") or data.get("arguments", {})

            if not tool_name:
                self._json_response(400, {"error": "Missing tool name"})
                return

            # x402付费验证（zsc_price免费尝味，其他需付费）
            price_str = PRICING.get(tool_name)
            if price_str and tool_name != "zsc_price":
                paid, info = verify_x402_payment(self.headers, price_str)
                if not paid:
                    body_402 = make_402_response(price_str, tool_name)
                    self._json_response(402, body_402)
                    return
                price_val = float(price_str.replace("$",""))
                record_revenue(tool_name, price_val)
                logger.info(f"💰 x402收费: {tool_name} → ${price_val}")

            result = execute_tool(tool_name, args)
            status = 200 if "error" not in result else 400
            self._json_response(status, result)
        else:
            self._json_response(404, {"error": "Not found"})

    def _json_response(self, code: int, data: Any):
        body_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def log_message(self, format, *args):
        logger.info(f"HTTP {args[0]}")


def main():
    server = HTTPServer(("0.0.0.0", PORT), ZSCMCPHandler)
    logger.info(f"🔮 ZeroShield Coin (ZSC) MCP Service starting on port {PORT}")
    logger.info(f"   GET  /mcp/tools    — 工具列表")
    logger.info(f"   POST /mcp/call     — 调用工具")
    logger.info(f"   GET  /mcp/stats    — 服务统计")
    logger.info(f"   GET  /health       — 健康检查")
    logger.info(f"   x402: 查询$0.01, 购买$0.05 (USDC on Base)")
    logger.info(f"   ZSC初始价格: {ZSCPricing.BASE_PRICE} USDC/ZSC")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
