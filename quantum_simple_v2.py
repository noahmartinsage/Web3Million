#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子蜂群 - 简化测试版
最小化代码，确保能运行
"""
import sys, io, os
# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os, json, time, random, threading, ccxt
from datetime import datetime

for v in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy']:
    os.environ.pop(v, None)

print("🚀 量子蜂群启动...")

# 连接 OKX
with open('okx_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

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
print("✅ OKX 连接成功")

# 简单智能体
class Agent:
    def __init__(self, id, symbol, leverage):
        self.id = id
        self.symbol = symbol
        self.leverage = leverage
        self.balance = 10.0
        self.pnl = 0.0
        self.running = True
        print(f"🆕 智能体#{id} {symbol} {leverage}x ${self.balance}")
    
    def run(self):
        scan = 0
        while self.running:
            try:
                ticker = okx.fetch_ticker(self.symbol)
                price = ticker['last']
                scan += 1
                if scan % 10 == 0:
                    print(f"#{self.id} {self.symbol} ${price:.2f} 扫描:{scan} PnL:${self.pnl:.4f}")
                time.sleep(3)
            except Exception as e:
                print(f"#{self.id} 错误：{e}")
                time.sleep(5)

# 创建 5 个智能体
agents = []
symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
for i in range(5):
    a = Agent(i+1, random.choice(symbols), random.randint(25, 50))
    agents.append(a)
    t = threading.Thread(target=a.run, daemon=True)
    t.start()
    time.sleep(0.5)

print(f"\n✅ {len(agents)}个智能体运行中，30 秒汇报一次...\n")

# 主循环
start = datetime.now()
while True:
    time.sleep(30)
    total_bal = sum(a.balance for a in agents)
    total_pnl = sum(a.pnl for a in agents)
    runtime = datetime.now() - start
    print(f"\n{'='*50}")
    print(f"🐝 蜂巢状态 | 运行:{runtime}")
    print(f"智能体:{len(agents)} | 总资金:${total_bal:.2f} | PnL:${total_pnl:.4f}")
    print(f"{'='*50}\n")
