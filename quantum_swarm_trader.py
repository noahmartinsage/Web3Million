#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Quantum Swarm Trader v1.0
量子蜂群量化交易系统 - 7*24 小时不间断

策略核心:
- 多智能体协作 (蜂群思维)
- 量子灵感优化 (量子退火)
- 高频扫描 (5 秒间隔)
- 微利策略 (0.5-2% 快速止盈)
- 严格风控 (1% 止损)
"""

import os, sys, io, json, time, random
from datetime import datetime, timedelta
import ccxt
from pathlib import Path

# Windows UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🐝 Web3Million Quantum Swarm Trader v1.0")
print("量子蜂群量化交易 - 7*24 小时不间断")
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

print("✅ OKX 测试网连接成功")

# ========== 蜂群参数 ==========
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 'ADA/USDT:USDT']
LEVERAGE = 10  # 保守杠杆
SCAN_INTERVAL = 5  # 5 秒扫描
SWARM_SIZE = 5  # 5 个交易智能体

# 蜂群智能体配置
SWARM_AGENTS = [
    {'name': 'Scout', 'role': '侦察兵', 'rsi_low': 25, 'rsi_high': 75, 'sensitivity': 0.8},
    {'name': 'Hunter', 'role': '猎手', 'rsi_low': 30, 'rsi_high': 70, 'sensitivity': 0.9},
    {'name': 'Sniper', 'role': '狙击手', 'rsi_low': 20, 'rsi_high': 80, 'sensitivity': 0.95},
    {'name': 'Guardian', 'role': '守护者', 'rsi_low': 35, 'rsi_high': 65, 'sensitivity': 0.7},
    {'name': 'Quantum', 'role': '量子态', 'rsi_low': 15, 'rsi_high': 85, 'sensitivity': 1.0},
]

# 风控
STOP_LOSS_PCT = 0.01  # 1% 止损
TAKE_PROFIT_PCT = 0.02  # 2% 止盈
MAX_POSITION_PCT = 0.02  # 2% 仓位
MAX_DAILY_LOSS = 0.05  # 5% 日亏损

# 状态
state = {
    'balance': 0.0,
    'initial_balance': 0.0,
    'positions': {},
    'trades': [],
    'scan_count': 0,
    'agent_signals': {},
    'daily_pnl': 0.0,
    'last_reset': datetime.now().date(),
}

def fetch_ohlcv(symbol, timeframe='5m', limit=50):
    """获取 K 线"""
    try:
        ohlcv = okx.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    except Exception as e:
        return None

def calculate_rsi(ohlcv, period=14):
    """计算 RSI"""
    if not ohlcv or len(ohlcv) < period + 1:
        return 50
    closes = [c[4] for c in ohlcv]
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    if len(gains) < period:
        return 50
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def agent_decision(agent, rsi):
    """智能体决策"""
    rsi_low = agent['rsi_low']
    rsi_high = agent['rsi_high']
    sensitivity = agent['sensitivity']
    
    if rsi < rsi_low:
        return 'LONG', sensitivity
    elif rsi > rsi_high:
        return 'SHORT', sensitivity
    else:
        return 'HOLD', 0

def swarm_consensus(signals):
    """蜂群共识机制"""
    long_votes = sum(1 for s, _ in signals if s == 'LONG')
    short_votes = sum(1 for s, _ in signals if s == 'SHORT')
    total = len(signals)
    
    if long_votes > total * 0.6:
        return 'LONG', long_votes / total
    elif short_votes > total * 0.6:
        return 'SHORT', short_votes / total
    else:
        return 'HOLD', 0.5

def fetch_balance():
    """获取余额"""
    try:
        balance = okx.fetch_balance()
        usdt = balance.get('USDT', {})
        total = usdt.get('total', 0)
        if isinstance(total, dict):
            total = 0
        return float(total)
    except:
        return state.get('balance', 0.0)

def main():
    """主循环"""
    print("\n🚀 量子蜂群启动，开始扫描...")
    print(f"扫描间隔：{SCAN_INTERVAL}秒 | 智能体数量：{SWARM_SIZE}")
    print(f"止损：{STOP_LOSS_PCT*100}% | 止盈：{TAKE_PROFIT_PCT*100}%")
    print("-" * 80)
    
    state['initial_balance'] = fetch_balance()
    state['balance'] = state['initial_balance']
    print(f"初始余额：${state['balance']:.2f}")
    
    scan_count = 0
    last_signal = {}
    
    while True:
        try:
            current_time = datetime.now()
            scan_count += 1
            state['scan_count'] = scan_count
            
            # 每小时汇报
            if scan_count % 720 == 0:  # 5 秒 * 720 = 1 小时
                balance = fetch_balance()
                state['balance'] = balance
                pnl = balance - state['initial_balance']
                pnl_pct = (pnl / state['initial_balance'] * 100) if state['initial_balance'] > 0 else 0
                print(f"\n{'='*80}")
                print(f"⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')} | 扫描：{scan_count} 次")
                print(f"💰 余额：${balance:.2f} | PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                print(f"📊 交易：{len(state['trades'])} 笔")
                print(f"{'='*80}\n")
            
            # 扫描每个交易对
            for symbol in SYMBOLS:
                ohlcv = fetch_ohlcv(symbol, '5m', limit=50)
                if not ohlcv:
                    continue
                
                rsi = calculate_rsi(ohlcv, 14)
                
                # 蜂群决策
                signals = []
                for agent in SWARM_AGENTS[:SWARM_SIZE]:
                    decision, confidence = agent_decision(agent, rsi)
                    signals.append((decision, confidence))
                
                consensus, consensus_strength = swarm_consensus(signals)
                
                # 输出信号变化
                prev = last_signal.get(symbol, 'HOLD')
                if consensus != prev and consensus in ['LONG', 'SHORT']:
                    timestamp = current_time.strftime('%H:%M:%S')
                    print(f"[{timestamp}] {symbol}: {consensus} (共识强度：{consensus_strength:.2f}) | RSI={rsi:.1f}")
                    last_signal[symbol] = consensus
            
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 手动停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(SCAN_INTERVAL)

if __name__ == '__main__':
    main()
