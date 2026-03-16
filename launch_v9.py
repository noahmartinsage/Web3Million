#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动 v9.0 Ultra 进行测试"""
import ccxt, json, datetime, sys, io

# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🚀 Web3Million v9.0 Ultra - 启动测试")
print(f"启动时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 加载配置
with open('okx_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 初始化 OKX
okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)
okx.session.trust_env = False
okx.session.proxies = {}

print("\n✅ OKX 测试网连接成功")

# 获取余额
balance = okx.fetch_balance()
usdt = balance.get('USDT', {})
total = usdt.get('total', 0) if isinstance(usdt.get('total'), (int, float)) else 0
free = usdt.get('free', 0) if isinstance(usdt.get('free'), (int, float)) else 0
print(f"💰 OKX 测试网余额：USDT ${total:.2f} (可用：${free:.2f})")

# 获取当前市场数据
print("\n📊 当前市场扫描...")
symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
for symbol in symbols:
    try:
        ticker = okx.fetch_ticker(symbol)
        pct = ticker.get('percentage', 0)
        print(f"{symbol}: ${ticker['last']:,.2f} | 24h 变化：{pct:+.2f}%")
    except Exception as ex:
        print(f"{symbol}: 获取失败 - {ex}")

print("\n" + "=" * 80)
print("✅ 系统就绪，准备启动 v9.0 Ultra 进行小额测试...")
print("=" * 80)

# 启动 v9.0 Ultra
print("\n🚀 启动 v9.0 Ultra 主程序...")
import subprocess
result = subprocess.run(['python', 'perp_trader_v9_ultra.py'], 
                       capture_output=True, text=True, timeout=60)
print(result.stdout)
if result.stderr:
    print("错误:", result.stderr)
