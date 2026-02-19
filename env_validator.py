#!/usr/bin/env python3
"""
Web3Million 系统环境验证与启动脚本
功能：
1. 全面检查环境依赖
2. 验证 API 连接
3. 检查配置文件
4. 启动系统进行实盘前验证
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import json

class EnvironmentValidator:
    """环境验证器"""
    
    def __init__(self):
        self.workspace = Path(__file__).parent
        self.issues = []
        self.warnings = []
        self.success = []
        
    def check_python_version(self):
        """检查 Python 版本"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.success.append(f"✅ Python 版本：{version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.issues.append(f"❌ Python 版本过低：{version.major}.{version.minor}.{version.micro} (需要 3.8+)")
            return False
    
    def check_node_version(self):
        """检查 Node.js 版本"""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
            self.success.append(f"✅ Node.js 版本：{result.stdout.strip()}")
            return True
        except Exception as e:
            self.warnings.append(f"⚠️ Node.js 未安装或不可用：{e}")
            return False
    
    def check_required_packages(self):
        """检查必需的 Python 包"""
        required_packages = {
            'web3': 'Web3 交互',
            'ccxt': '交易所 API',
            'pandas': '数据处理',
            'numpy': '数值计算',
            'matplotlib': '数据可视化',
            'seaborn': '统计图表',
            'plotly': '交互式图表',
            'aiohttp': '异步 HTTP',
            'ipfshttpclient': 'IPFS 存储',
            'pycryptodome': '加密库',
            'python-dotenv': '环境变量',
            'requests': 'HTTP 请求',
            'gitpython': 'Git 操作',
            'eth-account': '以太坊账户'
        }
        
        print("\n📦 检查 Python 依赖包...")
        all_installed = True
        
        for package, description in required_packages.items():
            try:
                __import__(package)
                self.success.append(f"✅ {package} ({description})")
            except ImportError:
                self.issues.append(f"❌ {package} 未安装 ({description})")
                all_installed = False
        
        return all_installed
    
    def check_env_file(self):
        """检查环境配置文件"""
        env_file = self.workspace / '.env'
        
        if not env_file.exists():
            self.issues.append("❌ .env 文件不存在")
            return False
        
        # 读取并检查关键配置
        env_vars = {}
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        
        # 检查 OKX 配置
        okx_configured = all([
            'OKX_API_KEY' in env_vars and env_vars['OKX_API_KEY'] != 'YOUR_BINANCE_API_KEY',
            'OKX_SECRET_KEY' in env_vars and env_vars['OKX_SECRET_KEY'] != 'YOUR_BINANCE_SECRET_KEY',
            'OKX_PASSPHRASE' in env_vars and env_vars['OKX_PASSPHRASE'] != 'YOUR_PASSPHRASE'
        ])
        
        if okx_configured:
            self.success.append("✅ OKX API 配置已设置")
        else:
            self.warnings.append("⚠️ OKX API 配置可能未正确设置（使用默认值或占位符）")
        
        # 检查 RPC 配置
        if 'ETHEREUM_RPC_URL' in env_vars:
            self.success.append("✅ Ethereum RPC URL 已配置")
        else:
            self.warnings.append("⚠️ Ethereum RPC URL 未配置")
        
        return True
    
    def check_module_structure(self):
        """检查项目模块结构"""
        required_dirs = [
            'ai_trading',
            'risk_management',
            'analytics',
            'defi_arbitrage',
            'nft_launchpad',
            'tokenomics',
            'project_management',
            'self_evolution'
        ]
        
        print("\n📁 检查项目结构...")
        all_exist = True
        
        for dir_name in required_dirs:
            dir_path = self.workspace / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.success.append(f"✅ 模块目录：{dir_name}")
            else:
                self.issues.append(f"❌ 模块目录缺失：{dir_name}")
                all_exist = False
        
        return all_exist
    
    def check_core_files(self):
        """检查核心文件"""
        core_files = [
            'main_controller.py',
            'run_web3million.py',
            'requirements.txt',
            '.env'
        ]
        
        print("\n📄 检查核心文件...")
        all_exist = True
        
        for file_name in core_files:
            file_path = self.workspace / file_name
            if file_path.exists():
                self.success.append(f"✅ 核心文件：{file_name}")
            else:
                self.issues.append(f"❌ 核心文件缺失：{file_name}")
                all_exist = False
        
        return all_exist
    
    def test_okx_connection(self):
        """测试 OKX API 连接"""
        print("\n🔌 测试 OKX API 连接...")
        
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            import ccxt
            exchange = ccxt.okx({
                'apiKey': os.getenv('OKX_API_KEY'),
                'secret': os.getenv('OKX_SECRET_KEY'),
                'password': os.getenv('OKX_PASSPHRASE'),
                'enableRateLimit': True,
            })
            
            # 测试获取市场数据
            markets = exchange.load_markets()
            self.success.append(f"✅ OKX API 连接成功 (加载 {len(markets)} 个交易对)")
            return True
            
        except Exception as e:
            self.warnings.append(f"⚠️ OKX API 连接测试失败：{str(e)}")
            return False
    
    def run(self):
        """运行完整验证"""
        print("="*60)
        print("🔍 Web3Million 系统环境验证")
        print("="*60)
        print(f"验证时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"工作目录：{self.workspace}")
        print("="*60)
        
        # 执行所有检查
        self.check_python_version()
        self.check_node_version()
        self.check_required_packages()
        self.check_env_file()
        self.check_module_structure()
        self.check_core_files()
        self.test_okx_connection()
        
        # 输出结果
        print("\n" + "="*60)
        print("📊 验证结果汇总")
        print("="*60)
        
        if self.success:
            print(f"\n✅ 成功项：{len(self.success)}")
            for item in self.success[:10]:  # 只显示前 10 项
                print(f"  {item}")
            if len(self.success) > 10:
                print(f"  ... 还有 {len(self.success) - 10} 项")
        
        if self.warnings:
            print(f"\n⚠️ 警告项：{len(self.warnings)}")
            for item in self.warnings:
                print(f"  {item}")
        
        if self.issues:
            print(f"\n❌ 问题项：{len(self.issues)}")
            for item in self.issues:
                print(f"  {item}")
        
        print("\n" + "="*60)
        
        # 判断是否可以启动
        if not self.issues:
            print("🎉 环境验证通过！系统可以启动。")
            return True
        else:
            print("🚨 存在环境问题，请先修复后再启动系统。")
            return False


def install_missing_dependencies():
    """安装缺失的依赖"""
    print("\n📦 正在安装/更新依赖包...")
    
    requirements_file = Path(__file__).parent / 'requirements.txt'
    if requirements_file.exists():
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '-r', 
                str(requirements_file), '--upgrade'
            ])
            print("✅ 依赖包安装完成！")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖包安装失败：{e}")
            return False
    else:
        print("❌ requirements.txt 文件不存在")
        return False


