#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子蜂群 - 最简测试版
"""
import sys
print("Python version:", sys.version)
print("Starting Quantum Hive...")

import os, json, time, random, threading, ccxt
from datetime import datetime

print("Imports OK")

# 连接 OKX
try:
    with open('okx_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("Config loaded")
    
    okx = ccxt.okx({
        'apiKey': config['api_key'],
        'secret': config['secret_key'],
        'password': config['passphrase'],
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    okx.set_sandbox_mode(True)
    okx.session.trust_env = False
    print("OKX initialized")
    
    # 测试连接
    ticker = okx.fetch_ticker('BTC/USDT:USDT')
    print(f"BTC Price: ${ticker['last']}")
    
    print("\n✅ All systems ready! Starting agents...\n")
    
    # 创建 1 个测试智能体
    class SimpleAgent:
        def __init__(self, symbol):
            self.symbol = symbol
            self.scan = 0
            self.running = True
            
        def run(self):
            print(f"Agent started: {self.symbol}")
            while self.running:
                try:
                    ticker = okx.fetch_ticker(self.symbol)
                    self.scan += 1
                    if self.scan <= 3 or self.scan % 5 == 0:
                        print(f"[{self.symbol}] Scan #{self.scan} - Price: ${ticker['last']}")
                    time.sleep(5)
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(5)
    
    agent = SimpleAgent('ETH/USDT:USDT')
    t = threading.Thread(target=agent.run, daemon=True)
    t.start()
    
    print("Agent thread started, waiting...")
    
    # 主循环
    for i in range(10):
        time.sleep(3)
        print(f"Main loop: {i+1}/10")
    
    agent.running = False
    print("Done!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
