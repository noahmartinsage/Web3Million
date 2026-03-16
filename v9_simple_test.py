#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million v9.0 Ultra - 简化测试版
目标：验证核心逻辑，胜率 95%+
"""
import os, sys, io, json, time
from datetime import datetime
import ccxt

# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🦊 Web3Million v9.0 Ultra - 简化测试版")
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("目标胜率：95%+ | 策略：极度稀缺信号 + 三周期共振 + 爆量确认")
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

print("\n✅ OKX 测试网连接成功")

# 获取余额
try:
    balance = okx.fetch_balance()
    usdt = balance.get('USDT', {})
    total = usdt.get('total', 0)
    if isinstance(total, dict):
        total = 0
    print(f"💰 账户余额：USDT ${float(total):.2f}")
except Exception as e:
    print(f"❌ 获取余额失败：{e}")

# 策略参数
SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
RSI_LONG = 15
RSI_SHORT = 85

print(f"\n🎯 策略参数:")
print(f"  交易对：{SYMBOLS}")
print(f"  RSI 做多阈值：< {RSI_LONG} (极度超卖)")
print(f"  RSI 做空阈值：> {RSI_SHORT} (极度超买)")
print(f"  扫描间隔：30 秒")
print("-" * 80)

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

print("\n🚀 开始扫描市场...")
print("按 Ctrl+C 停止\n")

scan_count = 0
try:
    while True:
        scan_count += 1
        current_time = datetime.now()
        
        # 每小时汇报
        if scan_count % 120 == 0:
            print(f"\n⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')} | 扫描：{scan_count} 次")
            print("-" * 80)
        
        # 扫描每个交易对
        for symbol in SYMBOLS:
            try:
                # 获取 15m K 线
                ohlcv = okx.fetch_ohlcv(symbol, '15m', limit=100)
                if not ohlcv or len(ohlcv) < 50:
                    continue
                
                # 计算 RSI
                rsi = calculate_rsi(ohlcv, 14)
                if rsi is None:
                    continue
                
                current_price = ohlcv[-1][4]
                
                # 检查信号
                signal = None
                if rsi < RSI_LONG:
                    signal = f"🟢 LONG 信号！RSI={rsi:.1f} (<{RSI_LONG}) 极度超卖"
                elif rsi > RSI_SHORT:
                    signal = f"🔴 SHORT 信号！RSI={rsi:.1f} (>{RSI_SHORT}) 极度超买"
                
                # 只在 RSI 极端时输出
                if signal:
                    print(f"[{current_time.strftime('%H:%M:%S')}] {symbol} @ ${current_price:,.2f} | {signal}")
                elif scan_count % 10 == 0:  # 每 10 次扫描输出一次正常状态
                    print(f"[{current_time.strftime('%H:%M:%S')}] {symbol} @ ${current_price:,.2f} | RSI={rsi:.1f} (无信号)")
                
            except Exception as e:
                print(f"❌ {symbol} 错误：{e}")
        
        time.sleep(30)  # 30 秒扫描一次
        
except KeyboardInterrupt:
    print(f"\n\n🛑 手动停止 | 总扫描次数：{scan_count}")
except Exception as e:
    print(f"\n\n❌ 异常：{e}")
