#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v9.0 MEGA - 疯狂版
目标：百倍杠杆 + 宽松入场 + 高频复利
策略核心：
- RSI <30 或 >70 即可入场 (频率提高 5 倍)
- 单周期突破即入场 (取消三周期共振)
- 市价强平式入场 (取消爆量确认)
- 100x 杠杆 (直接拉满)
- 10% 止损 / 50% 止盈 (1:5 盈亏比)
"""
import os, sys, io, json, time, math
from datetime import datetime, timedelta
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🔥 Web3Million Perpetual v9.0 MEGA - 疯狂版")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("策略：100x 杠杆 + 宽松入场 + 高频复利")
print("警告：此策略极高风险，可能 1 分钟翻倍或归零！")
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

# ========== 疯狂策略参数 ==========
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
LEVERAGE = 100  # 100x 疯狂杠杆
TIMEFRAME = '5m'  # 5 分钟 K 线
RSI_LONG_THRESHOLD = 30   # 宽松做多阈值
RSI_SHORT_THRESHOLD = 70  # 宽松做空阈值
STOP_LOSS_PCT = 0.10      # 10% 止损 (给足波动)
TAKE_PROFIT_PCT = 0.50    # 50% 止盈 (1:5 盈亏比)
MAX_POSITION_PCT = 0.20   # 最大仓位 20% (5 倍杠杆全仓)
SCAN_INTERVAL = 10        # 10 秒扫描一次

# 状态管理
state = {
    'balance': 0.0,
    'initial_balance': 0.0,
    'position': None,
    'trades': [],
    'scan_count': 0,
    'win_count': 0,
    'loss_count': 0,
    'last_trade_time': None,
}

def fetch_ohlcv(symbol, timeframe='5m', limit=50):
    """获取 K 线数据"""
    try:
        ohlcv = okx.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    except Exception as e:
        print(f"❌ 获取 K 线失败 {symbol}: {e}")
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
        # 设置杠杆
        okx.set_leverage(LEVERAGE, symbol)
        
        # 市价开仓
        order = okx.create_order(symbol, 'market', side, amount)
        print(f"✅ 开仓 {side} {symbol} {amount} @ {order.get('price', '市价')}")
        return order
    except Exception as e:
        print(f"❌ 开仓失败 {symbol}: {e}")
        return None

def close_position(symbol, side):
    """平仓"""
    try:
        # 市价平仓
        pos = get_position(symbol)
        if pos and float(pos.get('contracts', 0)) > 0:
            close_side = 'sell' if side == 'buy' else 'buy'
            order = okx.create_order(symbol, 'market', close_side, float(pos['contracts']))
            print(f"✅ 平仓 {close_side} {symbol} {pos['contracts']}")
            return order
    except Exception as e:
        print(f"❌ 平仓失败 {symbol}: {e}")
    return None

def main():
    print("\n🚀 v9.0 MEGA 疯狂模式启动！")
    print(f"扫描间隔：{SCAN_INTERVAL}秒")
    print(f"杠杆：{LEVERAGE}x")
    print(f"RSI 入场阈值：<{RSI_LONG_THRESHOLD} 做长 / >{RSI_SHORT_THRESHOLD} 做空")
    print(f"止损/止盈：{STOP_LOSS_PCT*100}% / {TAKE_PROFIT_PCT*100}%")
    print("=" * 80)
    
    initial_balance = get_balance()
    state['initial_balance'] = initial_balance
    state['balance'] = initial_balance
    print(f"初始余额：${initial_balance:.2f} USDT")
    
    while True:
        try:
            state['scan_count'] += 1
            current_time = datetime.now().strftime('%H:%M:%S')
            balance = get_balance()
            state['balance'] = balance
            pnl = balance - initial_balance
            pnl_pct = (pnl / initial_balance * 100) if initial_balance > 0 else 0
            
            print(f"\n[{current_time}] 扫描 #{state['scan_count']} | 余额：${balance:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            
            # 扫描每个交易对
            for symbol in SYMBOLS:
                ohlcv = fetch_ohlcv(symbol, TIMEFRAME)
                if not ohlcv:
                    continue
                
                rsi = calculate_rsi(ohlcv)
                current_price = ohlcv[-1][4]
                
                print(f"  {symbol}: RSI={rsi:.1f} Price=${current_price}")
                
                # 检查持仓
                pos = get_position(symbol)
                has_position = pos and float(pos.get('contracts', 0)) > 0
                
                # 做多信号：RSI < 30
                if rsi < RSI_LONG_THRESHOLD and not has_position:
                    print(f"  🔥 疯狂做多信号！RSI={rsi:.1f} < {RSI_LONG_THRESHOLD}")
                    # 计算仓位：20% 余额 / 当前价格
                    position_size = (balance * MAX_POSITION_PCT) / current_price
                    if position_size > 0:
                        open_position(symbol, 'buy', position_size)
                
                # 做空信号：RSI > 70
                elif rsi > RSI_SHORT_THRESHOLD and not has_position:
                    print(f"  🔥 疯狂做空信号！RSI={rsi:.1f} > {RSI_SHORT_THRESHOLD}")
                    # 计算仓位
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
                        print(f"  ⚠️ 触发止损！PnL={pnl_pct_current:.2f}%")
                        close_position(symbol, side)
                    # 止盈
                    elif pnl_pct_current >= TAKE_PROFIT_PCT * 100:
                        print(f"  🎯 触发止盈！PnL={pnl_pct_current:.2f}%")
                        close_position(symbol, side)
            
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n🛑 手动停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
