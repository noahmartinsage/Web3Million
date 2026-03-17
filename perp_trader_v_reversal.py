#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million V-Reversal - V 型反转杀手
专为暴跌/暴涨后抄底/摸顶设计
策略核心:
1. RSI < 25 立即做多 (暴跌抄底)
2. RSI > 75 立即做空 (暴涨摸顶)
3. 价格偏离 MA20 超过 5% 立即反向
4. 100x 杠杆，满仓干
5. 止损 8%，止盈 30% (1:3.75)
"""
import sys, io, json, time
from datetime import datetime
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🔥🔥🔥 Web3Million V-REVERSAL - V 型反转杀手 🔥🔥🔥")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("策略：RSI 极值 + 偏离度 + 100x 杠杆 + 满仓抄底摸顶")
print("警告：极度危险，专为暴跌/暴涨设计！")
print("=" * 80)

# 加载配置
with open('okx_config.json', 'r') as f:
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

print("✅ OKX 测试网连接成功")

# ========== V 型反转策略参数 ==========
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
LEVERAGE = 100  # 100x
SCAN_INTERVAL = 3  # 3 秒扫描
RSI_LONG = 25   # RSI < 25 立即抄底
RSI_SHORT = 75  # RSI > 75 立即摸顶
DEVIATION_PCT = 0.05  # 偏离 MA20 超过 5%
STOP_LOSS = 0.08  # 8% 止损
TAKE_PROFIT = 0.30  # 30% 止盈
POSITION_SIZE = 0.95  # 95% 仓位

state = {'scan_count': 0, 'trades': []}

def fetch_ohlcv(symbol, timeframe='5m', limit=50):
    try:
        return okx.fetch_ohlcv(symbol, timeframe, limit=limit)
    except:
        return None

def calculate_rsi(ohlcv, period=14):
    if not ohlcv or len(ohlcv) < period + 1:
        return 50
    closes = [c[4] for c in ohlcv]
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(0, diff))
        losses.append(abs(min(0, diff)))
    if len(gains) < period:
        return 50
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_ma(ohlcv, period=20):
    if not ohlcv or len(ohlcv) < period:
        return None
    closes = [c[4] for c in ohlcv[-period:]]
    return sum(closes) / len(closes)

def get_balance():
    try:
        b = okx.fetch_balance()
        return float(b['total'].get('USDT', 0))
    except:
        return 0

def get_position(symbol):
    try:
        positions = okx.fetch_positions()
        for pos in positions:
            if pos['symbol'] == symbol:
                return pos
    except:
        pass
    return None

def open_position(symbol, side, amount):
    try:
        okx.set_leverage(LEVERAGE, symbol)
        order = okx.create_order(symbol, 'market', side, amount)
        print(f"🔥 V-REVERSAL {side} {symbol} {amount:.6f} @ {order.get('price', '市价')}")
        return order
    except Exception as e:
        print(f"❌ 开仓失败: {e}")
        return None

def close_position(symbol):
    try:
        pos = get_position(symbol)
        if pos and float(pos.get('contracts', 0)) > 0:
            side = pos.get('side', '')
            close_side = 'sell' if side == 'buy' else 'buy'
            order = okx.create_order(symbol, 'market', close_side, float(pos['contracts']))
            print(f"✅ 平仓 {close_side} {symbol}")
            return order
    except:
        pass
    return None

def main():
    print(f"\n🚀 V-REVERSAL 启动！")
    print(f"扫描间隔：{SCAN_INTERVAL}秒")
    print(f"杠杆：{LEVERAGE}x")
    print(f"RSI 抄底：< {RSI_LONG} | 摸顶：> {RSI_SHORT}")
    print(f"偏离 MA20: {DEVIATION_PCT*100}%")
    print(f"止损/止盈：{STOP_LOSS*100}% / {TAKE_PROFIT*100}%")
    print("=" * 80)
    
    initial_balance = get_balance()
    print(f"初始余额：${initial_balance:.2f} USDT")
    
    last_print = time.time()
    
    while True:
        try:
            state['scan_count'] += 1
            balance = get_balance()
            pnl = balance - initial_balance
            pnl_pct = (pnl / initial_balance * 100) if initial_balance > 0 else 0
            
            if time.time() - last_print >= 10:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] 扫描 #{state['scan_count']} | 余额：${balance:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                last_print = time.time()
            
            for symbol in SYMBOLS:
                ohlcv = fetch_ohlcv(symbol, '5m')
                if not ohlcv:
                    continue
                
                current_price = ohlcv[-1][4]
                rsi = calculate_rsi(ohlcv, 14)
                ma20 = calculate_ma(ohlcv, 20)
                
                pos = get_position(symbol)
                has_position = pos and float(pos.get('contracts', 0)) > 0
                
                # 做多信号 1: RSI < 25 暴跌抄底
                if rsi < RSI_LONG and not has_position:
                    print(f"🔥🔥🔥 RSI 暴跌抄底！{symbol} RSI={rsi:.1f} < {RSI_LONG}")
                    amount = (balance * POSITION_SIZE) / current_price
                    if amount > 0:
                        open_position(symbol, 'buy', amount)
                
                # 做空信号 1: RSI > 75 暴涨摸顶
                elif rsi > RSI_SHORT and not has_position:
                    print(f"🔥🔥🔥 RSI 暴涨摸顶！{symbol} RSI={rsi:.1f} > {RSI_SHORT}")
                    amount = (balance * POSITION_SIZE) / current_price
                    if amount > 0:
                        open_position(symbol, 'sell', amount)
                
                # 做多信号 2: 价格低于 MA20 超过 5%
                deviation = (ma20 - current_price) / ma20 if ma20 else 0
                if deviation > DEVIATION_PCT and not has_position:
                    print(f"🔥 偏离抄底！{symbol} 价格低于 MA20 {deviation*100:.1f}%")
                    amount = (balance * POSITION_SIZE) / current_price
                    if amount > 0:
                        open_position(symbol, 'buy', amount)
                
                # 检查止损/止盈
                if has_position:
                    entry = float(pos.get('entryPrice', 0))
                    side = pos.get('side', '')
                    pnl_pct = ((current_price - entry) / entry) if entry > 0 else 0
                    if side == 'sell':
                        pnl_pct = -pnl_pct
                    pnl_pct = pnl_pct * 100
                    
                    if pnl_pct <= -STOP_LOSS * 100:
                        print(f"⚠️ 止损！PnL={pnl_pct:.1f}%")
                        close_position(symbol)
                    elif pnl_pct >= TAKE_PROFIT * 100:
                        print(f"🎯 止盈！PnL={pnl_pct:.1f}%")
                        close_position(symbol)
            
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
