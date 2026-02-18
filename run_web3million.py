#!/usr/bin/env python3
"""
Web3Million 启动脚本
用于启动AI驱动的百万美元增长计划
"""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """安装必需的依赖包"""
    required_packages = [
        "web3",
        "ccxt", 
        "pandas",
        "numpy", 
        "matplotlib",
        "seaborn",
        "plotly",
        "aiohttp",
        "ipfshttpclient",
        "pycryptodome",
        "python-dotenv",
        "requests",
        "gitpython",
        "eth-account"
    ]
    
    print("📦 正在安装必需的依赖包...")
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError:
            print(f"⚠️ {package} 安装失败")

def main():
    """主函数"""
    print("🚀 Web3Million - AI驱动的Web3百万富翁计划")
    print("="*50)
    
    # 安装依赖
    install_dependencies()
    
    # 添加当前目录到Python路径
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        # 尝试导入我们的模块
        print("\n🔧 正在加载系统模块...")
        
        # 由于模块较多，我们直接启动主控制器
        print("🎯 启动Web3百万美元增长计划...")
        
        # 运行主控制器
        import main_controller
        controller = main_controller.Web3MillionController(initial_capital=10.0)
        
        print(f"💰 系统已启动! 初始资金: ${controller.initial_capital}")
        print("📈 AI交易引擎、DeFi套利、NFT发行和代币经济系统已激活")
        print("⚠️  按 Ctrl+C 停止系统")
        
        # 启动主循环
        import asyncio
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(controller.start())
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("正在尝试安装缺失的包...")
        install_dependencies()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Web3百万美元计划已暂停")
        if 'controller' in locals():
            status = controller.get_status_report()
            print(f"📊 最终状态: ${status['current_capital']:.2f} / ${status['target_capital']}")
    
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()