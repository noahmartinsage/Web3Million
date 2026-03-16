#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 疯狂模式实时监控面板
每 5 秒汇报一次双系统状态和交易信号
"""
import json, sys, io, time
from datetime import datetime
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🔥 Web3Million 疯狂模式实时监控面板")
print("=" * 80)

# 加载配置
with open('okx_config.json', 'r') as f:
    config = json.load(f)

okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)

initial_balance = 1288.57
report_count = 0

while True:
    try:
        report_count += 1
        balance_data = okx.fetch_balance()
        balance = float(balance_data['total'].get('USDT', 0))
        pnl = balance - initial_balance
        pnl_pct = (pnl / initial_balance * 100)
        
        # 获取持仓
        positions = okx.fetch_positions()
        active_positions = [p for p in positions if float(p.get('contracts', 0)) > 0]
        
        # 获取当前价格
        btc = okx.fetch_ticker('BTC/USDT:USDT')
        eth = okx.fetch_ticker('ETH/USDT:USDT')
        sol = okx.fetch_ticker('SOL/USDT:USDT')
        
        print("\n" + "=" * 80)
        print(f"📊 第 {report_count} 次汇报 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print(f"💰 余额：${balance:.2f} USDT | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        print(f"📈 市场价格:")
        print(f"   BTC: ${btc['last']} ({btc.get('percentage', 0):+.2f}%)")
        print(f"   ETH: ${eth['last']} ({eth.get('percentage', 0):+.2f}%)")
        print(f"   SOL: ${sol['last']} ({sol.get('percentage', 0):+.2f}%)")
        print(f"📊 持仓数量：{len(active_positions)}")
        
        if active_positions:
            for p in active_positions:
                entry = float(p.get('entryPrice', 0))
                current = float(p.get('markPrice', 0))
                pnl_pos = ((current - entry) / entry * 100) if p.get('side') == 'buy' else ((entry - current) / entry * 100)
                print(f"   {p['symbol']} {p.get('side', '').upper()} @ ${entry} | 未实现盈亏：{pnl_pos:+.2f}%")
        else:
            print("   无未平仓合约 (等待信号中)")
        
        print("=" * 80)
        print("🔥 疯狂系统状态:")
        print("   v9.0 MEGA: 100x 杠杆 | RSI <30/>70 入场 | 扫描中...")
        print("   量子蜂群 FRENZY: 75x 杠杆 | 1 秒扫描 | 20 智能体 | 反手策略激活")
        print("=" * 80)
        
        time.sleep(10)  # 每 10 秒汇报一次
        
    except KeyboardInterrupt:
        print("\n🛑 监控停止")
        break
    except Exception as e:
        print(f"⚠️ 监控异常：{e}")
        time.sleep(5)
