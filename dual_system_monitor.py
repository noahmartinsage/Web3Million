#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 双系统监控器
监控 v9.0 Ultra 和 量子蜂群 交易系统的实时状态
"""
import json
import time
from datetime import datetime
from pathlib import Path
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_balance():
    """检查 OKX 测试网余额"""
    try:
        import ccxt
        with open('okx_config.json', 'r') as f:
            config = json.load(f)
        
        okx = ccxt.okx({
            'apiKey': config['api_key'],
            'secret': config['secret_key'],
            'password': config['passphrase'],
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        okx.set_sandbox_mode(True)
        
        balance = okx.fetch_balance()
        return float(balance['total'].get('USDT', 0))
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 70)
    print("Web3Million 双系统监控器")
    print("v9.0 Ultra 激进策略 + 量子蜂群量化交易")
    print("=" * 70)
    
    initial_balance = check_balance()
    print(f"初始余额：{initial_balance} USDT")
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 持续监控
    check_interval = 60  # 60 秒检查一次
    last_balance = initial_balance
    
    while True:
        try:
            time.sleep(check_interval)
            current_time = datetime.now().strftime('%H:%M:%S')
            balance = check_balance()
            
            if isinstance(balance, (int, float)):
                pnl = balance - last_balance
                total_pnl = balance - initial_balance
                change = (pnl / last_balance * 100) if last_balance > 0 else 0
                
                print(f"\n[{current_time}] 余额：{balance:.2f} USDT | PnL: {pnl:+.2f} ({change:+.2f}%) | 总 PnL: {total_pnl:+.2f} USDT")
                last_balance = balance
            else:
                print(f"[{current_time}] 查询失败：{balance}")
                
        except KeyboardInterrupt:
            print("\n监控停止")
            break
        except Exception as e:
            print(f"[Error] {e}")

if __name__ == "__main__":
    main()
