#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEV Bot - Mempool监听器 v1.0
实时监听以太坊mempool中的待处理交易
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from web3 import Web3
from web3.datastructures import AttributeDict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MempoolListener:
    """以太坊Mempool监听器"""
    
    def __init__(
        self,
        rpc_url: str,
        scan_interval: float = 0.1,
        max_pending_txs: int = 1000
    ):
        """
        初始化Mempool监听器
        
        Args:
            rpc_url: 以太坊RPC节点URL
            scan_interval: 扫描间隔（秒）
            max_pending_txs: 最大缓存待处理交易数
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.scan_interval = scan_interval
        self.max_pending_txs = max_pending_txs
        
        # 状态变量
        self.running = False
        self.pending_txs: Dict[str, AttributeDict] = {}
        self.processed_txs: set = set()
        self.stats = {
            'total_scanned': 0,
            'total_processed': 0,
            'total_filtered': 0,
            'start_time': None
        }
        
        # 目标合约（DEX路由器等）
        self.target_contracts = {
            'uniswap_v2_router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            'uniswap_v3_router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            'sushiswap_router': '0xd9e1cE17a264Dd44cAaC8B4b9D8B5675C6F0E8B0',
        }
        
        # 目标方法签名（用于识别交易类型）
        self.target_signatures = {
            'swapExactTokensForTokens': '0x38ed1739',
            'swapTokensForExactTokens': '0x8803dbee',
            'swapExactETHForTokens': '0x7ff36ab5',
            'swapTokensForExactETH': '0x18cbafe5',
            'swapExactTokensForETH': '0x791ac947',
            'swapETHForExactTokens': '0xfb3bdb41',
        }
        
    async def start(self):
        """启动监听器"""
        if not self.w3.isConnected():
            logger.error("❌ 无法连接到以太坊节点")
            return False
        
        logger.info("✅ 连接到以太坊节点成功")
        logger.info(f"📦 当前区块: {self.w3.eth.block_number}")
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        logger.info("👂 开始监听Mempool...")
        
        # 启动扫描任务
        await self._scan_loop()
        
        return True
    
    async def stop(self):
        """停止监听器"""
        self.running = False
        logger.info("🛑 Mempool监听器已停止")
        
        # 打印统计信息
        self._print_stats()
    
    async def _scan_loop(self):
        """扫描循环"""
        while self.running:
            try:
                # 获取待处理交易
                pending_block = self.w3.eth.get_block('pending', full_transactions=True)
                
                if pending_block and pending_block.transactions:
                    new_txs = 0
                    
                    for tx in pending_block.transactions:
                        tx_hash = tx['hash'].hex() if isinstance(tx['hash'], bytes) else tx['hash']
                        
                        # 跳过已处理的交易
                        if tx_hash in self.processed_txs:
                            continue
                        
                        # 处理新交易
                        await self._process_transaction(tx)
                        new_txs += 1
                        
                        # 限制缓存大小
                        if len(self.pending_txs) >= self.max_pending_txs:
                            self._cleanup_old_txs()
                    
                    if new_txs > 0:
                        self.stats['total_scanned'] += new_txs
                        logger.debug(f"📊 扫描到 {new_txs} 笔新交易")
                
                # 等待下一次扫描
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"❌ 扫描错误: {e}")
                await asyncio.sleep(1)
    
    async def _process_transaction(self, tx: AttributeDict):
        """处理单笔交易"""
        try:
            tx_hash = tx['hash'].hex() if isinstance(tx['hash'], bytes) else tx['hash']
            
            # 基本过滤
            if not self._is_interesting_transaction(tx):
                return
            
            # 提取关键信息
            tx_info = {
                'hash': tx_hash,
                'from': tx['from'],
                'to': tx['to'],
                'value': tx['value'],
                'gas_price': tx['gasPrice'],
                'gas': tx['gas'],
                'nonce': tx['nonce'],
                'input': tx['input'].hex() if isinstance(tx['input'], bytes) else tx['input'],
                'timestamp': datetime.now().isoformat()
            }
            
            # 检测交易类型
            tx_type = self._detect_transaction_type(tx_info)
            
            if tx_type:
                self.stats['total_filtered'] += 1
                
                # 打印发现
                gas_price_gwei = self.w3.from_wei(tx['gasPrice'], 'gwei')
                value_eth = self.w3.from_wei(tx['value'], 'ether')
                
                logger.info(
                    f"🎯 发现目标交易 [{tx_type}]\n"
                    f"   Hash: {tx_hash[:10]}...\n"
                    f"   From: {tx['from'][:10]}...\n"
                    f"   To: {tx['to'][:10] if tx['to'] else 'Contract Creation'}...\n"
                    f"   Value: {value_eth:.4f} ETH\n"
                    f"   Gas: {gas_price_gwei:.2f} Gwei\n"
                    f"   Method: {tx_info['input'][:10]}..."
                )
                
                # 缓存交易
                self.pending_txs[tx_hash] = tx_info
                
                # 标记为已处理
                self.processed_txs.add(tx_hash)
                
                # 触发MEV机会分析（后续实现）
                # await self._analyze_mev_opportunity(tx_info)
            
        except Exception as e:
            logger.error(f"❌ 处理交易失败: {e}")
    
    def _is_interesting_transaction(self, tx: AttributeDict) -> bool:
        """判断交易是否值得关注"""
        # 过滤条件
        
        # 1. 检查目标合约
        if tx['to'] and tx['to'].lower() in [addr.lower() for addr in self.target_contracts.values()]:
            return True
        
        # 2. 检查方法签名
        if tx['input'] and len(tx['input']) >= 10:
            method_sig = tx['input'][:10] if isinstance(tx['input'], str) else tx['input'][:10].hex()
            if method_sig in self.target_signatures.values():
                return True
        
        # 3. 大额转账
        value_eth = self.w3.from_wei(tx['value'], 'ether')
        if value_eth > 10:  # 大于10 ETH
            return True
        
        # 4. 高Gas交易（可能是有价值的交易）
        gas_price_gwei = self.w3.from_wei(tx['gasPrice'], 'gwei')
        if gas_price_gwei > 100:  # 高于100 Gwei
            return True
        
        return False
    
    def _detect_transaction_type(self, tx_info: Dict) -> Optional[str]:
        """检测交易类型"""
        input_data = tx_info['input']
        
        if not input_data or len(input_data) < 10:
            return None
        
        # 提取方法签名
        method_sig = input_data[:10]
        
        # 匹配交易类型
        for name, sig in self.target_signatures.items():
            if method_sig == sig:
                return name
        
        return None
    
    def _cleanup_old_txs(self):
        """清理旧交易缓存"""
        # 保留最近500笔
        if len(self.processed_txs) > 500:
            self.processed_txs = set(list(self.processed_txs)[-500:])
        
        if len(self.pending_txs) > 500:
            recent_hashes = list(self.pending_txs.keys())[-500:]
            self.pending_txs = {k: self.pending_txs[k] for k in recent_hashes}
    
    def _print_stats(self):
        """打印统计信息"""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        
        logger.info("\n" + "="*50)
        logger.info("📊 Mempool监听器统计")
        logger.info("="*50)
        logger.info(f"运行时长: {duration:.1f} 秒")
        logger.info(f"总扫描交易: {self.stats['total_scanned']}")
        logger.info(f"总处理交易: {self.stats['total_processed']}")
        logger.info(f"过滤后交易: {self.stats['total_filtered']}")
        
        if duration > 0:
            tps = self.stats['total_scanned'] / duration
            logger.info(f"平均TPS: {tps:.2f} tx/s")
        
        logger.info(f"缓存交易数: {len(self.pending_txs)}")
        logger.info("="*50 + "\n")


async def main():
    """主函数"""
    # 配置RPC节点（需要替换为实际节点）
    # 可以使用 Alchemy, Infura 或自建节点
    RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
    
    # 测试网配置
    # RPC_URL = "https://rpc.sepolia.org"
    
    listener = MempoolListener(
        rpc_url=RPC_URL,
        scan_interval=0.5,  # 0.5秒扫描一次
        max_pending_txs=1000
    )
    
    try:
        logger.info("🚀 启动MEV Bot - Mempool监听器")
        await listener.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ 收到停止信号")
        await listener.stop()
    except Exception as e:
        logger.error(f"❌ 运行错误: {e}")
        await listener.stop()


if __name__ == "__main__":
    asyncio.run(main())
