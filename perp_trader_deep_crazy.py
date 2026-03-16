#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Deep Crazy - 深度疯狂版
策略核心：趋势跟踪 + 动量突破 + 100x 杠杆
- 不再等待 RSI 极端值
- 价格突破 MA20 立即做多
- 价格跌破 MA20 立即做空
- 100x 杠杆，满仓干
- 止损 5%，止盈 20% (1:4)
"""
import os, sys, io, json, time, math
from datetime import datetime
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🔥🔥🔥 Web3Million DEEP CRAZY - 深度疯狂版 🔥🔥🔥")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("策略：趋势跟踪 + 动量突破 + 100x 杠杆 + 满仓干")
print("警告：极度危险，可能 1 分钟翻倍或归零！")
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

# ========== 深度疯狂策略参数 ==========
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
LEVERAGE = 100  # 100x 疯狂杠杆
TIMEFRAME = '5m'  # 5 分钟 K 线
SCAN_INTERVAL = 5  # 5 秒扫描一次
MAX_POSITION_PCT = 0.95  # 95% 仓位满仓干！
STOP_LOSS_PCT = 0.05  # 5% 止损
TAKE_PROFIT_PCT = 0.20  # 20% 止盈 (1:4)

# 状态
state = {
    'balance': 0.0,
    'initial_balance': 0.0,
    'trades': [],
    'scan_count': 0,
}

def fetch_ohlcv(symbol, timeframe='5m', limit=50):
    """获取 K 线"""
    try:
        ohlcv = okx.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    except Exception as e:
        return None

def calculate_ma(data, period=20):
    """计算 MA20"""
    if not data or len(data) < period:
        return None
    closes = [c[4] for c in data[-period:]]
    return sum(closes) / len(closes)

def calculate_momentum(data, period=5):
    """计算动量 (当前价 - N 周期前价) / N 周期前价"""
    if not data or len(data) < period + 1:
        return 0
    current = data[-1][4]
    past = data[-period-1][4]
    return (current - past) / past * 100

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
        print(f"🔥🔥🔥 DEEP CRAZY 开仓 {side} {symbol} {amount:.6f} @ {order.get('price', '市价')}")
        return order
    except Exception as e:
        print(f"❌ 开仓失败 {symbol}: {e}")
        return None

def close_position(symbol):
    """平仓"""
    try:
        pos = get_position(symbol)
        if pos and float(pos.get('contracts', 0)) > 0:
            side = pos.get('side', '')
            close_side = 'sell' if side == 'buy' else 'buy'
            order = okx.create_order(symbol, 'market', close_side, float(pos['contracts']))
            print(f"✅ 平仓 {close_side} {symbol}")
            return order
    except Exception as e:
        pass
    return None

def main():
    print("\n🚀🚀🚀 DEEP CRAZY 深度疯狂模式启动！")
    print(f"扫描间隔：{SCAN_INTERVAL}秒")
    print(f"杠杆：{LEVERAGE}x")
    print(f"仓位：{MAX_POSITION_PCT*100}% 满仓干！")
    print(f"止损/止盈：{STOP_LOSS_PCT*100}% / {TAKE_PROFIT_PCT*100}%")
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
            
            # 每 10 秒打印状态
            if time.time() - last_print >= 10:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] 扫描 #{state['scan_count']} | 余额：${balance:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                last_print = time.time()
            
            # 扫描每个交易对
            for symbol in SYMBOLS:
                ohlcv = fetch_ohlcv(symbol, TIMEFRAME)
                if not ohlcv:
                    continue
                
                current_price = ohlcv[-1][4]
                ma20 = calculate_ma(ohlcv, 20)
                momentum = calculate_momentum(ohlcv, 5)
                
                if not ma20:
                    continue
                
                # 检查持仓
                pos = get_position(symbol)
                has_position = pos and float(pos.get('contracts', 0)) > 0
                
                # 做多信号：价格 > MA20 且 动量 > 0
                if not has_position and current_price > ma20 and momentum > 0:
                    print(f"🔥 突破信号！{symbol} 价格${current_price} > MA20${ma20:.2f} 动量{momentum:.2f}%")
                    position_size = (balance * MAX_POSITION_PCT) / current_price
                    if position_size > 0:
                        open_position(symbol, 'buy', position_size)
                
                # 做空信号：价格 < MA20 且 动量 < 0
                elif not has_position and current_price < ma20 and momentum < 0:
                    print(f"🔥 跌破信号！{symbol} 价格${current_price} < MA20${ma20:.2f} 动量{momentum:.2f}%")
                    position_size = (balance * MAX_POSITION_PCT) / current_price
                    if position_size > 0:
                        open_position(symbol, 'sell', position_size)
                
                # 检查止损/止盈
                if has_position:
                    entry_price = float(pos.get('entryPrice', 0))
                    side = pos.get('side', '')
                    unrealized_pnl = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                    if side == 'sell':
                        unrealized_pnl = -unrealized_pnl
                    
                    pnl_pct_current = unrealized_pnl * 100
                    
                    # 止损
                    if pnl_pct_current <= -STOP_LOSS_PCT * 100:
                        print(f"⚠️ 触发止损！PnL={pnl_pct_current:.2f}%")
                        close_position(symbol)
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
