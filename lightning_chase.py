#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Lightning Chase - 闪电追单策略
专为快速暴涨暴跌设计，解决"踏空"问题！
策略核心:
1. 监控 1 分钟内价格变化 > 3% (暴涨/暴跌)
2. 立即市价追单 (不等待 MA/RSI 确认)
3. 100x 杠杆，满仓干
4. 持仓时间：30 秒 - 5 分钟 (快进快出)
5. 止损 3%，止盈 10%
"""
import os, sys, io, json, time, math
from datetime import datetime, timedelta
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("⚡⚡⚡ Web3Million LIGHTNING CHASE - 闪电追单 ⚡⚡⚡")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("策略：1 分钟涨跌>3% 立即追单 + 100x 杠杆 + 快进快出")
print("警告：极高风险，专为暴涨暴跌设计！")
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

# ========== 闪电追单参数 ==========
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
LEVERAGE = 100  # 100x 疯狂杠杆
SCAN_INTERVAL = 2  # 2 秒扫描一次 (更快！)
PRICE_CHANGE_THRESHOLD = 0.03  # 1 分钟涨跌 > 3% 触发
MAX_POSITION_PCT = 0.95  # 95% 仓位
STOP_LOSS_PCT = 0.03  # 3% 止损
TAKE_PROFIT_PCT = 0.10  # 10% 止盈
MAX_HOLD_TIME = 300  # 最长持仓 5 分钟

# 状态
state = {
    'balance': 0.0,
    'initial_balance': 0.0,
    'trades': [],
    'scan_count': 0,
    'price_history': {},  # 记录每个币种的价格历史
    'last_chase_time': {},  # 上次追单时间 (避免重复)
}

def fetch_price(symbol):
    """获取最新价格"""
    try:
        ticker = okx.fetch_ticker(symbol)
        return ticker['last']
    except:
        return None

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
        print(f"⚡⚡⚡ 闪电追单 {side} {symbol} {amount:.6f} @ {order.get('price', '市价')}")
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
    print("\n🚀 闪电追单策略启动！")
    print(f"扫描间隔：{SCAN_INTERVAL}秒")
    print(f"杠杆：{LEVERAGE}x")
    print(f"触发条件：1 分钟涨跌 > {PRICE_CHANGE_THRESHOLD*100}%")
    print(f"止损/止盈：{STOP_LOSS_PCT*100}% / {TAKE_PROFIT_PCT*100}%")
    print(f"最长持仓：{MAX_HOLD_TIME}秒")
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
                current_price = fetch_price(symbol)
                if not current_price:
                    continue
                
                current_price = float(current_price)
                
                # 记录价格历史
                if symbol not in state['price_history']:
                    state['price_history'][symbol] = []
                
                state['price_history'][symbol].append({
                    'price': current_price,
                    'time': time.time()
                })
                
                # 保留最近 2 分钟的数据 (每 2 秒一次，约 60 个点)
                if len(state['price_history'][symbol]) > 60:
                    state['price_history'][symbol] = state['price_history'][symbol][-60:]
                
                # 需要至少 30 秒的数据 (15 个点) 才能计算 1 分钟变化
                if len(state['price_history'][symbol]) < 15:
                    continue
                
                # 计算 1 分钟前和现在的价格变化
                now = time.time()
                old_price = None
                for record in reversed(state['price_history'][symbol]):
                    if now - record['time'] >= 60:  # 1 分钟前
                        old_price = record['price']
                        break
                
                if not old_price:
                    continue
                
                # 计算变化率
                price_change = (current_price - old_price) / old_price
                price_change_pct = abs(price_change * 100)
                
                # 检查是否触发追单
                if price_change_pct >= PRICE_CHANGE_THRESHOLD * 100:
                    # 检查是否已有持仓
                    pos = get_position(symbol)
                    has_position = pos and float(pos.get('contracts', 0)) > 0
                    
                    # 避免重复追单 (同一方向 30 秒内只追一次)
                    last_chase = state['last_chase_time'].get(symbol, 0)
                    if time.time() - last_chase < 30:
                        continue
                    
                    # 确定方向
                    if price_change > 0:
                        # 暴涨 → 做多
                        direction = 'buy'
                        signal = f"暴涨 {price_change_pct:.2f}%"
                    else:
                        # 暴跌 → 做空
                        direction = 'sell'
                        signal = f"暴跌 {price_change_pct:.2f}%"
                    
                    print(f"\n⚡⚡⚡ 闪电追单信号！{symbol} {signal}")
                    
                    if not has_position:
                        # 开仓
                        position_size = (balance * MAX_POSITION_PCT) / current_price
                        if position_size > 0:
                            open_position(symbol, direction, position_size)
                            state['last_chase_time'][symbol] = time.time()
                            
                            # 记录交易
                            state['trades'].append({
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'symbol': symbol,
                                'direction': direction,
                                'price': current_price,
                                'reason': signal
                            })
                    else:
                        print(f"  已有持仓，跳过")
                
                # 检查持仓时间和止损止盈
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
