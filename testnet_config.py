"""
测试网配置文件
用于连接各种测试网络进行安全验证
"""

# 测试网配置
TESTNET_CONFIG = {
    # Ethereum Sepolia Testnet
    'ethereum_sepolia': {
        'rpc_url': 'https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID',
        'chain_id': 11155111,
        'currency': 'ETH',
        'explorer_url': 'https://sepolia.etherscan.io'
    },
    
    # Binance Smart Chain Testnet
    'bsc_testnet': {
        'rpc_url': 'https://data-seed-prebsc-1-s1.binance.org:8545',
        'chain_id': 97,
        'currency': 'BNB',
        'explorer_url': 'https://testnet.bscscan.com'
    },
    
    # Polygon Mumbai Testnet
    'polygon_mumbai': {
        'rpc_url': 'https://rpc-mumbai.maticvigil.com',
        'chain_id': 80001,
        'currency': 'MATIC',
        'explorer_url': 'https://mumbai.polygonscan.com'
    }
}

# 测试代币水龙头配置
FAUCET_CONFIG = {
    'ethereum_sepolia': [
        'https://sepoliafaucet.com',
        'https://faucet.sepolia.dev',
        'https://sepolia-faucet.pk910.de'
    ],
    'bsc_testnet': [
        'https://testnet.binance.org/faucet-smart'
    ],
    'polygon_mumbai': [
        'https://faucet.polygon.technology'
    ]
}

# 测试交易所API配置（模拟）
TEST_EXCHANGES = {
    'binance_testnet': {
        'api_url': 'https://testnet.binance.vision/api',
        'api_key': 'YOUR_TEST_API_KEY',
        'secret_key': 'YOUR_TEST_SECRET_KEY',
        'demo_mode': True
    },
    'bybit_testnet': {
        'api_url': 'https://api-testnet.bybit.com',
        'api_key': 'YOUR_TEST_API_KEY',
        'secret_key': 'YOUR_TEST_SECRET_KEY',
        'demo_mode': True
    }
}

# 钱包配置模板
WALLET_CONFIG_TEMPLATE = {
    'wallet_type': 'metamask',  # metamask, walletconnect, coinbase, etc
    'private_key': '',  # 将从环境变量或安全存储中加载
    'mnemonic': '',     # 将从环境变量或安全存储中加载
    'address': '',      # 钱包地址
    'network': 'ethereum_sepolia',  # 默认网络
    'max_gas_price': 100,  # Gwei
    'slippage_tolerance': 0.5,  # 0.5%
    'transaction_timeout': 300,  # 5分钟
    'risk_limits': {
        'max_transaction_value': 100,  # 最大交易金额（测试币）
        'max_daily_volume': 500,       # 每日最大交易量（测试币）
        'max_loss_per_day': 50         # 每日最大损失（测试币）
    }
}

# 风险管理配置
RISK_MANAGEMENT_CONFIG = {
    'max_position_size': 0.1,  # 最大仓位10%
    'stop_loss_percentage': 0.05,  # 5%止损
    'take_profit_percentage': 0.15,  # 15%止盈
    'max_drawdown': 0.15,  # 最大回撤15%
    'max_leverage': 1.0,   # 无杠杆
    'emergency_stop': True  # 紧急停止开关
}

# 通知配置
NOTIFICATION_CONFIG = {
    'telegram': {
        'enabled': True,
        'chat_id': 'YOUR_TELEGRAM_CHAT_ID',
        'bot_token': 'YOUR_BOT_TOKEN'
    },
    'email': {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': 'your_email@gmail.com',
        'sender_password': 'your_app_password'
    },
    'critical_only': True  # 只发送关键警报
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'file_path': './logs/testnet_operations.log',
    'max_size_mb': 100,
    'backup_count': 5,
    'sensitive_data_masking': True  # 敏感数据脱敏
}

# 交易对配置（测试）
TRADING_PAIRS = [
    {
        'symbol': 'ETH/USDT',
        'base_asset': 'ETH',
        'quote_asset': 'USDT',
        'min_order_size': 0.001,
        'max_order_size': 10,
        'grid_levels': 10,
        'grid_spacing': 0.02  # 2%
    },
    {
        'symbol': 'BNB/USDT',
        'base_asset': 'BNB',
        'quote_asset': 'USDT',
        'min_order_size': 0.01,
        'max_order_size': 100,
        'grid_levels': 10,
        'grid_spacing': 0.02
    }
]

# 智能合约配置（测试）
SMART_CONTRACTS = {
    'router_address': '0x...',  # 测试网路由器地址
    'factory_address': '0x...',  # 测试网工厂地址
    'weth_address': '0x...',    # 测试网WETH地址
    'usdt_address': '0x...',    # 测试网USDT地址
    'usdc_address': '0x...'     # 测试网USDC地址
}

def get_network_config(network_name):
    """获取网络配置"""
    return TESTNET_CONFIG.get(network_name)

def get_faucet_urls(network_name):
    """获取水龙头URL"""
    return FAUCET_CONFIG.get(network_name, [])

if __name__ == "__main__":
    print("测试网配置文件已准备就绪")
    print("支持的网络:", list(TESTNET_CONFIG.keys()))
    print("请在使用前填写您的API密钥和钱包信息")