def start_validation_mode():
    """启动验证模式（不执行真实交易）"""
    print("\n" + "="*60)
    print("🚀 启动 Web3Million 系统 - 验证模式")
    print("="*60)
    
    try:
        # 添加工作目录到 Python 路径
        workspace = Path(__file__).parent
        sys.path.insert(0, str(workspace))
        
        # 设置环境变量
        from dotenv import load_dotenv
        load_dotenv()
        
        # 导入主控制器
        print("\n🔧 加载主控制器...")
        import main_controller
        
        # 创建控制器实例（验证模式）
        controller = main_controller.Web3MillionController(initial_capital=10.0)
        
        print("\n✅ 系统加载成功！")
        print(f"💰 初始资金：${controller.initial_capital}")
        print(f"🎯 目标资金：${controller.target}")
        print("\n📋 已加载模块:")
        print(f"  - AI 交易引擎：{'✅' if controller.trading_engine else '❌'}")
        print(f"  - 风险管理系统：{'✅' if controller.risk_manager else '❌'}")
        print(f"  - 数据分析仪表板：{'✅' if controller.analytics else '❌'}")
        print(f"  - DeFi 套利机器人：{'✅' if controller.arbitrage_bot else '❌'}")
        print(f"  - NFT 发行平台：{'✅' if controller.nft_launchpad else '❌'}")
        print(f"  - 代币发射系统：{'✅' if controller.token_system else '❌'}")
        print(f"  - 项目管理器：{'✅' if controller.project_tracker else '❌'}")
        
        print("\n" + "="*60)
        print("⚠️  验证模式：系统已加载但不执行真实交易")
        print("💡 提示：确认一切正常后，可以修改配置启动实盘模式")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 系统启动失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    # 设置控制台编码为 UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("\n" + "="*60)
    print("Web3Million - AI 驱动的百万美元增长计划")
    print("="*60)
    
    # 步骤 1: 环境验证
    validator = EnvironmentValidator()
    env_ok = validator.run()
    
    if not env_ok:
        print("\n❌ 环境验证失败")
        choice = input("\n是否尝试自动安装缺失的依赖？(y/n): ")
        if choice.lower() == 'y':
            install_missing_dependencies()
            # 重新验证
            validator = EnvironmentValidator()
            env_ok = validator.run()
        
        if not env_ok:
            print("\n🚨 请先手动修复环境问题后再启动系统")
            sys.exit(1)
    
    # 步骤 2: 启动验证模式
    print("\n准备启动系统验证...")
    choice = input("是否启动验证模式？(y/n): ")
    
    if choice.lower() == 'y':
        success = start_validation_mode()
        if success:
            print("\n✅ 系统验证完成！可以开始实盘前测试。")
        else:
            print("\n❌ 系统验证失败，请检查错误信息。")
            sys.exit(1)
    else:
        print("\n👋 已取消启动。")
    
    print("\n" + "="*60)
    print("验证流程结束")
    print("="*60)


if __name__ == "__main__":
    main()
