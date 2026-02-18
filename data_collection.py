"""
Web3Million数据采集模块
实现行情、链上、舆情数据的采集功能
支持Binance/OKX等主流交易所的数据获取
"""
import asyncio
import aiohttp
import ccxt.async_support as ccxt_async
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from redis_cache import Web3MillionCache, RedisCache
from database_setup import SessionLocal, OnchainData
import time
import json
import logging
from urllib.parse import urlencode
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    """
    数据采集器
    负责采集行情、链上、舆情等多维度数据
    """
    
    def __init__(self):
        # 初始化交易所连接（使用异步模式）
        self.binance = ccxt_async.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'  # 使用期货市场
            }
        })
        self.okx = ccxt_async.okx({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap'  # 使用永续合约
            }
        })
        
        # 初始化Redis缓存
        try:
            redis_cache = RedisCache(host='localhost', port=6379, db=0)
        except:
            redis_cache = RedisCache.__new__(RedisCache)
            redis_cache.redis_client = None
        self.cache = Web3MillionCache(redis_cache)
        
        # 初始化数据库会话
        self.db_session = SessionLocal()
        
        # 交易对配置
        self.symbols = ['BTC/USDT', 'ETH/USDT']
        self.timeframes = ['1m', '5m', '15m']
        
        logger.info("数据采集器初始化完成")
    
    async def fetch_market_data(self, exchange_name: str, symbol: str, timeframe: str = '1m', limit: int = 100) -> Optional[Dict]:
        """
        采集行情数据
        Key: market:{exchange}:{symbol}:kline_{cycle}
        """
        try:
            exchange = getattr(self, exchange_name.lower())
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # 转换为DataFrame格式
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # 构造返回数据
            market_data = {
                'symbol': symbol,
                'exchange': exchange_name,
                'timeframe': timeframe,
                'data': df.to_dict('records'),
                'last_updated': datetime.now().isoformat()
            }
            
            # 存入缓存
            cycle_minutes = {'1m': 1, '5m': 5, '15m': 15}.get(timeframe, 1)
            self.cache.set_market_data(exchange_name, symbol, cycle_minutes, market_data)
            
            logger.info(f"成功获取{exchange_name} {symbol} {timeframe}行情数据，共{len(ohlcv)}条记录")
            return market_data
            
        except Exception as e:
            logger.error(f"获取{exchange_name} {symbol} {timeframe}行情数据失败: {e}")
            return None
    
    async def fetch_all_market_data(self) -> Dict[str, Any]:
        """
        批量获取所有关注交易对的行情数据
        """
        all_market_data = {}
        
        for symbol in self.symbols:
            for timeframe in self.timeframes:
                # 获取Binance数据
                binance_data = await self.fetch_market_data('binance', symbol, timeframe)
                if binance_data:
                    key = f"binance_{symbol.replace('/', '_')}_{timeframe}"
                    all_market_data[key] = binance_data
                
                # 获取OKX数据
                okx_data = await self.fetch_market_data('okx', symbol, timeframe)
                if okx_data:
                    key = f"okx_{symbol.replace('/', '_')}_{timeframe}"
                    all_market_data[key] = okx_data
        
        logger.info(f"批量获取行情数据完成，共获取{len(all_market_data)}组数据")
        return all_market_data
    
    def fetch_onchain_data_akshare(self, symbol: str) -> Optional[Dict]:
        """
        通过AkShare获取链上数据
        """
        try:
            # 注意：AkShare的实际链上数据接口可能有限，这里使用模拟数据演示
            # 在实际部署中，可以使用Glassnode、CryptoQuant等专业链上数据提供商
            onchain_data = {
                'symbol': symbol,
                'datetime': datetime.now().isoformat(),
                'whale_transfer_type': 'neutral',  # 模拟值
                'whale_transfer_amount': 0.0,      # 模拟值
                'exchange_net_flow': 0.0,          # 模拟值
                'onchain_score': 0,                # 模拟值
                'source': 'AkShare'
            }
            
            # 尝试获取真实的链上数据（如果AkShare支持）
            # 示例：比特币活跃地址数
            try:
                # 这里可以接入真实的链上指标
                # 如：btc_active_addresses = ak.crypto_bitcoin_info() # 假设存在此接口
                pass
            except:
                pass
            
            # 存入缓存
            self.cache.set_onchain_data(symbol, onchain_data)
            
            logger.info(f"成功获取{symbol}链上数据")
            return onchain_data
            
        except Exception as e:
            logger.error(f"获取{symbol}链上数据失败: {e}")
            return None
    
    def fetch_news_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        获取舆情数据并进行情感分析
        """
        try:
            # 获取最新的加密货币新闻
            # 由于免费的新闻API受限，这里使用模拟数据
            news_data = {
                'symbol': symbol,
                'datetime': datetime.now().isoformat(),
                'news_count': 0,
                'sentiment_score': 0,  # -5到+5的情感分数
                'top_news': [],
                'source': 'Simulated'
            }
            
            # 在实际应用中，可以使用如下API：
            # 1. CryptoPanic API
            # 2. News API
            # 3. RSS订阅各种加密媒体
            # 4. 社交媒体API（Twitter等）
            
            # 模拟获取新闻
            logger.info(f"获取{symbol}舆情数据")
            return news_data
            
        except Exception as e:
            logger.error(f"获取{symbol}舆情数据失败: {e}")
            return None
    
    async def collect_all_data(self) -> Dict[str, Any]:
        """
        统一采集所有类型的数据
        """
        logger.info("开始采集所有数据...")
        
        # 采集行情数据
        market_data = await self.fetch_all_market_data()
        
        # 采集链上数据
        onchain_data = {}
        for symbol in self.symbols:
            btc_symbol = 'BTC' if 'BTC' in symbol else 'ETH' if 'ETH' in symbol else symbol.split('/')[0]
            onchain_result = self.fetch_onchain_data_akshare(btc_symbol)
            if onchain_result:
                onchain_data[f"{btc_symbol}_onchain"] = onchain_result
        
        # 采集舆情数据
        sentiment_data = {}
        for symbol in self.symbols:
            sentiment_result = self.fetch_news_sentiment(symbol)
            if sentiment_result:
                sentiment_data[f"{symbol}_sentiment"] = sentiment_result
        
        # 组织返回数据
        all_data = {
            'market_data': market_data,
            'onchain_data': onchain_data,
            'sentiment_data': sentiment_data,
            'collection_time': datetime.now().isoformat()
        }
        
        logger.info("数据采集完成")
        return all_data
    
    def simulate_real_onchain_data(self, symbol: str) -> Dict:
        """
        模拟真实的链上数据（在没有真实API的情况下）
        """
        # 生成模拟的链上指标
        import random
        
        # 随机生成链上活动指标
        whale_activity = random.choice(['to_exchange', 'from_exchange', 'neutral'])
        whale_amount = round(random.uniform(-500, 500), 2)  # 巨鲸转账数量
        net_flow = round(random.uniform(-1000, 1000), 2)    # 交易所净流入
        score = random.randint(-15, 15)                     # 链上得分
        
        onchain_data = {
            'symbol': symbol,
            'datetime': datetime.now().isoformat(),
            'whale_transfer_type': whale_activity,
            'whale_transfer_amount': whale_amount,
            'exchange_net_flow': net_flow,
            'onchain_score': score,
            'source': 'Simulated_Realistic'
        }
        
        # 存入缓存
        self.cache.set_onchain_data(symbol, onchain_data)
        
        return onchain_data
    
    def simulate_real_sentiment_data(self, symbol: str) -> Dict:
        """
        模拟真实的舆情数据
        """
        import random
        
        # 模拟新闻情感分析结果
        sentiment_score = random.randint(-5, 5)  # -5到+5的情感分数
        
        sentiment_data = {
            'symbol': symbol,
            'datetime': datetime.now().isoformat(),
            'news_count': random.randint(0, 10),
            'sentiment_score': sentiment_score,
            'top_news': [
                f"新闻标题关于{symbol}",
                f"市场动态：{symbol}走势分析"
            ],
            'source': 'Simulated_Realistic'
        }
        
        return sentiment_data
    
    async def close(self):
        """
        关闭数据采集器
        """
        await self.binance.close()
        await self.okx.close()
        self.db_session.close()
        logger.info("数据采集器已关闭")


class DataCollectionService:
    """
    数据采集服务类
    提供定时采集和数据处理功能
    """
    
    def __init__(self):
        self.collector = DataCollector()
        self.running = False
    
    async def run_market_collection(self):
        """
        运行行情数据采集任务
        频率: 1分钟/次
        """
        logger.info("启动行情数据采集任务")
        
        while self.running:
            try:
                market_data = await self.collector.fetch_all_market_data()
                logger.info(f"行情数据采集完成，获取到{len(market_data)}组数据")
                
                # 模拟数据处理和存储
                for key, data in market_data.items():
                    if data and 'data' in data and len(data['data']) > 0:
                        latest_candle = data['data'][-1]  # 最新K线数据
                        logger.debug(f"{key}: 最新价格 {latest_candle['close']}")
                
                # 每分钟采集一次
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"行情数据采集任务出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
    
    def run_onchain_collection(self):
        """
        运行链上数据采集任务
        频率: 5分钟/次
        """
        logger.info("启动链上数据采集任务")
        
        while self.running:
            try:
                onchain_data = {}
                for symbol in self.collector.symbols:
                    btc_symbol = 'BTC' if 'BTC' in symbol else 'ETH' if 'ETH' in symbol else symbol.split('/')[0]
                    # 使用模拟的真实链上数据
                    onchain_result = self.collector.simulate_real_onchain_data(btc_symbol)
                    if onchain_result:
                        onchain_data[f"{btc_symbol}_onchain"] = onchain_result
                
                logger.info(f"链上数据采集完成，获取到{len(onchain_data)}组数据")
                
                # 每5分钟采集一次
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"链上数据采集任务出错: {e}")
                time.sleep(300)  # 出错后等待5分钟再继续
    
    def run_sentiment_collection(self):
        """
        运行舆情数据采集任务
        频率: 30分钟/次
        """
        logger.info("启动舆情数据采集任务")
        
        while self.running:
            try:
                sentiment_data = {}
                for symbol in self.collector.symbols:
                    sentiment_result = self.collector.simulate_real_sentiment_data(symbol)
                    if sentiment_result:
                        sentiment_data[f"{symbol}_sentiment"] = sentiment_result
                
                logger.info(f"舆情数据采集完成，获取到{len(sentiment_data)}组数据")
                
                # 每30分钟采集一次
                time.sleep(1800)
                
            except Exception as e:
                logger.error(f"舆情数据采集任务出错: {e}")
                time.sleep(1800)  # 出错后等待30分钟再继续
    
    async def start_all_tasks(self):
        """
        启动所有数据采集任务
        """
        self.running = True
        logger.info("启动所有数据采集任务")
        
        # 创建任务
        market_task = asyncio.create_task(self.run_market_collection())
        # 由于其他任务是同步的，我们在独立线程中运行它们
        import threading
        
        onchain_thread = threading.Thread(target=self.run_onchain_collection)
        sentiment_thread = threading.Thread(target=self.run_sentiment_collection)
        
        onchain_thread.daemon = True
        sentiment_thread.daemon = True
        
        onchain_thread.start()
        sentiment_thread.start()
        
        try:
            # 等待市场数据采集任务完成（实际上它会一直运行）
            await market_task
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止数据采集任务")
        finally:
            self.stop_all_tasks()
    
    def stop_all_tasks(self):
        """
        停止所有数据采集任务
        """
        self.running = False
        logger.info("已停止所有数据采集任务")
    
    async def collect_once(self) -> Dict[str, Any]:
        """
        执行一次性数据采集
        """
        logger.info("执行一次性数据采集")
        return await self.collector.collect_all_data()


async def main():
    """
    主函数 - 演示数据采集功能
    """
    logger.info("启动Web3Million数据采集模块")
    
    service = DataCollectionService()
    
    # 执行一次性数据采集以验证功能
    result = await service.collect_once()
    
    print("数据采集结果摘要:")
    print(f"- 市场数据组数: {len(result.get('market_data', {}))}")
    print(f"- 链上数据组数: {len(result.get('onchain_data', {}))}")
    print(f"- 舆情数据组数: {len(result.get('sentiment_data', {}))}")
    print(f"- 采集时间: {result.get('collection_time')}")
    
    # 显示一些具体的市场数据样本
    market_data = result.get('market_data', {})
    for key, data in list(market_data.items())[:2]:  # 只显示前2个
        if data and 'data' in data and len(data['data']) > 0:
            latest = data['data'][-1]
            print(f"- {key}: 价格 {latest['close']}, 时间 {datetime.fromtimestamp(latest['timestamp']/1000)}")
    
    # 显示链上数据样本
    onchain_data = result.get('onchain_data', {})
    for key, data in onchain_data.items():
        print(f"- {key}: 得分 {data.get('onchain_score', 0)}, 活动类型 {data.get('whale_transfer_type', 'N/A')}")
    
    logger.info("数据采集演示完成")


if __name__ == "__main__":
    asyncio.run(main())