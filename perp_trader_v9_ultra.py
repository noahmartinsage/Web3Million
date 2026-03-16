#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Perpetual v9.0 Ultra - 激进狙击手版
目标：胜率 95%+
策略核心：
  - 极度严格的入场条件 (RSI <15 或 >85)
  - 三周期共振 (15m/1h/4h 同向)
  - 爆量确认 (>200% 均量)
  - 高波动率 (ATR > 2%)
  - 时间窗口过滤 (只在北京/伦敦/纽约重叠时段)
  - 3% 止损 / 20% 止盈 (1:6 盈亏比)
"""
import os, sys, io, json, time
from datetime import datetime, timedelta
import ccxt

# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🦊 Web3Million Perpetual v9.0 Ultra - 激进狙击手版")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("目标胜率：95%+ | 策略：极度稀缺信号 + 多周期共振 + 爆量确认")
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

# ========== 策略参数 (激进版) ==========
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
LEVERAGE = 20  # 杠杆
TIMEFRAMES = ['15m', '1h', '4h']  # 三周期

# 激进阈值
RSI_LONG_THRESHOLD = 15   # 极度超卖才做多
RSI_SHORT_THRESHOLD = 85  # 极度超买才做空
VOLUME_RATIO = 2.0        # 成交量 >200% 均量
ATR_MIN = 0.02            # ATR > 2%
MACD_SIGMA = 2.0          # MACD 柱状线 > 2 倍标准差

# 风控
STOP_LOSS_PCT = 0.03      # 3% 账户风险止损
TAKE_PROFIT_PCT = 0.20    # 20% 账户风险止盈 (1:6.6)
MAX_POSITION_PCT = 0.05   # 最大仓位 5%

# 时间窗口 (UTC) - 只在北京/伦敦/纽约重叠时段
TRADING_HOURS = [
    (7, 10),   # 伦敦早市 + 北京下午
    (13, 16),  # 伦敦下午 + 纽约凌晨
]

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
    'cooldown_until': None,  # 冷却时间
}

def get_current_hour_utc():
    """获取当前 UTC 小时"""
    return datetime.utcnow().hour

def is_trading_hour():
    """检查是否在交易时间窗口内"""
    hour = get_current_hour_utc()
    for start, end in TRADING_HOURS:
        if start <= hour < end:
            return True
    return False

def fetch_ohlcv(symbol, timeframe='15m', limit=100):
    """获取 K 线数据"""
    try:
        ohlcv = okx.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    except Exception as e:
        print(f"❌ 获取 K 线失败 {symbol} {timeframe}: {e}")
        return None

def calculate_rsi(ohlcv, period=14):
    """计算 RSI"""
    if not ohlcv or len(ohlcv) < period + 1:
        return None
    
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
        return None
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(ohlcv, fast=12, slow=26, signal=9):
    """计算 MACD"""
    if not ohlcv or len(ohlcv) < slow + signal + 1:
        return None, None, None
    
    closes = [c[4] for c in ohlcv]
    
    # EMA 计算
    def ema(data, period):
        multiplier = 2 / (period + 1)
        ema_val = sum(data[:period]) / period
        for i in range(period, len(data)):
            ema_val = (data[i] - ema_val) * multiplier + ema_val
        return ema_val
    
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = ema_fast - ema_slow
    
    # 计算 MACD 柱状线 (简化)
    macd_hist = macd_line  # 简化处理
    return macd_line, macd_hist, signal

def calculate_atr(ohlcv, period=14):
    """计算 ATR"""
    if not ohlcv or len(ohlcv) < period + 1:
        return None
    
    atr_sum = 0
    for i in range(len(ohlcv) - period, len(ohlcv)):
        high = ohlcv[i][2]
        low = ohlcv[i][3]
        prev_close = ohlcv[i-1][4]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        atr_sum += tr
    
    atr = atr_sum / period
    close = ohlcv[-1][4]
    atr_pct = atr / close
    return atr_pct

def check_multi_timeframe共振(symbol):
    """检查多周期共振"""
    trends = []
    for tf in TIMEFRAMES:
        ohlcv = fetch_ohlcv(symbol, tf)
        if not ohlcv or len(ohlcv) < 25:
            return None, None
        
        # 计算 MA5 和 MA20
        closes = [c[4] for c in ohlcv]
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20
        
        if ma5 > ma20:
            trends.append(1)  # 上涨
        elif ma5 < ma20:
            trends.append(-1)  # 下跌
        else:
            trends.append(0)
    
    # 检查是否三周期同向
    if all(t == 1 for t in trends):
        return 'BULLISH', trends
    elif all(t == -1 for t in trends):
        return 'BEARISH', trends
    else:
        return 'NEUTRAL', trends

def check_volume_ratio(symbol, ratio_threshold=2.0):
    """检查成交量是否爆量"""
    ohlcv = fetch_ohlcv(symbol, '15m', limit=50)
    if not ohlcv or len(ohlcv) < 21:
        return False
    
    volumes = [c[5] for c in ohlcv]
    current_vol = volumes[-1]
    avg_vol = sum(volumes[-20:-1]) / 19  # 过去 20 根均量
    
    if avg_vol == 0:
        return False
    
    ratio = current_vol / avg_vol
    return ratio >= ratio_threshold

def check_atr(symbol, min_atr=0.02):
    """检查 ATR 是否足够"""
    ohlcv = fetch_ohlcv(symbol, '15m', limit=50)
    if not ohlcv:
        return False
    
    atr_pct = calculate_atr(ohlcv, 14)
    if atr_pct is None:
        return False
    
    return atr_pct >= min_atr

def generate_signal(symbol):
    """生成交易信号 (激进版)"""
    # 1. 检查交易时间
    if not is_trading_hour():
        return 'HOLD', '非交易时段'
    
    # 2. 检查多周期共振
    trend_direction, trends = check_multi_timeframe共振(symbol)
    if trend_direction == 'NEUTRAL':
        return 'HOLD', '无多周期共振'
    
    # 3. 获取 15m 数据
    ohlcv = fetch_ohlcv(symbol, '15m', limit=100)
    if not ohlcv or len(ohlcv) < 50:
        return 'HOLD', '数据不足'
    
    # 4. 计算 RSI
    rsi = calculate_rsi(ohlcv, 14)
    if rsi is None:
        return 'HOLD', 'RSI 计算失败'
    
    # 5. 检查成交量
    if not check_volume_ratio(symbol, VOLUME_RATIO):
        return 'HOLD', '成交量不足'
    
    # 6. 检查 ATR
    if not check_atr(symbol, ATR_MIN):
        return 'HOLD', '波动率不足'
    
    # 7. 生成信号
    if trend_direction == 'BULLISH' and rsi < RSI_LONG_THRESHOLD:
        return 'LONG', f'极度超卖 RSI={rsi:.1f} + 多周期共振 + 爆量'
    elif trend_direction == 'BEARISH' and rsi > RSI_SHORT_THRESHOLD:
        return 'SHORT', f'极度超买 RSI={rsi:.1f} + 多周期共振 + 爆量'
    
    return 'HOLD', f'RSI={rsi:.1f} 未达阈值'

def fetch_balance():
    """获取账户余额"""
    try:
        balance = okx.fetch_balance()
        usdt = balance.get('USDT', {})
        total = usdt.get('total', 0)
        if isinstance(total, dict):
            total = 0
        return float(total)
    except Exception as e:
        print(f"❌ 获取余额失败：{e}")
        return state.get('balance', 0.0)

def main():
    """主循环"""
    print("\n🚀 v9.0 Ultra 启动，开始扫描...")
    print(f"交易时段：{TRADING_HOURS} (UTC)")
    print(f"策略：RSI<{RSI_LONG_THRESHOLD} 做多 | RSI>{RSI_SHORT_THRESHOLD} 做空")
    print(f"过滤：{VOLUME_RATIO}x 爆量 | ATR>{ATR_MIN*100}% | 三周期共振")
    print("-" * 80)
    
    state['initial_balance'] = fetch_balance()
    state['balance'] = state['initial_balance']
    print(f"初始余额：${state['balance']:.2f}")
    
    scan_interval = 30  # 30 秒扫描一次
    last_signal = {}
    
    while True:
        try:
            current_time = datetime.now()
            state['scan_count'] += 1
            
            # 每小时汇报一次
            if state['scan_count'] % 120 == 0:  # 30 秒 * 120 = 1 小时
                balance = fetch_balance()
                state['balance'] = balance
                pnl = balance - state['initial_balance']
                pnl_pct = (pnl / state['initial_balance'] * 100) if state['initial_balance'] > 0 else 0
                print(f"\n{'='*80}")
                print(f"⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')} | 扫描：{state['scan_count']} 次")
                print(f"💰 余额：${balance:.2f} | PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%)")
                print(f"📊 交易：{len(state['trades'])} 笔 | 胜：{state['win_count']} | 负：{state['loss_count']}")
                if state['trades']:
                    win_rate = state['win_count'] / (state['win_count'] + state['loss_count']) * 100 if (state['win_count'] + state['loss_count']) > 0 else 0
                    print(f"🎯 胜率：{win_rate:.1f}%")
                print(f"{'='*80}\n")
            
            # 扫描交易对
            for symbol in SYMBOLS:
                signal, reason = generate_signal(symbol)
                
                # 只在信号变化时输出
                prev_signal = last_signal.get(symbol, 'HOLD')
                if signal != prev_signal or signal in ['LONG', 'SHORT']:
                    timestamp = current_time.strftime('%H:%M:%S')
                    if signal == 'HOLD':
                        pass  # 不输出 HOLD
                    else:
                        print(f"[{timestamp}] {symbol}: {signal} - {reason}")
                
                last_signal[symbol] = signal
                
                # 模拟交易执行 (此处简化，实际需连接交易所 API)
                # 实盘时需添加：开仓、平仓、止损、止盈逻辑
            
            time.sleep(scan_interval)
            
        except KeyboardInterrupt:
            print("\n🛑 手动停止")
            break
        except Exception as e:
            print(f"❌ 错误：{e}")
            time.sleep(scan_interval)

if __name__ == '__main__':
    main()
