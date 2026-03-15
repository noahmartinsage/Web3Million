#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEV Bot - 套利机会检测器 v1.0
实时检测DEX之间的价格差异，发现套利机会
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import logging
from dataclasses import dataclass
import math

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Token:
    """代币信息"""
    symbol: str
    address: str
    decimals: int = 18


@dataclass
class ArbitrageOpportunity:
    """套利机会"""
    token_pair: Tuple[str, str]
    buy_dex: str
    sell_dex: str
    buy_price: float
    sell_price: float
    price_diff_pct: float
    potential_profit_usd: float
    timestamp: str


class DEXPriceFetcher:
    """DEX价格获取器"""
    
    def __init__(self, w3: Web3):
        self.w3 = w3
        
        # DEX Router合约地址
        self.dex_routers = {
            'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            'sushiswap': '0xd9e1cE17a264Dd44cAaC8B4b9D8B5675C6F0E8B0',
            # Uniswap V3 需要不同的处理方式
        }
        
        # 常见代币地址
        self.tokens = {
            'WETH': Token('WETH', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'),
            'USDC': Token('USDC', '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 6),
            'USDT': Token('USDT', '0xdAC17F958D2ee523a2206206994597C13D831ec7', 6),
            'DAI': Token('DAI', '0x6B175474E89094C44Da98b954EessdCdAE3F2725'),
            'WBTC': Token('WBTC', '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 8),
        }
        
        # Router ABI（简化版，只包含getAmountsOut）
        self.router_abi = json.loads('''
        [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [
                    {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        ''')
    
    async def get_price(
        self,
        dex_name: str,
        token_in: Token,
        token_out: Token,
        amount: float = 1.0
    ) -> Optional[float]:
        """
        获取DEX价格
        
        Args:
            dex_name: DEX名称
            token_in: 输入代币
            token_out: 输出代币
            amount: 输入金额
        
        Returns:
            输出金额（价格）
        """
        try:
            router_address = self.dex_routers.get(dex_name)
            if not router_address:
                return None
            
            router = self.w3.eth.contract(
                address=Web3.to_checksum_address(router_address),
                abi=self.router_abi
            )
            
            # 准备参数
            amount_in_wei = int(amount * (10 ** token_in.decimals))
            path = [
                Web3.to_checksum_address(token_in.address),
                Web3.to_checksum_address(token_out.address)
            ]
            
            # 调用合约
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            
            # 转换输出金额
            amount_out = amounts[1] / (10 ** token_out.decimals)
            
            return amount_out
            
        except Exception as e:
            logger.debug(f"获取{dex_name}价格失败: {e}")
            return None
    
    async def get_all_prices(
        self,
        token_pairs: List[Tuple[str, str]]
    ) -> Dict[str, Dict[str, float]]:
        """
        批量获取所有DEX价格
        
        Returns:
            {
                'WETH/USDC': {
                    'uniswap_v2': 2000.5,
                    'sushiswap': 2002.3,
                },
                ...
            }
        """
        prices = {}
        
        for token_a_symbol, token_b_symbol in token_pairs:
            token_a = self.tokens.get(token_a_symbol)
            token_b = self.tokens.get(token_b_symbol)
            
            if not token_a or not token_b:
                continue
            
            pair_key = f"{token_a_symbol}/{token_b_symbol}"
            prices[pair_key] = {}
            
            # 并行获取所有DEX价格
            tasks = []
            for dex_name in self.dex_routers.keys():
                task = self.get_price(dex_name, token_a, token_b, 1.0)
                tasks.append((dex_name, task))
            
            # 等待所有价格
            for dex_name, task in tasks:
                try:
                    price = await task
                    if price:
                        prices[pair_key][dex_name] = price
                except Exception as e:
                    logger.debug(f"获取{dex_name}价格失败: {e}")
        
        return prices


class ArbitrageDetector:
    """套利机会检测器"""
    
    def __init__(
        self,
        w3: Web3,
        min_profit_usd: float = 10.0,
        min_price_diff_pct: float = 0.5
    ):
        """
        初始化套利检测器
        
        Args:
            w3: Web3实例
            min_profit_usd: 最小利润（美元）
            min_price_diff_pct: 最小价格差异百分比
        """
        self.price_fetcher = DEXPriceFetcher(w3)
        self.min_profit_usd = min_profit_usd
        self.min_price_diff_pct = min_price_diff_pct
        
        # 监控的交易对
        self.watch_pairs = [
            ('WETH', 'USDC'),
            ('WETH', 'USDT'),
            ('WETH', 'DAI'),
            ('WBTC', 'WETH'),
            ('WBTC', 'USDC'),
        ]
        
        # 统计
        self.stats = {
            'total_checks': 0,
            'opportunities_found': 0,
            'total_profit_potential': 0.0
        }
    
    async def scan(self) -> List[ArbitrageOpportunity]:
        """扫描套利机会"""
        opportunities = []
        
        # 获取所有价格
        prices = await self.price_fetcher.get_all_prices(self.watch_pairs)
        
        self.stats['total_checks'] += 1
        
        # 分析每个交易对
        for pair_key, dex_prices in prices.items():
            if len(dex_prices) < 2:
                continue
            
            # 找出最高价和最低价DEX
            sorted_dexes = sorted(dex_prices.items(), key=lambda x: x[1], reverse=True)
            
            highest_dex, highest_price = sorted_dexes[0]
            lowest_dex, lowest_price = sorted_dexes[-1]
            
            # 计算价格差
            price_diff_pct = ((highest_price - lowest_price) / lowest_price) * 100
            
            # 检查是否满足最小利润要求
            if price_diff_pct >= self.min_price_diff_pct:
                # 计算潜在利润（假设交易100 ETH）
                trade_amount = 100  # ETH
                potential_profit = trade_amount * (price_diff_pct / 100)
                potential_profit_usd = potential_profit * 2000  # 假设ETH价格$2000
                
                if potential_profit_usd >= self.min_profit_usd:
                    token_pair = tuple(pair_key.split('/'))
                    
                    opportunity = ArbitrageOpportunity(
                        token_pair=token_pair,
                        buy_dex=lowest_dex,
                        sell_dex=highest_dex,
                        buy_price=lowest_price,
                        sell_price=highest_price,
                        price_diff_pct=price_diff_pct,
                        potential_profit_usd=potential_profit_usd,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    opportunities.append(opportunity)
                    
                    self.stats['opportunities_found'] += 1
                    self.stats['total_profit_potential'] += potential_profit_usd
                    
                    # 打印发现
                    logger.info(
                        f"\n💰 发现套利机会！\n"
                        f"   交易对: {pair_key}\n"
                        f"   买入: {lowest_dex} @ {lowest_price:.6f}\n"
                        f"   卖出: {highest_dex} @ {highest_price:.6f}\n"
                        f"   价差: {price_diff_pct:.3f}%\n"
                        f"   潜在利润: ${potential_profit_usd:.2f}"
                    )
        
        return opportunities
    
    def print_stats(self):
        """打印统计信息"""
        logger.info("\n" + "="*50)
        logger.info("📊 套利检测器统计")
        logger.info("="*50)
        logger.info(f"总扫描次数: {self.stats['total_checks']}")
        logger.info(f"发现机会: {self.stats['opportunities_found']}")
        logger.info(f"潜在总利润: ${self.stats['total_profit_potential']:.2f}")
        
        if self.stats['total_checks'] > 0:
            success_rate = self.stats['opportunities_found'] / self.stats['total_checks'] * 100
            logger.info(f"机会率: {success_rate:.2f}%")
        
        logger.info("="*50 + "\n")


async def main():
    """主函数"""
    # 配置RPC节点（需要替换为实际节点）
    RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
    
    # 初始化Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.isConnected():
        logger.error("❌ 无法连接到以太坊节点")
        return
    
    logger.info("✅ 连接到以太坊节点成功")
    logger.info(f"📦 当前区块: {w3.eth.block_number}")
    
    # 创建套利检测器
    detector = ArbitrageDetector(
        w3=w3,
        min_profit_usd=5.0,
        min_price_diff_pct=0.3
    )
    
    logger.info("🔍 开始扫描套利机会...")
    logger.info(f"监控交易对: {detector.watch_pairs}")
    
    try:
        while True:
            # 扫描套利机会
            opportunities = await detector.scan()
            
            if opportunities:
                logger.info(f"✅ 发现 {len(opportunities)} 个套利机会")
            
            # 等待下一次扫描
            await asyncio.sleep(10)  # 10秒扫描一次
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ 收到停止信号")
        detector.print_stats()


if __name__ == "__main__":
    asyncio.run(main())
