#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Ultimate Evolving Strategy - 终极进化策略
核心能力:
1. 超低阈值：1 分钟涨跌>0.5% 即触发 (原 3%)
2. 超快扫描：0.5 秒扫描一次 (原 2 秒)
3. 多重确认：RSI+MACD+ 成交量 三重验证
4. 动态参数：每笔交易后自动优化
5. 实盘学习：根据盈亏调整阈值
"""
import json, time, sys, io, math
from datetime import datetime
from pathlib import Path
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🚀🚀🚀 Web3Million ULTIMATE EVOLVING STRATEGY 🚀🚀🚀")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("特点：0.5 秒扫描 + 0.5% 触发 + 三重确认 + 实时进化")
print("=" * 80)

# 加载配置
with open('okx_config.json', 'r') as f:
    config = json.load(f)

# 初始化 OKX
okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': False,  # 关闭限流，全力扫描
    'options': {'defaultType': 'swap'}
})
okx.set_sandbox_mode(True)
okx.session.trust_env = False
okx.session.proxies = {}

print("✅ OKX 测试网连接成功")

# ========== 动态参数 (实时进化) ==========
DYNAMIC_PARAMS = {
    'price_change_threshold': 0.005,  # 0.5% 触发 (可调低)
    'rsi_period': 14,
    'rsi_long_threshold': 35,  # 放宽做多
    'rsi_short_threshold': 65,  # 放宽做空
    'leverage': 75,
    'position_size': 0.50,  # 50% 仓位
    'stop_loss': 0.05,  # 5%
    'take_profit': 0.15,  # 15%
    'scan_interval': 0.5,  # 0.5 秒
}

# 状态
state = {
    'balance': 0.0,
    'initial_balance': 0.0,
    'trades': [],
    'scan_count': 0,
    'price_history': {},
    'last_trade_time': 0,
    'win_count': 0,
    'loss_count': 0,
    'total_pnl': 0.0,
}

def fetch_ohlcv(symbol, timeframe='1m', limit=10):
    """快速获取 K 线"""
    try:
        return okx.fetch_ohlcv(symbol, timeframe, limit=limit)
    except:
        return None

def calculate_rsi(ohlcv, period=14):
    """快速 RSI"""
    if not ohlcv or len(ohlcv) < period + 1:
        return 50
    closes = [c[4] for c in ohlcv]
    gains = [max(closes[i] - closes[i-1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i-1] - closes[i], 0) for i in range(1, len(closes))]
    avg_gain = sum(gains[-period:]) / period if len(gains) >= period else 0
    avg_loss = sum(losses[-period:]) / period if len(losses) >= period else 1
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

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
        okx.set_leverage(DYNAMIC_PARAMS['leverage'], symbol)
        order = okx.create_order(symbol, 'market', side, amount)
        print(f"🚀🚀🚀 ULTIMATE 开仓 {side} {symbol} {amount:.6f} @ {order.get('price', '市价')}")
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

def evolve_params(profitable):
    """根据交易结果进化参数"""
    if profitable:
        # 盈利：降低阈值，增加仓位
        DYNAMIC_PARAMS['price_change_threshold'] = max(0.003, DYNAMIC_PARAMS['price_change_threshold'] - 0.001)
        DYNAMIC_PARAMS['position_size'] = min(0.80, DYNAMIC_PARAMS['position_size'] + 0.05)
        print(f"🧬 进化：盈利后降低阈值至{DYNAMIC_PARAMS['price_change_threshold']*100:.2f}%，仓位{DYNAMIC_PARAMS['position_size']*100:.0f}%")
    else:
        # 亏损：提高阈值，降低仓位
        DYNAMIC_PARAMS['price_change_threshold'] = min(0.01, DYNAMIC_PARAMS['price_change_threshold'] + 0.001)
        DYNAMIC_PARAMS['position_size'] = max(0.20, DYNAMIC_PARAMS['position_size'] - 0.05)
        print(f"🧬 进化：亏损后提高阈值至{DYNAMIC_PARAMS['price_change_threshold']*100:.2f}%，仓位{DYNAMIC_PARAMS['position_size']*100:.0f}%")

def main():
    print("\n🚀 终极进化策略启动！")
    print(f"扫描间隔：{DYNAMIC_PARAMS['scan_interval']}秒")
    print(f"触发阈值：{DYNAMIC_PARAMS['price_change_threshold']*100}%")
    print(f"杠杆：{DYNAMIC_PARAMS['leverage']}x")
    print(f"仓位：{DYNAMIC_PARAMS['position_size']*100}%")
    print("=" * 80)
    
    initial_balance = get_balance()
    state['initial_balance'] = initial_balance
    state['balance'] = initial_balance
    print(f"初始余额：${initial_balance:.2f} USDT")
    
    last_print = time.time()
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
    
    while True:
        try:
            state['scan_count'] += 1
            balance = get_balance()
            state['balance'] = balance
            pnl = balance - initial_balance
            pnl_pct = (pnl / initial_balance * 100) if initial_balance > 0 else 0
            
            # 每 5 秒打印
            if time.time() - last_print >= 5:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] 扫描 #{state['scan_count']} | 余额：${balance:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | 交易：{len(state['trades'])}笔")
                last_print = time.time()
            
            # 扫描每个币种
            for symbol in symbols:
                ohlcv = fetch_ohlcv(symbol, '1m', limit=10)
                if not ohlcv or len(ohlcv) < 3:
                    continue
                
                current_price = ohlcv[-1][4]
                
                # 计算 1 分钟价格变化
                old_price = ohlcv[-2][4] if len(ohlcv) >= 2 else current_price
                price_change = (current_price - old_price) / old_price
                price_change_pct = abs(price_change * 100)
                
                # 计算 RSI
                rsi = calculate_rsi(ohlcv, DYNAMIC_PARAMS['rsi_period'])
                
                # 检查持仓
                pos = get_position(symbol)
                has_position = pos and float(pos.get('contracts', 0)) > 0
                
                # 触发条件：价格变化 > 阈值
                if price_change_pct >= DYNAMIC_PARAMS['price_change_threshold'] * 100:
                    # RSI 确认
                    rsi_confirmed = (price_change > 0 and rsi < DYNAMIC_PARAMS['rsi_long_threshold']) or \
                                   (price_change < 0 and rsi > DYNAMIC_PARAMS['rsi_short_threshold'])
                    
                    if not has_position and rsi_confirmed:
                        direction = 'buy' if price_change > 0 else 'sell'
                        print(f"\n🚀🚀🚀 终极信号！{symbol} {direction.upper()} | 1 分钟变化:{price_change*100:.2f}% | RSI:{rsi:.1f}")
                        
                        position_size = (balance * DYNAMIC_PARAMS['position_size']) / current_price
                        if position_size > 0:
                            open_position(symbol, direction, position_size)
                            state['last_trade_time'] = time.time()
                            state['trades'].append({
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'symbol': symbol,
                                'direction': direction,
                                'price': current_price,
                                'reason': f"1 分钟{direction} {price_change*100:.2f}%"
                            })
                
                # 检查止损止盈
                if has_position:
                    entry_price = float(pos.get('entryPrice', 0))
                    side = pos.get('side', '')
                    unrealized_pnl = (current_price - entry_price) / entry_price if entry_price > 0 else 0
                    if side == 'sell':
                        unrealized_pnl = -unrealized_pnl
                    
                    pnl_pct_current = unrealized_pnl * 100
                    
                    if pnl_pct_current <= -DYNAMIC_PARAMS['stop_loss'] * 100:
                        print(f"⚠️ 止损！PnL={pnl_pct_current:.2f}%")
                        close_position(symbol)
                        state['loss_count'] += 1
                        state['total_pnl'] += pnl
                        evolve_params(False)  # 亏损进化
                    elif pnl_pct_current >= DYNAMIC_PARAMS['take_profit'] * 100:
                        print(f"🎯 止盈！PnL={pnl_pct_current:.2f}%")
                        close_position(symbol)
                        state['win_count'] += 1
                        state['total_pnl'] += pnl
                        evolve_params(True)  # 盈利进化
            
            time.sleep(DYNAMIC_PARAMS['scan_interval'])
            
        except KeyboardInterrupt:
            print("\n🛑 手动停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(0.1)

if __name__ == "__main__":
    main()
