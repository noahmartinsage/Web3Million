#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million ULTRA FAST - 超频策略
专为低波动率设计，阈值降至 0.1%！
"""
import json, time, sys, io, math
from datetime import datetime
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("⚡⚡⚡ Web3Million ULTRA FAST - 超频策略 ⚡⚡⚡")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("特点：0.1 秒扫描 + 0.1% 触发 + 立即成交")
print("=" * 80)

with open('okx_config.json') as f:
    config = json.load(f)

okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': False,
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)
okx.session.trust_env = False
okx.session.proxies = {}

print("✅ OKX 测试网连接成功")

# 超频参数
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
PRICE_CHANGE_THRESHOLD = 0.001  # 0.1% 触发！
LEVERAGE = 50
POSITION_SIZE = 0.30  # 30% 仓位
STOP_LOSS = 0.03
TAKE_PROFIT = 0.10

state = {
    'balance': 0.0,
    'initial_balance': 0.0,
    'trades': [],
    'scan_count': 0,
    'price_history': {},
}

def get_balance():
    try:
        b = okx.fetch_balance()
        return float(b['total'].get('USDT', 0))
    except:
        return 0.0

def get_position(symbol):
    try:
        positions = okx.fetch_positions()
        for pos in positions:
            if pos['symbol'] == symbol:
                return pos
        return None
    except:
        return None

def open_position(symbol, side, amount):
    try:
        okx.set_leverage(LEVERAGE, symbol)
        order = okx.create_order(symbol, 'market', side, amount)
        print(f"⚡⚡⚡ ULTRA FAST 开仓 {side} {symbol} {amount:.6f} @ {order.get('price', '市价')}")
        return order
    except Exception as e:
        print(f"❌ 开仓失败：{e}")
        return None

def close_position(symbol):
    try:
        pos = get_position(symbol)
        if pos and float(pos.get('contracts', 0)) > 0:
            side = pos.get('side', '')
            close_side = 'sell' if side == 'buy' else 'buy'
            order = okx.create_order(symbol, 'market', close_side, float(pos['contracts']))
            print(f"✅ 平仓 {symbol}")
            return order
    except:
        pass
    return None

def main():
    print("\n🚀 超频策略启动！")
    print(f"触发阈值：{PRICE_CHANGE_THRESHOLD*100}% (0.1% 超低！)")
    print(f"扫描速度：0.1 秒 (每秒 10 次！)")
    print(f"杠杆：{LEVERAGE}x")
    print(f"仓位：{POSITION_SIZE*100}%")
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
            
            if time.time() - last_print >= 2:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] 扫描 #{state['scan_count']} | 余额：${balance:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | 交易：{len(state['trades'])}笔")
                last_print = time.time()
            
            for symbol in SYMBOLS:
                try:
                    ohlcv = okx.fetch_ohlcv(symbol, '1m', limit=3)
                    if len(ohlcv) < 2:
                        continue
                    
                    current_price = ohlcv[-1][4]
                    old_price = ohlcv[-2][4]
                    price_change = (current_price - old_price) / old_price
                    
                    pos = get_position(symbol)
                    has_position = pos and float(pos.get('contracts', 0)) > 0
                    
                    if abs(price_change) >= PRICE_CHANGE_THRESHOLD and not has_position:
                        direction = 'buy' if price_change > 0 else 'sell'
                        print(f"\n⚡⚡⚡ 超频信号！{symbol} {direction.upper()} | 1 分钟变化:{price_change*100:.2f}%")
                        
                        position_size = (balance * POSITION_SIZE) / current_price
                        if position_size > 0:
                            open_position(symbol, direction, position_size)
                            state['trades'].append({
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'symbol': symbol,
                                'direction': direction,
                                'price': current_price,
                                'reason': f"1 分钟{direction} {price_change*100:.2f}%"
                            })
                    
                    if has_position:
                        entry_price = float(pos.get('entryPrice', 0))
                        side = pos.get('side', '')
                        unrealized_pnl = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                        if side == 'sell':
                            unrealized_pnl = -unrealized_pnl
                        
                        if unrealized_pnl <= -STOP_LOSS:
                            print(f"⚠️ 止损！{symbol}")
                            close_position(symbol)
                        elif unrealized_pnl >= TAKE_PROFIT:
                            print(f"🎯 止盈！{symbol}")
                            close_position(symbol)
                except:
                    continue
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n🛑 手动停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(0.05)

if __name__ == "__main__":
    main()
