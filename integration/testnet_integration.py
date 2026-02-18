"""
测试网集成模块
将测试网环境与Web3Million系统集成
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from web3 import Web3
import ccxt.async_support as ccxt_async
from eth_account import Account

from testnet_config import TESTNET_CONFIG, WALLET_CONFIG_TEMPLATE, RISK_MANAGEMENT_CONFIG
from ai_trading.core_engine import AITradingEngine
from risk_management.system import AdvancedRiskManager
from defi_arbitrage.opportunity_finder import ArbitrageBot


class TestnetIntegration:
    """测试网集成器"""
    
    def __init__(self):
        self.network_configs = TESTNET_CONFIG
        self.wallet_config = WALLET_CONFIG_TEMPLATE.copy()
        self.risk_config = RISK_MANAGEMENT_CONFIG
        self.web3_instances = {}
        self.exchange_instances = {}
        self.connected = False
        
    def configure_wallet(self, private_key: str = None, mnemonic: str = None, network: str = 'ethereum_sepolia'):
        """配置钱包"""
        if private_key:
            self.wallet_config['private_key'] = private_key
            account = Account.from_key(private_key)
            self.wallet_config['address'] = account.address
        elif mnemonic:
            self.wallet_config['mnemonic'] = mnemonic
            # 从助记词派生地址（简化）
            account = Account.from_mnemonic(mnemonic, account_path="m/44'/60'/0'/0/0")
            self.wallet_config['address'] = account.address
        
        self.wallet_config['network'] = network
        print(f"✅ 钱包已配置: {self.wallet_config['address'][:10]}... 地址")
        
    def connect_network(self, network_name: str):
        """连接到指定网络"""
        if network_name not in self.network_configs:
            raise ValueError(f"不支持的网络: {network_name}")
        
        config = self.network_configs[network_name]
        rpc_url = config['rpc_url']
        
        # 替换占位符（如果有的话）
        if 'YOUR_INFURA_PROJECT_ID' in rpc_url:
            infura_id = os.getenv('INFURA_PROJECT_ID')
            if infura_id:
                rpc_url = rpc_url.replace('YOUR_INFURA_PROJECT_ID', infura_id)
            else:
                print(f"⚠️ 未找到Infura项目ID，使用默认RPC URL")
        
        try:
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            if web3.is_connected():
                self.web3_instances[network_name] = web3
                print(f"✅ 已连接到 {network_name} 网络")
                print(f"🔗 RPC: {rpc_url}")
                print(f"💳 区块高度: {web3.eth.block_number}")
                return True
            else:
                print(f"❌ 无法连接到 {network_name} 网络")
                return False
        except Exception as e:
            print(f"❌ 连接 {network_name} 网络时出错: {e}")
            return False
    
    async def connect_exchange_testnet(self, exchange_name: str, api_key: str = None, secret_key: str = None):
        """连接到测试网交易所"""
        if exchange_name not in ['binance_testnet', 'bybit_testnet']:
            raise ValueError(f"不支持的测试网交易所: {exchange_name}")
        
        config = {
            'binance_testnet': {
                'id': 'binance',
                'apiKey': api_key or os.getenv('BINANCE_TESTNET_API_KEY', ''),
                'secret': secret_key or os.getenv('BINANCE_TESTNET_SECRET_KEY', ''),
                'urls': {'api': 'https://testnet.binance.vision'},
            },
            'bybit_testnet': {
                'id': 'bybit',
                'apiKey': api_key or os.getenv('BYBIT_TESTNET_API_KEY', ''),
                'secret': secret_key or os.getenv('BYBIT_TESTNET_SECRET_KEY', ''),
                'sandbox': True,
            }
        }
        
        try:
            exchange_config = config[exchange_name]
            exchange = ccxt_async.Exchange(exchange_config)
            
            # 测试连接
            await exchange.fetch_balance()
            self.exchange_instances[exchange_name] = exchange
            print(f"✅ 已连接到 {exchange_name}")
            return True
            
        except Exception as e:
            print(f"❌ 连接 {exchange_name} 时出错: {e}")
            return False
    
    def get_balance(self, network: str = None, token: str = 'ETH') -> Optional[float]:
        """获取钱包余额"""
        if not network:
            network = self.wallet_config['network']
        
        if network not in self.web3_instances:
            print(f"❌ 未连接到 {network} 网络")
            return None
        
        web3 = self.web3_instances[network]
        address = self.wallet_config['address']
        
        if token.upper() == 'ETH':
            balance_wei = web3.eth.get_balance(address)
            balance_eth = web3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        else:
            # 对于ERC20代币，需要代币合约地址
            print(f"⚠️ 暂不支持查询 {token} 余额（需提供代币合约地址）")
            return None
    
    async def validate_test_environment(self) -> Dict[str, Any]:
        """验证测试环境"""
        validation_results = {
            'network_connection': False,
            'wallet_configured': bool(self.wallet_config['address']),
            'balance_check': None,
            'exchange_connection': len(self.exchange_instances) > 0,
            'risk_management': True  # 默认通过
        }
        
        # 检查网络连接
        network = self.wallet_config['network']
        if network in self.web3_instances:
            validation_results['network_connection'] = True
            
            # 检查余额
            balance = self.get_balance(network)
            if balance is not None:
                validation_results['balance_check'] = balance
                print(f"💰 钱包余额: {balance} {self.network_configs[network]['currency']}")
        
        # 总体验证结果
        all_good = all([
            validation_results['network_connection'],
            validation_results['wallet_configured'],
            validation_results['balance_check'] is not None and validation_results['balance_check'] > 0,
            validation_results['exchange_connection']
        ])
        
        validation_results['overall_status'] = all_good
        return validation_results
    
    async def prepare_for_live_trading(self, initial_capital: float = 10.0):
        """准备实盘交易（在测试环境中模拟）"""
        print("🔧 准备在测试环境中进行交易...")
        
        # 验证环境
        validation = await self.validate_test_environment()
        if not validation['overall_status']:
            print("❌ 测试环境验证失败")
            for key, value in validation.items():
                print(f"  {key}: {value}")
            return False
        
        print("✅ 测试环境验证通过，准备启动交易系统")
        
        # 初始化交易引擎（使用测试配置）
        trading_engine = AITradingEngine(initial_capital=initial_capital)
        risk_manager = AdvancedRiskManager(initial_capital=initial_capital)
        arbitrage_bot = ArbitrageBot(initial_capital=initial_capital)
        
        # 应用测试网特定配置
        risk_manager.max_position_size = self.risk_config['max_position_size']
        risk_manager.max_drawdown = self.risk_config['max_drawdown']
        
        print(f"📊 交易系统已配置:")
        print(f"   - 初始资金: ${initial_capital}")
        print(f"   - 最大仓位: {risk_manager.max_position_size*100}%")
        print(f"   - 最大回撤: {risk_manager.max_drawdown*100}%")
        print(f"   - 网络: {self.wallet_config['network']}")
        
        return {
            'trading_engine': trading_engine,
            'risk_manager': risk_manager,
            'arbitrage_bot': arbitrage_bot,
            'validation': validation
        }
    
    def get_faucet_info(self, network_name: str = None):
        """获取水龙头信息"""
        if not network_name:
            network_name = self.wallet_config['network']
        
        faucets = []
        if network_name in ['ethereum_sepolia', 'ethereum_goerli']:
            faucets = [
                'https://sepoliafaucet.com',
                'https://faucet.sepolia.dev',
                'https://sepolia-faucet.pk910.de'
            ]
        elif network_name == 'bsc_testnet':
            faucets = ['https://testnet.binance.org/faucet-smart']
        elif network_name == 'polygon_mumbai':
            faucets = ['https://faucet.polygon.technology']
        
        return faucets


async def main():
    """主函数 - 演示测试网集成"""
    print("🧪 测试网集成系统启动")
    
    # 创建集成实例
    integration = TestnetIntegration()
    
    # 连接到Sepolia测试网
    print("\n🔗 连接到Ethereum Sepolia测试网...")
    success = integration.connect_network('ethereum_sepolia')
    
    if success:
        print("\n🔐 配置测试钱包...")
        # 注意：在实际使用中，私钥应从安全来源获取
        # integration.configure_wallet(private_key="YOUR_PRIVATE_KEY_HERE", network='ethereum_sepolia')
        
        # 演示如何获取水龙头信息
        faucets = integration.get_faucet_info('ethereum_sepolia')
        print(f"\n💧 Sepolia测试网水龙头:")
        for faucet in faucets:
            print(f"   - {faucet}")
        
        # 连接到测试网交易所
        print(f"\n💱 连接到Binance测试网...")
        await integration.connect_exchange_testnet('binance_testnet')
    
    print(f"\n✅ 测试网集成准备就绪")
    print(f"📋 当前状态:")
    print(f"   - 网络连接: {'✅' if 'ethereum_sepolia' in integration.web3_instances else '❌'}")
    print(f"   - 钱包配置: {'✅' if integration.wallet_config['address'] else '❌'}")
    print(f"   - 交易所连接: {'✅' if integration.exchange_instances else '❌'}")


if __name__ == "__main__":
    asyncio.run(main())