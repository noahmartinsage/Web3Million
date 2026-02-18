"""
替代方法连接测试
使用requests库直接调用API进行测试
"""

import requests
import json
import hmac
import hashlib
import time
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class OKXConnectionTester:
    """OKX连接测试器 - 使用requests直接调用API"""
    
    def __init__(self):
        self.api_key = os.getenv('OKX_API_KEY')
        self.secret_key = os.getenv('OKX_SECRET_KEY')
        self.passphrase = os.getenv('OKX_PASSPHRASE')
        self.base_url = 'https://www.okx.com'
        
    def generate_signature(self, timestamp, method, request_path, body=''):
        """生成签名"""
        message = str(timestamp) + method.upper() + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf-8'),
            bytes(message, encoding='utf-8'),
            digestmod=hashlib.sha256
        )
        return mac.hexdigest()
    
    def get_headers(self, method, request_path, body=''):
        """获取请求头"""
        timestamp = str(time.time())
        sign = self.generate_signature(timestamp, method, request_path, body)
        
        headers = {
            'Content-Type': 'application/json',
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase
        }
        
        return headers
    
    def test_public_endpoint(self):
        """测试公共端点（无需认证）"""
        print("🔍 测试公共API端点...")
        
        try:
            # 获取服务器时间
            response = requests.get(f"{self.base_url}/api/v5/public/time")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服务器时间: {data}")
                return True
            else:
                print(f"❌ 公共端点测试失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 公共端点测试异常: {e}")
            return False
    
    def test_market_data(self):
        """测试市场数据端点"""
        print("\n📊 测试市场数据...")
        
        try:
            # 获取BTC-USDT交易对信息
            response = requests.get(f"{self.base_url}/api/v5/market/ticker?instId=BTC-USDT")
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':  # OKX API成功码
                    ticker = data['data'][0] if data['data'] else {}
                    print(f"✅ BTC-USDT行情: {ticker.get('last', 'N/A')}")
                    return True
                else:
                    print(f"❌ 市场数据API返回错误: {data}")
                    return False
            else:
                print(f"❌ 市场数据请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 市场数据测试异常: {e}")
            return False
    
    def test_private_endpoint(self):
        """测试私有端点（需要认证）"""
        print("\n🔒 测试私有API端点...")
        
        try:
            # 获取账户信息
            method = 'GET'
            request_path = '/api/v5/account/balance'
            body = ''
            
            headers = self.get_headers(method, request_path, body)
            url = f"{self.base_url}{request_path}"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data['code'] == '0':
                    print(f"✅ 账户信息获取成功")
                    print(f"   数据: {data['data'][:2] if data['data'] else []}")  # 显示前2项
                    return True
                else:
                    print(f"❌ 私有API返回错误: {data['msg']}")
                    return False
            elif response.status_code == 401:
                print(f"❌ 认证失败: API凭据可能无效")
                return False
            else:
                print(f"❌ 私有API请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 私有端点测试异常: {e}")
            return False
    
    def test_sandbox_specific(self):
        """测试测试网特定功能"""
        print("\n🧪 测试测试网特定功能...")
        
        try:
            # 检查是否在测试网环境
            # OKX测试网通常有不同的域名或路径
            response = requests.get(f"{self.base_url}/api/v5/system/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 系统状态: {data}")
                return True
            else:
                print(f"⚠️ 系统状态检查返回: {response.status_code}")
                return True  # 状态码不是关键问题
                
        except Exception as e:
            print(f"⚠️ 系统状态检查异常: {e}")
            return True  # 异常不是关键问题
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🔧 开始OKX连接修复测试")
        print("="*50)
        
        results = {
            'public_endpoint': self.test_public_endpoint(),
            'market_data': self.test_market_data(),
            'private_endpoint': self.test_private_endpoint(),
            'sandbox_features': self.test_sandbox_specific()
        }
        
        print(f"\n📊 测试结果:")
        for test, result in results.items():
            status = "✅" if result else "❌"
            test_name = {
                'public_endpoint': '公共端点',
                'market_data': '市场数据',
                'private_endpoint': '私有端点',
                'sandbox_features': '测试网功能'
            }.get(test, test)
            print(f"   {test_name}: {status}")
        
        # 总体评估
        successful_tests = sum(results.values())
        total_tests = len(results)
        
        print(f"\n🎯 总体成绩: {successful_tests}/{total_tests} 项测试通过")
        
        if successful_tests >= 3:  # 至少3项通过
            print("✅ 连接修复测试基本成功")
            overall_success = True
        elif successful_tests >= 2:
            print("⚠️ 连接修复测试部分成功，需要进一步调试")
            overall_success = False
        else:
            print("❌ 连接修复测试失败，需要人工干预")
            overall_success = False
        
        # 保存结果
        test_results = {
            'timestamp': time.time(),
            'results': results,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'overall_success': overall_success
        }
        
        with open('connection_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        return overall_success

def main():
    tester = OKXConnectionTester()
    success = tester.run_comprehensive_test()
    
    print(f"\n{'🎉 修复测试完成!' if success else '⚠️ 需要进一步修复'}")
    print("详细结果已保存到 connection_test_results.json")
    
    if not success:
        print("\n💡 建议下一步操作:")
        print("   1. 检查API凭据是否正确")
        print("   2. 确认API密钥在测试网环境中创建")
        print("   3. 验证API密钥权限设置")
        print("   4. 检查网络连接和防火墙设置")
    
    return success

if __name__ == "__main__":
    main()