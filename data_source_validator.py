"""
数据源验证器
确保使用真实及时的官方数据源
"""

import asyncio
import ccxt.async_support as ccxt_async
import aiohttp
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class DataSourceValidator:
    """数据源验证器"""
    
    def __init__(self):
        self.exchanges = {}
        self.data_sources = {}
        
    async def initialize_exchanges(self):
        """初始化交易所连接"""
        print("📡 初始化数据源...")
        
        # 创建多个交易所实例用于数据验证
        exchange_configs = {
            'okx': {
                'apiKey': '',
                'secret': '',
                'password': '',
                'sandbox': True,  # 测试网模式
            },
            'binance': {
                'apiKey': '',
                'secret': '',
                'sandbox': True,  # 测试网模式
            },
            'bybit': {
                'apiKey': '',
                'secret': '',
                'sandbox': True,  # 测试网模式
            }
        }
        
        for name, config in exchange_configs.items():
            try:
                exchange_class = getattr(ccxt_async, name)
                exchange = exchange_class(config)
                exchange.enableRateLimit = True
                self.exchanges[name] = exchange
                print(f"✅ {name.upper()} 数据源已连接")
            except Exception as e:
                print(f"⚠️ {name.upper()} 数据源连接失败: {e}")
        
        print(f"📊 共连接 {len(self.exchanges)} 个数据源")
    
    async def fetch_ticker_consistency(self, symbol: str = "BTC/USDT") -> Dict:
        """获取多个交易所的价格数据以验证一致性"""
        print(f"🔍 验证 {symbol} 价格一致性...")
        
        tickers = {}
        for name, exchange in self.exchanges.items():
            try:
                ticker = await exchange.fetch_ticker(symbol)
                tickers[name] = {
                    'last': ticker.get('last'),
                    'bid': ticker.get('bid'),
                    'ask': ticker.get('ask'),
                    'timestamp': ticker.get('timestamp'),
                    'datetime': ticker.get('datetime')
                }
                print(f"   {name.upper()}: ${ticker.get('last', 'N/A')}")
            except Exception as e:
                print(f"   {name.upper()}: 获取失败 - {e}")
        
        return tickers
    
    async def validate_price_accuracy(self, symbol: str = "BTC/USDT", tolerance: float = 0.01) -> bool:
        """验证价格准确性（在容差范围内）"""
        print(f"🔍 验证 {symbol} 价格准确性 (容差: {tolerance*100}%)...")
        
        tickers = await self.fetch_ticker_consistency(symbol)
        
        # 获取所有有效价格
        prices = [data['last'] for data in tickers.values() if data['last'] is not None]
        
        if len(prices) < 2:
            print("⚠️  价格数据不足，无法验证一致性")
            return False
        
        # 计算价格范围
        min_price = min(prices)
        max_price = max(prices)
        price_range = max_price - min_price
        avg_price = sum(prices) / len(prices)
        
        # 检查价格是否在容差范围内
        price_diff_percent = price_range / avg_price if avg_price != 0 else 0
        
        print(f"   价格范围: ${min_price:.4f} - ${max_price:.4f}")
        print(f"   平均价格: ${avg_price:.4f}")
        print(f"   价格差异: {price_diff_percent*100:.4f}%")
        
        if price_diff_percent <= tolerance:
            print(f"✅ 价格一致性验证通过 (差异: {price_diff_percent*100:.4f}% ≤ {tolerance*100}%)")
            return True
        else:
            print(f"❌ 价格一致性验证失败 (差异: {price_diff_percent*100:.4f}% > {tolerance*100}%)")
            return False
    
    async def validate_latency(self, symbol: str = "BTC/USDT") -> Dict:
        """验证数据延迟"""
        print(f"⏱️ 验证 {symbol} 数据延迟...")
        
        latency_results = {}
        for name, exchange in self.exchanges.items():
            try:
                start_time = time.time()
                ticker = await exchange.fetch_ticker(symbol)
                end_time = time.time()
                
                api_latency = (end_time - start_time) * 1000  # 转换为毫秒
                timestamp = ticker.get('timestamp')
                
                if timestamp:
                    # 计算数据新鲜度（假设timestamp是以毫秒为单位）
                    current_time_ms = int(time.time() * 1000)
                    data_age_ms = current_time_ms - timestamp
                    total_latency = api_latency + data_age_ms
                    
                    latency_results[name] = {
                        'api_latency_ms': api_latency,
                        'data_age_ms': data_age_ms,
                        'total_latency_ms': total_latency
                    }
                    
                    print(f"   {name.upper()}: API延迟 {api_latency:.2f}ms, 数据年龄 {data_age_ms:.2f}ms, 总延迟 {total_latency:.2f}ms")
                else:
                    print(f"   {name.upper()}: 无法获取时间戳信息")
            except Exception as e:
                print(f"   {name.upper()}: 延迟测试失败 - {e}")
        
        return latency_results
    
    async def stress_test_connections(self, symbol: str = "BTC/USDT", duration: int = 30, interval: float = 1.0):
        """压力测试连接稳定性"""
        print(f"💪 压力测试连接稳定性 (持续 {duration} 秒, 间隔 {interval}s)...")
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        total_requests = 0
        
        while time.time() - start_time < duration:
            for name, exchange in self.exchanges.items():
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    success_count += 1
                    total_requests += 1
                except Exception as e:
                    error_count += 1
                    total_requests += 1
                    print(f"   {name.upper()} 请求失败: {e}")
            
            await asyncio.sleep(interval)
        
        success_rate = (success_count / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"📈 压力测试结果:")
        print(f"   总请求数: {total_requests}")
        print(f"   成功: {success_count}")
        print(f"   失败: {error_count}")
        print(f"   成功率: {success_rate:.2f}%")
        
        return {
            'success_rate': success_rate,
            'total_requests': total_requests,
            'success_count': success_count,
            'error_count': error_count
        }
    
    async def validate_data_integrity(self, symbol: str = "BTC/USDT") -> bool:
        """验证数据完整性"""
        print(f"🛡️ 验证 {symbol} 数据完整性...")
        
        for name, exchange in self.exchanges.items():
            try:
                # 获取多种类型的数据以验证完整性
                ticker = await exchange.fetch_ticker(symbol)
                orderbook = await exchange.fetch_order_book(symbol, limit=5)
                trades = await exchange.fetch_trades(symbol, limit=5)
                
                # 验证必要字段是否存在
                required_ticker_fields = ['symbol', 'last', 'timestamp']
                ticker_valid = all(field in ticker for field in required_ticker_fields)
                
                required_orderbook_fields = ['bids', 'asks', 'timestamp']
                orderbook_valid = all(field in orderbook for field in required_orderbook_fields)
                
                print(f"   {name.upper()}: Ticker完整: {'✅' if ticker_valid else '❌'}, OrderBook完整: {'✅' if orderbook_valid else '❌'}, Trades: {len(trades) if trades else 0}")
                
                if not (ticker_valid and orderbook_valid):
                    print(f"   {name.upper()}: 数据完整性验证失败")
                    return False
                    
            except Exception as e:
                print(f"   {name.upper()}: 数据完整性验证异常 - {e}")
                return False
        
        print("✅ 所有数据源完整性验证通过")
        return True
    
    async def generate_validation_report(self) -> Dict:
        """生成验证报告"""
        print("📋 生成数据源验证报告...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_results': {},
            'latency_analysis': {},
            'stress_test_results': {},
            'data_integrity': False,
            'price_consistency': False,
            'overall_score': 0
        }
        
        # 执行各项验证
        if self.exchanges:
            # 价格一致性验证
            report['price_consistency'] = await self.validate_price_accuracy()
            
            # 延迟分析
            report['latency_analysis'] = await self.validate_latency()
            
            # 数据完整性验证
            report['data_integrity'] = await self.validate_data_integrity()
            
            # 压力测试
            report['stress_test_results'] = await self.stress_test_connections(duration=15, interval=0.5)
            
            # 计算整体分数
            score_components = [
                report['price_consistency'],
                report['data_integrity'],
                report['stress_test_results']['success_rate'] >= 95  # 成功率需≥95%
            ]
            
            report['overall_score'] = sum(score_components) / len(score_components) * 100
            
            print(f"🎯 整体数据源质量得分: {report['overall_score']:.2f}/100")
        
        return report
    
    async def close_connections(self):
        """关闭所有连接"""
        for name, exchange in self.exchanges.items():
            try:
                await exchange.close()
            except:
                pass
        print("🔒 所有数据源连接已关闭")


async def main():
    """主函数"""
    validator = DataSourceValidator()
    
    try:
        # 初始化交易所连接
        await validator.initialize_exchanges()
        
        if not validator.exchanges:
            print("❌ 未能连接到任何数据源，验证无法进行")
            return
        
        # 执行验证
        report = await validator.generate_validation_report()
        
        print(f"\n✅ 数据源验证完成!")
        print(f"📊 验证结果摘要:")
        print(f"   价格一致性: {'✅' if report['price_consistency'] else '❌'}")
        print(f"   数据完整性: {'✅' if report['data_integrity'] else '❌'}")
        print(f"   整体质量得分: {report['overall_score']:.2f}/100")
        
        if report['overall_score'] >= 80:
            print(f"🎉 数据源质量优秀，适合AI Agent策略执行!")
        elif report['overall_score'] >= 60:
            print(f"👍 数据源质量良好，可满足基本需求")
        else:
            print(f"⚠️ 数据源质量有待提升")
            
    finally:
        await validator.close_connections()


if __name__ == "__main__":
    asyncio.run(main())