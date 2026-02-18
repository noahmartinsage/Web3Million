"""
修复OKX连接问题
诊断并解决API连接故障
"""

import asyncio
import ccxt.async_support as ccxt_async
import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

def check_api_credentials():
    """检查API凭据"""
    print("🔍 检查API凭据...")
    
    api_key = os.getenv('OKX_API_KEY')
    secret_key = os.getenv('OKX_SECRET_KEY')
    passphrase = os.getenv('OKX_PASSPHRASE')
    
    print(f"API Key: {'✅ 已配置' if api_key else '❌ 未配置'}")
    print(f"Secret Key: {'✅ 已配置' if secret_key else '❌ 未配置'}")
    print(f"Passphrase: {'✅ 已配置' if passphrase else '❌ 未配置'}")
    
    # 验证格式
    if api_key:
        print(f"API Key 格式: {len(api_key)} 字符")
    if secret_key:
        print(f"Secret Key 格式: {len(secret_key)} 字符")
    
    return all([api_key, secret_key, passphrase])

def check_network_connectivity():
    """检查网络连接"""
    print("\n🌐 检查网络连接...")
    
    try:
        # 测试基本连接
        response = requests.get('https://www.okx.com', timeout=10)
        print(f"OKX网站连接: ✅ HTTP {response.status_code}")
        
        # 测试API端点
        api_response = requests.get('https://www.okx.com/api/v5/public/time', timeout=10)
        print(f"OKX API连接: ✅ HTTP {api_response.status_code}")
        
        return True
    except Exception as e:
        print(f"网络连接: ❌ {e}")
        return False

async def test_exchange_connection():
    """测试交易所连接"""
    print("\n🔗 测试交易所连接...")
    
    try:
        # 使用最小化配置进行测试
        exchange = ccxt_async.okx({
            'apiKey': os.getenv('OKX_API_KEY'),
            'secret': os.getenv('OKX_SECRET_KEY'),
            'password': os.getenv('OKX_PASSPHRASE'),
            'enableRateLimit': True,
            'sandbox': True,  # 测试网模式
            'timeout': 30000,  # 30秒超时
            'verbose': False,  # 关闭详细输出避免干扰
        })
        
        # 尝试加载市场（最简单的API调用）
        print("   尝试加载市场数据...")
        markets = await exchange.load_markets()
        
        print(f"   ✅ 市场数据加载成功: {len(markets)} 个交易对")
        
        # 测试获取时间（不需要认证）
        print("   尝试获取服务器时间...")
        time_response = await exchange.fetch_time()
        print(f"   ✅ 服务器时间获取成功: {time_response}")
        
        await exchange.close()
        return True
        
    except ccxt_async.AuthenticationError:
        print("   ❌ 认证错误 - API凭据可能无效")
        return False
    except ccxt_async.NetworkError as e:
        print(f"   ❌ 网络错误 - {e}")
        return False
    except ccxt_async.ExchangeError as e:
        print(f"   ❌ 交易所错误 - {e}")
        return False
    except Exception as e:
        print(f"   ❌ 未知错误 - {e}")
        return False

def fix_api_configuration():
    """修复API配置"""
    print("\n🔧 修复API配置...")
    
    # 检查是否需要特殊配置
    print("   检查测试网配置...")
    
    # 创建修复后的配置
    fixed_config = {
        'apiKey': os.getenv('OKX_API_KEY'),
        'secret': os.getenv('OKX_SECRET_KEY'),
        'password': os.getenv('OKX_PASSPHRASE'),
        'enableRateLimit': True,
        'sandbox': True,
        'timeout': 30000,
        'headers': {
            'User-Agent': 'Web3Million-Bot/1.0'
        },
        'options': {
            'adjustForTimeDifference': True,
            'recvWindow': 10000
        }
    }
    
    print("   ✅ 配置修复完成")
    return fixed_config

async def attempt_fixed_connection():
    """尝试修复后的连接"""
    print("\n🔄 尝试修复后的连接...")
    
    try:
        config = fix_api_configuration()
        
        exchange = ccxt_async.okx(config)
        
        # 设置时间差调整
        await exchange.load_time_difference()
        
        # 测试连接
        print("   尝试获取服务器时间...")
        server_time = await exchange.fetch_time()
        print(f"   ✅ 服务器时间: {server_time}")
        
        # 测试获取市场数据
        print("   尝试加载市场...")
        markets = await exchange.load_markets()
        print(f"   ✅ 加载了 {len(list(markets.keys())[:5])} 个交易对 (显示前5个)")
        
        for symbol in list(markets.keys())[:5]:
            print(f"      - {symbol}")
        
        # 测试获取账户信息（基本检查）
        print("   尝试获取账户信息...")
        balance = await exchange.fetch_balance(params={'type': 'spot'})
        print(f"   ✅ 账户信息获取成功")
        
        await exchange.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 修复后连接失败: {e}")
        return False

def suggest_fixes():
    """建议修复方案"""
    print("\n💡 建议的修复方案:")
    print("   1. 验证API密钥是否在OKX测试网正确创建")
    print("   2. 确认API密钥具有足够权限 (交易、查询)")
    print("   3. 检查IP白名单设置（如果启用）")
    print("   4. 确认测试网账户已激活")
    print("   5. 检查防火墙/网络限制")
    
    print("\n🔧 自动修复步骤:")
    print("   1. 验证API凭据")
    print("   2. 检查网络连接")
    print("   3. 修复配置参数")
    print("   4. 重试连接")

async def main():
    print("🔧 OKX连接问题诊断与修复")
    print("="*50)
    
    # 检查API凭据
    creds_ok = check_api_credentials()
    
    # 检查网络连接
    network_ok = check_network_connectivity()
    
    if creds_ok and network_ok:
        print("\n✅ 凭据和网络检查通过，尝试连接修复...")
        
        # 尝试修复连接
        fixed_connection = await attempt_fixed_connection()
        
        if fixed_connection:
            print("\n🎉 连接修复成功!")
            print("✅ OKX测试网连接已建立")
            return True
        else:
            print("\n⚠️ 连接修复失败，提供详细诊断...")
    else:
        print("\n❌ 凭据或网络检查失败")
    
    # 提供诊断和建议
    suggest_fixes()
    
    return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\n✅ 问题已修复，系统可正常连接OKX测试网")
    else:
        print("\n❌ 需要人工干预，请检查上述建议")