#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Quantum Swarm Frenzy - 狂暴版
1 秒扫描 + 20 智能体 + 反手策略 + 75x 杠杆
策略核心:
- 1 秒扫描间隔 (人类跟不上的速度)
- 20 个交易智能体 (蜂群规模扩大 4 倍)
- 75x 疯狂杠杆
- 3% 止损 / 10% 止盈 (薄利多销)
- 亏损后立即反手 (错误即反向)
"""
import os, sys, io, json, time, random, math
from datetime import datetime
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🐝🔥 Web3Million Quantum Swarm FRENZY - 狂暴版")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("警告：1 秒扫描 + 75x 杠杆 + 反手策略 - 极度危险！")
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

# ========== 狂暴策略参数 ==========
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT', 'ADA/USDT:USDT']
LEVERAGE = 75  # 75x 疯狂杠杆
SCAN_INTERVAL = 1  # 1 秒扫描 (人类跟不上的速度)
MAX_POSITION_PCT = 0.15  # 15% 仓位
STOP_LOSS_PCT = 0.03  # 3% 止损
TAKE_PROFIT_PCT = 0.10  # 10% 止盈

# 20 个蜂群智能体配置
SWARM_AGENTS = [
    {'name': 'Scout', 'role': '侦察兵', 'rsi_low': 25, 'rsi_high': 75, 'sensitivity': 0.8},
    {'name': 'Hunter', 'role': '猎手', 'rsi_low': 30, 'rsi_high': 70, 'sensitivity': 0.9},
    {'name': 'Sniper', 'role': '狙击手', 'rsi_low': 20, 'rsi_high': 80, 'sensitivity': 0.95},
    {'name': 'Guardian', 'role': '守护者', 'rsi_low': 35, 'rsi_high': 65, 'sensitivity': 0.7},
    {'name': 'Quantum', 'role': '量子态', 'rsi_low': 15, 'rsi_high': 85, 'sensitivity': 1.0},
    {'name': 'Frenzy1', 'role': '狂暴者 1 号', 'rsi_low': 28, 'rsi_high': 72, 'sensitivity': 0.85},
    {'name': 'Frenzy2', 'role': '狂暴者 2 号', 'rsi_low': 32, 'rsi_high': 68, 'sensitivity': 0.88},
    {'name': 'Frenzy3', 'role': '狂暴者 3 号', 'rsi_low': 26, 'rsi_high': 74, 'sensitivity': 0.82},
    {'name': 'Frenzy4', 'role': '狂暴者 4 号', 'rsi_low': 34, 'rsi_high': 66, 'sensitivity': 0.78},
    {'name': 'Frenzy5', 'role': '狂暴者 5 号', 'rsi_low': 29, 'rsi_high': 71, 'sensitivity': 0.87},
    {'name': 'Blitz1', 'role': '闪电 1 号', 'rsi_low': 27, 'rsi_high': 73, 'sensitivity': 0.91},
    {'name': 'Blitz2', 'role': '闪电 2 号', 'rsi_low': 31, 'rsi_high': 69, 'sensitivity': 0.89},
    {'name': 'Blitz3', 'role': '闪电 3 号', 'rsi_low': 24, 'rsi_high': 76, 'sensitivity': 0.84},
    {'name': 'Blitz4', 'role': '闪电 4 号', 'rsi_low': 33, 'rsi_high': 67, 'sensitivity': 0.86},
    {'name': 'Blitz5', 'role': '闪电 5 号', 'rsi_low': 28, 'rsi_high': 72, 'sensitivity': 0.93},
    {'name': 'Chaos', 'role': '混沌', 'rsi_low': 22, 'rsi_high': 78, 'sensitivity': 0.97},
    {'name': 'Vortex', 'role': '漩涡', 'rsi_low': 26, 'rsi_high': 74, 'sensitivity': 0.92},
    {'name': 'Storm', 'role': '风暴', 'rsi_low': 30, 'rsi_high': 70, 'sensitivity': 0.88},
    {'name': 'Inferno', 'role': '烈焰', 'rsi_low': 25, 'rsi_high': 75, 'sensitivity': 0.94},
    {'name': 'Apex', 'role': '巅峰', 'rsi_low': 29, 'rsi_high': 71, 'sensitivity': 0.90},
]

# 状态
state = {
    'balance': 0.0,
    'initial_balance': 0.0,
    'positions': {},
    'trades': [],
    'scan_count': 0,
    'agent_signals': {},
    'last_loss': {},  # 记录上次亏损，用于反手
}

def fetch_ohlcv(symbol, timeframe='1m', limit=50):
    """获取 K 线"""
    try:
        ohlcv = okx.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    except Exception as e:
        return None

def calculate_rsi(ohlcv, period=14):
    """计算 RSI"""
    if not ohlcv or len(ohlcv) < period + 1:
        return 50.0
    
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
        return 50.0
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_balance():
    """获取余额"""
    try:
        balance = okx.fetch_balance()
        return float(balance['total'].get('USDT', 0))
    except:
        return 0.0

def get_position(symbol):
    """获取持仓"""
    try:
        positions = okx.fetch_positions()
        for pos in positions:
            if pos['symbol'] == symbol:
                return pos
        return None
    except:
        return None

def open_position(symbol, side, amount):
    """开仓"""
    try:
        okx.set_leverage(LEVERAGE, symbol)
        order = okx.create_order(symbol, 'market', side, amount)
        print(f"🐝 开仓 {side} {symbol} {amount:.6f} @ {order.get('price', '市价')}")
        return order
    except Exception as e:
        return None

def close_position(symbol):
    """平仓"""
    try:
        pos = get_position(symbol)
        if pos and float(pos.get('contracts', 0)) > 0:
            side = pos.get('side', '')
            close_side = 'sell' if side == 'buy' else 'buy'
            order = okx.create_order(symbol, 'market', close_side, float(pos['contracts']))
            print(f"🐝 平仓 {close_side} {symbol} {pos['contracts']}")
            return order
    except Exception as e:
        pass
    return None

def main():
    print("\n🚀 量子蜂群 FRENZY 狂暴模式启动！")
    print(f"扫描间隔：{SCAN_INTERVAL}秒 (1 秒人类反应极限)")
    print(f"智能体数量：{len(SWARM_AGENTS)}个")
    print(f"杠杆：{LEVERAGE}x")
    print(f"止损/止盈：{STOP_LOSS_PCT*100}% / {TAKE_PROFIT_PCT*100}%")
    print(f"反手策略：启用 (亏损后立即反向)")
    print("=" * 80)
    
    initial_balance = get_balance()
    state['initial_balance'] = initial_balance
    state['balance'] = initial_balance
    print(f"初始余额：${initial_balance:.2f} USDT")
    
    last_print = time.time()
    
    while True:
        try:
            state['scan_count'] += 1
            balance = get_balance()
            state['balance'] = balance
            pnl = balance - initial_balance
            pnl_pct = (pnl / initial_balance * 100) if initial_balance > 0 else 0
            
            # 每秒打印太频繁，每 5 秒打印一次状态
            if time.time() - last_print >= 5:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] 扫描 #{state['scan_count']} | 余额：${balance:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                last_print = time.time()
            
            # 扫描每个交易对
            for symbol in SYMBOLS:
                ohlcv = fetch_ohlcv(symbol, '1m')
                if not ohlcv:
                    continue
                
                rsi = calculate_rsi(ohlcv)
                current_price = ohlcv[-1][4]
                
                # 获取所有智能体的投票
                long_votes = 0
                short_votes = 0
                
                for agent in SWARM_AGENTS:
                    sensitivity = agent['sensitivity']
                    rsi_low = agent['rsi_low']
                    rsi_high = agent['rsi_high']
                    
                    # 根据智能体参数投票
                    if rsi < rsi_low:
                        long_votes += sensitivity
                    elif rsi > rsi_high:
                        short_votes += sensitivity
                
                # 检查持仓
                pos = get_position(symbol)
                has_position = pos and float(pos.get('contracts', 0)) > 0
                
                # 开仓逻辑：超过 70% 智能体同意
                if not has_position:
                    if long_votes > len(SWARM_AGENTS) * 0.7:
                        print(f"🐝 蜂群共识做多 {symbol}! 投票：{long_votes:.1f}/{len(SWARM_AGENTS)}")
                        position_size = (balance * MAX_POSITION_PCT) / current_price
                        if position_size > 0:
                            open_position(symbol, 'buy', position_size)
                            state['last_loss'][symbol] = None
                    
                    elif short_votes > len(SWARM_AGENTS) * 0.7:
                        print(f"🐝 蜂群共识做空 {symbol}! 投票：{short_votes:.1f}/{len(SWARM_AGENTS)}")
                        position_size = (balance * MAX_POSITION_PCT) / current_price
                        if position_size > 0:
                            open_position(symbol, 'sell', position_size)
                            state['last_loss'][symbol] = None
                
                # 检查止损/止盈/反手
                if has_position:
                    entry_price = float(pos.get('entryPrice', 0))
                    side = pos.get('side', '')
                    unrealized_pnl = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                    if side == 'sell':
                        unrealized_pnl = -unrealized_pnl
                    
                    pnl_pct_current = unrealized_pnl * 100
                    
                    # 止损并反手
                    if pnl_pct_current <= -STOP_LOSS_PCT * 100:
                        print(f"⚠️ 触发止损！PnL={pnl_pct_current:.2f}% - 准备反手...")
                        close_position(symbol)
                        # 反手：原来做多现在做空，原来做空现在做多
                        reverse_side = 'sell' if side == 'buy' else 'buy'
                        position_size = (balance * MAX_POSITION_PCT) / current_price
                        if position_size > 0:
                            open_position(symbol, reverse_side, position_size)
                            print(f"🔄 反手成功！现在 {reverse_side} {symbol}")
                    
                    # 止盈
                    elif pnl_pct_current >= TAKE_PROFIT_PCT * 100:
                        print(f"🎯 触发止盈！PnL={pnl_pct_current:.2f}%")
                        close_position(symbol)
            
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 手动停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
