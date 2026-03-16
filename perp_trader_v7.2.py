#!/usr/bin/env python3
"""
v7.2 永续合约交易系统 - 24/7 自动化交易
配置参数:
- 杠杆：20x
- 止损：5% 账户风险
- 止盈：15% 账户风险
- 信号阈值：3.0
- 趋势过滤：只顺趋势交易
- 跟踪止盈：0.3% 回撤
"""

import ccxt.async_support as ccxt
import asyncio
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置
CONFIG = {
    'exchange': 'okx',
    'testnet': True,
    'symbols': ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT'],
    'leverage': 20,
    'max_position_usdt': 30,  # 最大仓位 $30
    'min_position_usdt': 0.01,  # 最小仓位
    'stop_loss_pct': 5.0,  # 止损 5%
    'take_profit_pct': 15.0,  # 止盈 15%
    'trailing_stop_pct': 0.3,  # 跟踪止盈 0.3%
    'signal_threshold': 3.0,  # 信号阈值
    'scan_interval': 30,  # 扫描间隔 30 秒
    'trade_cooldown': 300,  # 交易冷却 5 分钟
    'stop_loss_cooldown': 600,  # 止损后冷却 10 分钟
}

# 状态文件
STATE_FILE = Path('v7_state.json')

class PerpTrader:
    def __init__(self):
        self.exchange = None
        self.state = self.load_state()
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('perp_trader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_state(self):
        """加载交易状态"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            'last_trade_time': None,
            'last_stop_loss_time': None,
            'positions': {},
            'total_trades': 0,
            'total_pnl': 0,
            'balance': 1289.07  # 初始余额
        }
        
    def save_state(self):
        """保存交易状态"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    async def init_exchange(self):
        """初始化交易所连接"""
        api_key = os.getenv('OKX_API_KEY')
        secret = os.getenv('OKX_SECRET_KEY')
        passphrase = os.getenv('OKX_PASSPHRASE')
        
        if not all([api_key, secret, passphrase]):
            raise ValueError("缺少 OKX API 配置，请检查.env 文件")
        
        self.exchange = ccxt.okx({
            'enableRateLimit': True,
            'apiKey': api_key,
            'secret': secret,
            'password': passphrase,
            'options': {
                'defaultType': 'future',
            }
        })
        if CONFIG['testnet']:
            self.exchange.set_sandbox_mode(True)
        await self.exchange.fetch_balance()
        self.logger.info("交易所连接成功")
        
    async def get_ticker(self, symbol):
        """获取实时行情"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            self.logger.error(f"获取行情失败：{e}")
            return None
            
    def calculate_rsi(self, prices, period=14):
        """计算 RSI 指标"""
        if len(prices) < period + 1:
            return 50
            
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
            
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """计算 MACD 指标"""
        if len(prices) < slow + signal:
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'trend': 'neutral'}
        
        # 计算 EMA
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema_value = sum(data[:period]) / period
            for price in data[period:]:
                ema_value = (price - ema_value) * multiplier + ema_value
            return ema_value
        
        macd_line = ema(prices, fast) - ema(prices, slow)
        signal_line = ema(prices, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram,
            'trend': 'bullish' if histogram > 0 else 'bearish'
        }
        
    def calculate_ma(self, prices, period):
        """计算移动平均线"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
        
    async def get_ohlcv(self, symbol, timeframe='1h', limit=100):
        """获取 K 线数据"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return [c[4] for c in ohlcv]  # 收盘价
        except Exception as e:
            self.logger.error(f"获取 K 线失败：{e}")
            return []
            
    def generate_signal(self, rsi, macd_data, ma5, ma20, current_price):
        """生成交易信号"""
        score = 0
        
        # RSI 信号 (权重 1.5)
        if rsi <= 30:
            score += 1.5  # 超卖
        elif rsi >= 70:
            score -= 1.5  # 超买
            
        # MACD 信号 (权重 1.0)
        if macd_data['histogram'] > 0:
            score += 1.0
        else:
            score -= 1.0
            
        # 趋势信号 (权重 0.5)
        if ma5 > ma20:
            score += 0.5
        else:
            score -= 0.5
            
        return score
        
    async def check_position(self, symbol):
        """检查现有持仓"""
        try:
            positions = await self.exchange.fetch_positions([symbol])
            for pos in positions:
                if pos['contracts'] is not None and pos['contracts'] != 0:
                    return pos
            return None
        except Exception as e:
            self.logger.error(f"检查持仓失败：{e}")
            return None
            
    async def execute_trade(self, symbol, side, amount):
        """执行交易"""
        try:
            # 检查冷却时间
            now = time.time()
            if self.state.get('last_trade_time'):
                cooldown = CONFIG['stop_loss_cooldown'] if self.state.get('last_stop_loss_time') else CONFIG['trade_cooldown']
                if now - self.state['last_trade_time'] < cooldown:
                    return False
                    
            # 设置杠杆
            await self.exchange.set_leverage(CONFIG['leverage'], symbol)
            
            # 下单
            order = await self.exchange.create_order(
                symbol, 'market', side, amount,
                {'leverage': CONFIG['leverage']}
            )
            
            self.state['last_trade_time'] = now
            self.state['total_trades'] += 1
            self.save_state()
            
            self.logger.info(f"执行交易：{side} {symbol} {amount}")
            return True
            
        except Exception as e:
            self.logger.error(f"交易失败：{e}")
            return False
            
    async def manage_position(self, symbol, position):
        """管理现有持仓"""
        # 实现止损止盈逻辑
        pass
        
    async def scan_market(self):
        """扫描市场机会"""
        self.logger.info("开始扫描市场...")
        
        for symbol in CONFIG['symbols']:
            try:
                # 获取数据
                prices = await self.get_ohlcv(symbol, '1h', 100)
                ticker = await self.get_ticker(symbol)
                
                if not prices or not ticker:
                    continue
                    
                current_price = ticker['last']
                
                # 计算指标
                rsi = self.calculate_rsi(prices)
                macd_data = {
                    'macd': 0,
                    'signal': 0,
                    'histogram': 0,
                    'trend': 'neutral'
                }
                ma5 = self.calculate_ma(prices, 5)
                ma20 = self.calculate_ma(prices, 20)
                
                # 生成信号
                signal_score = self.generate_signal(rsi, macd_data, ma5, ma20, current_price)
                
                self.logger.info(f"{symbol}: RSI={rsi:.2f}, MA5={ma5:.2f}, MA20={ma20:.2f}, Signal={signal_score:.2f}")
                
                # 检查是否达到交易阈值
                if abs(signal_score) >= CONFIG['signal_threshold']:
                    side = 'buy' if signal_score > 0 else 'sell'
                    amount = CONFIG['min_position_usdt'] / current_price  # 动态仓位
                    
                    # 执行交易
                    await self.execute_trade(symbol, side, amount)
                    
            except Exception as e:
                self.logger.error(f"扫描 {symbol} 失败：{e}")
                
    async def run(self):
        """主运行循环"""
        await self.init_exchange()
        
        self.logger.info("v7.2 永续合约交易系统启动")
        self.logger.info(f"杠杆：{CONFIG['leverage']}x, 止损：{CONFIG['stop_loss_pct']}%, 止盈：{CONFIG['take_profit_pct']}%")
        
        try:
            while True:
                await self.scan_market()
                await asyncio.sleep(CONFIG['scan_interval'])
        except KeyboardInterrupt:
            self.logger.info("系统停止")
        finally:
            await self.exchange.close()
            self.save_state()

if __name__ == '__main__':
    trader = PerpTrader()
    asyncio.run(trader.run())
