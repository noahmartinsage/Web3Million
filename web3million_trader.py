#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 实盘交易控制器
使用OKX测试网进行真实交易验证
"""
import ccxt
import json
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class Web3MillionTrader:
    def __init__(self):
        # 初始化OKX测试网
        self.exchange = ccxt.okx({
            'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
            'secret': '76122A8879980469F474F042135584DB',
            'password': 'Qian159.',
            'testnet': True
        })
        self.running = True
        self.trade_count = 0
        
    def get_balance(self):
        """获取账户余额"""
        balance = self.exchange.fetch_balance()
        return {
            'USDT': balance['free'].get('USDT', 0),
            'BTC': balance['free'].get('BTC', 0),
            'ETH': balance['free'].get('ETH', 0)
        }
    
    def get_price(self, symbol='BTC/USDT'):
        """获取价格"""
        ticker = self.exchange.fetch_ticker(symbol)
        return {
            'last': ticker['last'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'volume': ticker['quoteVolume']
        }
    
    def buy(self, symbol, amount):
        """市价买入"""
        try:
            order = self.exchange.create_market_buy_order(symbol, amount)
            self.trade_count += 1
            return {
                'success': True,
                'order_id': order['id'],
                'amount': amount,
                'symbol': symbol
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sell(self, symbol, amount):
        """市价卖出"""
        try:
            order = self.exchange.create_market_sell_order(symbol, amount)
            self.trade_count += 1
            return {
                'success': True,
                'order_id': order['id'],
                'amount': amount,
                'symbol': symbol
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_order_book(self, symbol='BTC/USDT', limit=5):
        """获取订单簿"""
        ob = self.exchange.fetch_order_book(symbol, limit)
        return ob
    
    def scan_opportunities(self):
        """扫描交易机会"""
        opportunities = []
        
        # 检查多个交易对
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        
        for symbol in symbols:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                spread = (ticker['ask'] - ticker['bid']) / ticker['last'] * 100
                
                # 简单的价差交易机会
                if spread > 0.1:  # 价差大于0.1%
                    opportunities.append({
                        'symbol': symbol,
                        'spread': spread,
                        'bid': ticker['bid'],
                        'ask': ticker['ask'],
                        'volume': ticker['quoteVolume']
                    })
            except:
                pass
        
        return opportunities
    
    def run_trading_cycle(self, cycles=5):
        """运行交易循环"""
        print("\n" + "="*50)
        print("Web3Million Trading Cycle Started")
        print("="*50)
        
        for i in range(cycles):
            print(f"\n--- Cycle {i+1}/{cycles} ---")
            
            # 获取余额
            bal = self.get_balance()
            print(f"Balance: {bal['USDT']:.2f} USDT | {bal['BTC']:.4f} BTC | {bal['ETH']:.4f} ETH")
            
            # 获取BTC价格
            btc_price = self.get_price('BTC/USDT')
            print(f"BTC Price: ${btc_price['last']:.2f}")
            
            # 扫描机会
            ops = self.scan_opportunities()
            if ops:
                print(f"Found {len(ops)} opportunities")
                for op in ops:
                    print(f"  {op['symbol']}: spread {op['spread']:.3f}%")
            
            # 如果有足够USDT且没有持仓，可以买入
            if bal['USDT'] > 100 and bal['BTC'] < 0.01:
                print("Attempting to buy BTC...")
                result = self.buy('BTC/USDT', 0.001)
                if result['success']:
                    print(f"  Buy order placed: {result['order_id']}")
                else:
                    print(f"  Buy failed: {result.get('error')}")
            
            time.sleep(2)  # 等待2秒
        
        print(f"\n=== Trading completed. Total trades: {self.trade_count} ===")

def main():
    trader = Web3MillionTrader()
    
    print("=== Web3Million Trader Started ===")
    
    # 显示初始状态
    bal = trader.get_balance()
    print(f"\nInitial Balance:")
    print(f"  USDT: {bal['USDT']:.2f}")
    print(f"  BTC: {bal['BTC']:.4f}")
    print(f"  ETH: {bal['ETH']:.4f}")
    
    # 运行交易循环
    trader.run_trading_cycle(cycles=3)
    
    # 显示最终状态
    print("\nFinal Balance:")
    final_bal = trader.get_balance()
    print(f"  USDT: {final_bal['USDT']:.2f}")
    print(f"  BTC: {final_bal['BTC']:.4f}")
    print(f"  ETH: {final_bal['ETH']:.4f}")

if __name__ == '__main__':
    main()
