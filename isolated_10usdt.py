#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Isolated 10USDT - 逐仓以小博大策略
每笔仅用 10USDT 保证金，50x 杠杆，风险锁定
"""
import json, time, sys, io
from datetime import datetime
import ccxt

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("💎 Web3Million ISOLATED 10USDT - 逐仓以小博大 💎")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("特点：逐仓模式 + 10USDT/笔 + 50x 杠杆 + 风险锁定")
print("=" * 80)

with open('okx_config.json') as f:
    config = json.load(f)

okx = ccxt.okx({
    'apiKey': config['api_key'],
    'secret': config['secret_key'],
    'password': config['passphrase'],
    'enableRateLimit': False,
    'options': {
        'defaultType': 'swap',
        'marginMode': 'isolated',  # 逐仓模式
    }
})
okx.set_sandbox_mode(True)
okx.session.trust_env = False
okx.session.proxies = {}

print("✅ OKX 测试网连接成功")
print("✅ 逐仓模式已启用")

# 策略参数
MARGIN_PER_TRADE = 10  # 每笔 10USDT 保证金
LEVERAGE = 50  # 50x 杠杆
POSITION_SIZE = MARGIN_PER_TRADE * LEVERAGE  # 名义本金 $500
PRICE_CHANGE_THRESHOLD = 0.001  # 0.1% 触发
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
STOP_LOSS = 1.0  # 逐仓止损：100% 保证金 (最坏情况亏光 10U)
TAKE_PROFIT = 0.5  # 止盈：50% 收益率 ($5 利润)

state = {
    'trades': [],
    'scan_count': 0,
    'total_profit': 0,
    'total_loss': 0,
    'win_count': 0,
    'loss_count': 0,
}

def get_balance():
    try:
        b = okx.fetch_balance()
        return float(b['total'].get('USDT', 0))
    except:
        return 0.0

def set_isolated(symbol, margin):
    """设置逐仓保证金"""
    try:
        okx.set_margin_mode('isolated')
        okx.set_leverage(LEVERAGE, symbol, {'marginMode': 'isolated'})
        print(f"✅ {symbol} 逐仓设置：{LEVERAGE}x, 保证金${margin}")
        return True
    except Exception as e:
        print(f"❌ 设置失败：{e}")
        return False

def open_isolated_position(symbol, side, margin_usdt=10):
    """开逐仓仓位"""
    try:
        # 设置逐仓
        set_isolated(symbol, margin_usdt)
        
        # 获取价格
        ticker = okx.fetch_ticker(symbol)
        price = ticker['last']
        
        # 计算数量 (保证金 * 杠杆 / 价格)
        amount = (margin_usdt * LEVERAGE) / price
        
        # 开仓
        order = okx.create_order(symbol, 'market', side, amount)
        
        print(f"💎 开仓 {side} {symbol} | 保证金：${margin_usdt} | 杠杆：{LEVERAGE}x | 数量：{amount:.6f} @ ${price}")
        
        state['trades'].append({
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'side': side,
            'margin': margin_usdt,
            'leverage': LEVERAGE,
            'amount': amount,
            'price': price,
            'type': 'isolated'
        })
        
        return order
    except Exception as e:
        print(f"❌ 开仓失败：{e}")
        return None

def check_isolated_positions():
    """检查逐仓持仓"""
    try:
        positions = okx.fetch_positions()
        for pos in positions:
            if float(pos.get('contracts', 0)) > 0:
                symbol = pos['symbol']
                side = pos.get('side', '')
                entry_price = float(pos.get('entryPrice', 0))
                current_price = float(pos.get('markPrice', 0))
                unrealized_pnl = float(pos.get('unrealizedPnl', 0))
                pnl_pct = float(pos.get('percentage', 0)) * 100
                
                # 逐仓止盈止损
                if pnl_pct >= TAKE_PROFIT * 100:
                    print(f"🎯 止盈 {symbol} | 收益率：{pnl_pct:.2f}%")
                    close_side = 'sell' if side == 'buy' else 'buy'
                    okx.create_order(symbol, 'market', close_side, float(pos['contracts']))
                    state['win_count'] += 1
                    state['total_profit'] += abs(unrealized_pnl)
                elif pnl_pct <= -STOP_LOSS * 100:
                    print(f"⚠️ 止损 {symbol} | 亏损：{pnl_pct:.2f}%")
                    close_side = 'sell' if side == 'buy' else 'buy'
                    okx.create_order(symbol, 'market', close_side, float(pos['contracts']))
                    state['loss_count'] += 1
                    state['total_loss'] += abs(unrealized_pnl)
    except Exception as e:
        pass

def main():
    print("\n🚀 逐仓 10USDT 策略启动！")
    print(f"每笔保证金：${MARGIN_PER_TRADE}")
    print(f"杠杆：{LEVERAGE}x")
    print(f"名义本金：${POSITION_SIZE}")
    print(f"触发阈值：{PRICE_CHANGE_THRESHOLD*100}%")
    print(f"止盈：{TAKE_PROFIT*100}% (盈利${TAKE_PROFIT*MARGIN_PER_TRADE})")
    print(f"止损：{STOP_LOSS*100}% (亏损${STOP_LOSS*MARGIN_PER_TRADE})")
    print("=" * 80)
    
    balance = get_balance()
    print(f"当前余额：${balance:.2f} USDT")
    print(f"可用交易次数：{int(balance / MARGIN_PER_TRADE)} 次")
    
    last_print = time.time()
    
    while True:
        try:
            state['scan_count'] += 1
            balance = get_balance()
            total_pnl = state['total_profit'] - state['total_loss']
            
            if time.time() - last_print >= 5:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"\n[{current_time}] 扫描 #{state['scan_count']}")
                print(f"余额：${balance:.2f} | 总盈亏：${total_pnl:.2f}")
                print(f"交易：{len(state['trades'])}笔 | 盈利：{state['win_count']} | 亏损：{state['loss_count']}")
                last_print = time.time()
            
            # 检查现有持仓
            check_isolated_positions()
            
            # 扫描开仓机会
            for symbol in SYMBOLS:
                try:
                    ohlcv = okx.fetch_ohlcv(symbol, '1m', limit=3)
                    if len(ohlcv) < 2:
                        continue
                    
                    current_price = ohlcv[-1][4]
                    old_price = ohlcv[-2][4]
                    price_change = (current_price - old_price) / old_price
                    
                    # 检查是否有持仓
                    positions = okx.fetch_positions()
                    has_position = any(p['symbol'] == symbol and float(p.get('contracts', 0)) > 0 for p in positions)
                    
                    if abs(price_change) >= PRICE_CHANGE_THRESHOLD and not has_position:
                        direction = 'buy' if price_change > 0 else 'sell'
                        print(f"\n💎 逐仓信号！{symbol} {direction.upper()} | 1 分钟变化:{price_change*100:.2f}%")
                        open_isolated_position(symbol, direction, MARGIN_PER_TRADE)
                
                except Exception as e:
                    continue
            
            time.sleep(0.5)  # 0.5 秒扫描一次
        
        except KeyboardInterrupt:
            print("\n🛑 手动停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
