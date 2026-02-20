#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 完整交易策略
实现盈利的交易循环
"""
import ccxt
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class TradingStrategy:
    def __init__(self):
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        self.initial_balance = 0
        self.trades = []
        
    def get_balance(self):
        bal = self.exchange.fetch_balance()
        return {
            'USDT': bal['free'].get('USDT', 0),
            'BTC': bal['free'].get('BTC', 0),
            'ETH': bal['free'].get('ETH', 0),
            'total_usd': bal['free'].get('USDT', 0) + bal['free'].get('BTC', 0) * self.get_price('BTC/USDT')['last']
        }
    
    def get_price(self, symbol):
        ticker = self.exchange.fetch_ticker(symbol)
        return {'last': ticker['last'], 'bid': ticker['bid'], 'ask': ticker['ask']}
    
    def get_order_book(self, symbol, limit=10):
        return self.exchange.fetch_order_book(symbol, limit)
    
    def scan_arbitrage(self):
        """扫描套利机会"""
        opportunities = []
        
        # 检查多个DEX/交易对价差
        pairs = [
            ('BTC/USDT', 'ETH/USDT', 'BTC/ETH'),
            ('ETH/USDT', 'BTC/USDT', None),
            ('SOL/USDT', 'BTC/USDT', None),
        ]
        
        # 获取主要交易对价格
        prices = {}
        for pair in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
            try:
                prices[pair] = self.get_price(pair)
            except:
                pass
        
        if 'BTC/USDT' in prices and 'ETH/USDT' in prices:
            # 计算BTC/ETH汇率
            btc_eth_rate = prices['BTC/USDT']['last'] / prices['ETH/USDT']['last']
            
            # 获取BTC/ETH直接价格
            try:
                direct = self.get_price('BTC/ETH')
                spread = abs(btc_eth_rate - direct['last']) / direct['last'] * 100
                
                if spread > 0.5:  # 超过0.5%价差
                    opportunities.append({
                        'type': 'triangular',
                        'pairs': ['BTC/USDT', 'ETH/USDT', 'BTC/ETH'],
                        'spread': spread,
                        'rate': btc_eth_rate,
                        'direct': direct['last']
                    })
            except:
                pass
        
        return opportunities
    
    def momentum_strategy(self, symbol='BTC/USDT', threshold=0.3):
        """动量策略 - 追涨杀跌"""
        try:
            # 获取1小时K线数据
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=20)
            
            if len(ohlcv) < 10:
                return None
            
            # 计算移动平均线
            closes = [c[4] for c in ohlcv]
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
            ma20 = sum(closes[-20:]) / 20
            
            current_price = closes[-1]
            
            # 买入信号: MA5 > MA10 > MA20 且价格突破
            if ma5 > ma10 > ma20 and current_price > ma5 * (1 + threshold/100):
                return {'action': 'buy', 'reason': 'bullish_momentum', 'price': current_price}
            
            # 卖出信号: MA5 < MA10
            elif ma5 < ma10:
                return {'action': 'sell', 'reason': 'bearish_momentum', 'price': current_price}
            
            return None
            
        except Exception as e:
            print(f"Error in momentum strategy: {e}")
            return None
    
    def grid_strategy(self, symbol='BTC/USDT', grid_levels=5, range_pct=2):
        """网格策略 - 区间震荡"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            current = ticker['last']
            
            # 计算网格区间
            low = current * (1 - range_pct/100)
            high = current * (1 + range_pct/100)
            grid_size = (high - low) / grid_levels
            
            # 计算当前网格
            grid_index = int((current - low) / grid_size)
            
            return {
                'current': current,
                'low': low,
                'high': high,
                'grid_index': grid_index,
                'grid_size': grid_size
            }
        except:
            return None
    
    def execute_trade(self, action, symbol, amount):
        """执行交易"""
        try:
            if action == 'buy':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_market_sell_order(symbol, amount)
            
            self.trades.append({
                'symbol': symbol,
                'action': action,
                'amount': amount,
                'order_id': order['id'],
                'time': time.time()
            })
            
            return {'success': True, 'order': order}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run(self, cycles=10):
        """运行完整交易循环"""
        print("\n" + "="*60)
        print("Web3Million - Complete Trading Strategy")
        print("="*60)
        
        # 获取初始余额
        initial = self.get_balance()
        self.initial_balance = initial['total_usd']
        print(f"\nInitial Balance: ${initial['total_usd']:.2f}")
        print(f"  USDT: ${initial['USDT']:.2f}")
        print(f"  BTC: {initial['BTC']:.6f}")
        print(f"  ETH: {initial['ETH']:.6f}")
        
        print(f"\nStarting {cycles} trading cycles...\n")
        
        for i in range(cycles):
            print(f"=== Cycle {i+1}/{cycles} ===")
            
            # 1. 获取当前余额
            bal = self.get_balance()
            print(f"Balance: ${bal['total_usd']:.2f} | USDT: ${bal['USDT']:.2f} | BTC: {bal['BTC']:.6f}")
            
            # 2. 获取市场价格
            btc_price = self.get_price('BTC/USDT')
            print(f"BTC: ${btc_price['last']:.2f}")
            
            # 3. 扫描套利机会
            arb_opps = self.scan_arbitrage()
            if arb_opps:
                print(f"Arbitrage opportunities: {len(arb_opps)}")
                for opp in arb_opps:
                    print(f"  Spread: {opp['spread']:.2f}%")
            
            # 4. 动量策略分析
            momentum = self.momentum_strategy('BTC/USDT')
            if momentum:
                print(f"Momentum: {momentum['action']} ({momentum['reason']})")
                
                # 根据动量执行交易
                if momentum['action'] == 'buy' and bal['USDT'] > 50:
                    # 买入信号 - 使用10%仓位
                    amount = (bal['USDT'] * 0.1) / btc_price['last']
                    result = self.execute_trade('buy', 'BTC/USDT', amount)
                    if result['success']:
                        print(f"  -> BUY executed: {amount:.6f} BTC")
                    else:
                        print(f"  -> BUY failed: {result.get('error')}")
                        
                elif momentum['action'] == 'sell' and bal['BTC'] > 0.01:
                    # 卖出信号 - 卖出50%持仓
                    amount = bal['BTC'] * 0.5
                    result = self.execute_trade('sell', 'BTC/USDT', amount)
                    if result['success']:
                        print(f"  -> SELL executed: {amount:.6f} BTC")
                    else:
                        print(f"  -> SELL failed: {result.get('error')}")
            else:
                print("Momentum: Neutral (no clear signal)")
            
            # 5. 网格策略分析
            grid = self.grid_strategy('BTC/USDT')
            if grid:
                print(f"Grid: Level {grid['grid_index']}/{grid_levels} (${grid['low']:.0f}-${grid['high']:.0f})")
            
            print("")
            time.sleep(3)
        
        # 最终余额
        final = self.get_balance()
        profit = final['total_usd'] - self.initial_balance
        profit_pct = (profit / self.initial_balance) * 100
        
        print("="*60)
        print("TRADING SUMMARY")
        print("="*60)
        print(f"Initial: ${self.initial_balance:.2f}")
        print(f"Final:   ${final['total_usd']:.2f}")
        print(f"Profit:  ${profit:.2f} ({profit_pct:+.2f}%)")
        print(f"Trades:  {len(self.trades)}")
        
        return {
            'initial': self.initial_balance,
            'final': final['total_usd'],
            'profit': profit,
            'profit_pct': profit_pct,
            'trades': len(self.trades)
        }

if __name__ == '__main__':
    strategy = TradingStrategy()
    result = strategy.run(cycles=5)
