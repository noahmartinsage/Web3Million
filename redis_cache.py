"""
Web3Million Redis缓存策略
实现键值设计规范和缓存机制，支持量化交易系统的高性能数据访问
"""
import redis
import json
import pickle
from typing import Any, Optional, Union, List, Dict
from datetime import datetime, timedelta
import hashlib
from database_setup import TradeRecord, IndicatorData, OnchainData, Alert
from sqlalchemy.orm import Session
from api_framework import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

class RedisCache:
    """
    Redis缓存管理类
    实现Web3Million系统的缓存策略
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: str = None):
        """
        初始化Redis连接
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,  # 保持二进制模式以支持pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.redis_client.ping()
            print("Redis连接成功")
        except redis.ConnectionError:
            print("无法连接到Redis，使用模拟缓存")
            self.redis_client = None
    
    def _serialize(self, obj: Any) -> bytes:
        """
        序列化对象
        """
        return pickle.dumps(obj)
    
    def _deserialize(self, data: bytes) -> Any:
        """
        反序列化对象
        """
        if data is None:
            return None
        return pickle.loads(data)
    
    def _make_key(self, prefix: str, *args) -> str:
        """
        生成缓存键
        """
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存值
        """
        if self.redis_client is None:
            return False
        
        try:
            serialized_value = self._serialize(value)
            if expire:
                result = self.redis_client.setex(key, expire, serialized_value)
            else:
                result = self.redis_client.set(key, serialized_value)
            return result == b'OK' or result is True
        except Exception as e:
            print(f"设置缓存失败: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        """
        if self.redis_client is None:
            return None
        
        try:
            value = self.redis_client.get(key)
            return self._deserialize(value)
        except Exception as e:
            print(f"获取缓存失败: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        """
        if self.redis_client is None:
            return False
        
        try:
            result = self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"删除缓存失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        """
        if self.redis_client is None:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"检查键存在失败: {e}")
            return False
    
    def set_with_compression(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        设置缓存值（带压缩）
        """
        if self.redis_client is None:
            return False
        
        try:
            # 对大数据进行简单压缩（这里只是序列化，实际可以引入gzip）
            serialized_value = self._serialize(value)
            if expire:
                result = self.redis_client.setex(key, expire, serialized_value)
            else:
                result = self.redis_client.set(key, serialized_value)
            return result == b'OK' or result is True
        except Exception as e:
            print(f"设置压缩缓存失败: {e}")
            return False


class Web3MillionCache:
    """
    Web3Million专用缓存类
    实现特定的缓存策略和键值设计
    """
    
    def __init__(self, redis_client: RedisCache):
        self.cache = redis_client
    
    def set_market_data(self, exchange: str, symbol: str, cycle: int, data: Dict) -> bool:
        """
        设置市场数据缓存
        Key: market:{exchange}:{symbol}:kline_{cycle}
        过期时间: 1分钟
        """
        key = f"market:{exchange}:{symbol}:kline_{cycle}"
        return self.cache.set(key, data, expire=60)  # 1分钟过期
    
    def get_market_data(self, exchange: str, symbol: str, cycle: int) -> Optional[Dict]:
        """
        获取市场数据缓存
        """
        key = f"market:{exchange}:{symbol}:kline_{cycle}"
        return self.cache.get(key)
    
    def set_onchain_data(self, symbol: str, data: Dict) -> bool:
        """
        设置链上数据缓存
        Key: onchain:{symbol}:latest
        过期时间: 5分钟
        """
        key = f"onchain:{symbol}:latest"
        return self.cache.set(key, data, expire=300)  # 5分钟过期
    
    def get_onchain_data(self, symbol: str) -> Optional[Dict]:
        """
        获取链上数据缓存
        """
        key = f"onchain:{symbol}:latest"
        return self.cache.get(key)
    
    def set_indicator_data(self, symbol: str, data: Dict) -> bool:
        """
        设置指标数据缓存
        Key: indicator:{symbol}:latest
        过期时间: 1分钟
        """
        key = f"indicator:{symbol}:latest"
        return self.cache.set(key, data, expire=60)  # 1分钟过期
    
    def get_indicator_data(self, symbol: str) -> Optional[Dict]:
        """
        获取指标数据缓存
        """
        key = f"indicator:{symbol}:latest"
        return self.cache.get(key)
    
    def set_strategy_signal(self, symbol: str, data: Dict) -> bool:
        """
        设置策略信号缓存
        Key: strategy:{symbol}:latest_signal
        过期时间: 1分钟
        """
        key = f"strategy:{symbol}:latest_signal"
        return self.cache.set(key, data, expire=60)  # 1分钟过期
    
    def get_strategy_signal(self, symbol: str) -> Optional[Dict]:
        """
        获取策略信号缓存
        """
        key = f"strategy:{symbol}:latest_signal"
        return self.cache.get(key)
    
    def set_ai_weights(self, symbol: str, weights: Dict) -> bool:
        """
        设置AI权重缓存
        Key: ai:{symbol}:current_weights
        过期时间: 7天
        """
        key = f"ai:{symbol}:current_weights"
        return self.cache.set(key, weights, expire=7*24*3600)  # 7天过期
    
    def get_ai_weights(self, symbol: str) -> Optional[Dict]:
        """
        获取AI权重缓存
        """
        key = f"ai:{symbol}:current_weights"
        return self.cache.get(key)
    
    def set_position_data(self, exchange: str, symbol: str, data: Dict) -> bool:
        """
        设置持仓数据缓存
        Key: position:{exchange}:{symbol}
        过期时间: 10秒
        """
        key = f"position:{exchange}:{symbol}"
        return self.cache.set(key, data, expire=10)  # 10秒过期
    
    def get_position_data(self, exchange: str, symbol: str) -> Optional[Dict]:
        """
        获取持仓数据缓存
        """
        key = f"position:{exchange}:{symbol}"
        return self.cache.get(key)
    
    def set_order_data(self, exchange: str, order_id: str, data: Dict) -> bool:
        """
        设置订单数据缓存
        Key: order:{exchange}:{order_id}
        过期时间: 24小时
        """
        key = f"order:{exchange}:{order_id}"
        return self.cache.set(key, data, expire=24*3600)  # 24小时过期
    
    def get_order_data(self, exchange: str, order_id: str) -> Optional[Dict]:
        """
        获取订单数据缓存
        """
        key = f"order:{exchange}:{order_id}"
        return self.cache.get(key)
    
    def acquire_trade_lock(self, symbol: str, side: str, ttl: int = 30) -> bool:
        """
        获取交易锁（防重复下单）
        Key: lock:trade:{symbol}:{side}
        过期时间: 30秒
        """
        key = f"lock:trade:{symbol}:{side}"
        # 使用SET命令的NX和EX选项实现分布式锁
        if self.cache.redis_client:
            result = self.cache.redis_client.redis_client.set(
                key, 
                f"{datetime.now().isoformat()}:{os.getpid()}", 
                nx=True,  # 仅当key不存在时设置
                ex=ttl     # 设置过期时间
            )
            return result is not None
        return False
    
    def release_trade_lock(self, symbol: str, side: str) -> bool:
        """
        释放交易锁
        """
        key = f"lock:trade:{symbol}:{side}"
        return self.cache.delete(key)
    
    def add_alert_to_queue(self, alert_data: Dict) -> bool:
        """
        添加警报到队列
        Key: alert:unread
        使用列表结构存储未读警报
        """
        key = "alert:unread"
        if self.cache.redis_client:
            try:
                serialized_alert = self.cache._serialize(alert_data)
                result = self.cache.redis_client.lpush(key, serialized_alert)
                # 限制队列长度为100
                self.cache.redis_client.ltrim(key, 0, 99)
                return result is not None
            except Exception as e:
                print(f"添加警报到队列失败: {e}")
                return False
        return False
    
    def get_unread_alerts(self, count: int = 10) -> List[Dict]:
        """
        获取未读警报
        """
        key = "alert:unread"
        if self.cache.redis_client:
            try:
                # 获取列表中的元素
                alerts_bytes = self.cache.redis_client.lrange(key, 0, count-1)
                alerts = []
                for alert_bytes in alerts_bytes:
                    alert = self.cache._deserialize(alert_bytes)
                    if alert:
                        alerts.append(alert)
                return alerts
            except Exception as e:
                print(f"获取未读警报失败: {e}")
                return []
        return []


def test_redis_cache():
    """
    测试Redis缓存功能
    """
    print("开始测试Redis缓存功能...")
    
    # 尝试连接Redis，如果失败则使用模拟缓存
    try:
        cache = RedisCache(host='localhost', port=6379, db=0)
    except:
        print("Redis未运行，创建模拟缓存实例")
        cache = RedisCache.__new__(RedisCache)  # 创建实例而不调用__init__
        cache.redis_client = None
    
    web3_cache = Web3MillionCache(cache)
    
    # 测试市场数据缓存
    market_data = {
        "symbol": "BTC/USDT",
        "exchange": "binance",
        "cycle": 15,
        "klines": [
            {"open": 40000, "high": 41000, "low": 39500, "close": 40800, "volume": 100},
            {"open": 40800, "high": 41500, "low": 40500, "close": 41200, "volume": 120}
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    success = web3_cache.set_market_data("binance", "BTC/USDT", 15, market_data)
    print(f"设置市场数据缓存: {'成功' if success else '失败'}")
    
    retrieved_data = web3_cache.get_market_data("binance", "BTC/USDT", 15)
    print(f"获取市场数据缓存: {'成功' if retrieved_data is not None else '失败'}")
    
    # 测试AI权重缓存
    weights = {
        "onchain": 30,
        "tech": 35,
        "sentiment": 5,
        "trend": 20
    }
    
    success = web3_cache.set_ai_weights("BTC/USDT", weights)
    print(f"设置AI权重缓存: {'成功' if success else '失败'}")
    
    retrieved_weights = web3_cache.get_ai_weights("BTC/USDT")
    print(f"获取AI权重缓存: {'成功' if retrieved_weights is not None else '失败'}")
    
    # 测试交易锁
    lock_acquired = web3_cache.acquire_trade_lock("BTC/USDT", "long", 30)
    print(f"获取交易锁: {'成功' if lock_acquired else '失败'}")
    
    if lock_acquired:
        lock_released = web3_cache.release_trade_lock("BTC/USDT", "long")
        print(f"释放交易锁: {'成功' if lock_released else '失败'}")
    
    # 测试警报队列
    alert_data = {
        "type": "trade_signal",
        "title": "交易信号",
        "content": "BTC/USDT 发出买入信号",
        "timestamp": datetime.now().isoformat()
    }
    
    queue_success = web3_cache.add_alert_to_queue(alert_data)
    print(f"添加警报到队列: {'成功' if queue_success else '失败'}")
    
    alerts = web3_cache.get_unread_alerts(5)
    print(f"获取未读警报: {len(alerts)} 条")
    
    print("Redis缓存功能测试完成！")


if __name__ == "__main__":
    test_redis_cache()