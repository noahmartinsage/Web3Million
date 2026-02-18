"""
测试网版Web3Million控制器
用于在测试环境中运行和验证系统
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
import json
import sys
import os
from typing import Dict, List, Optional

# 导入我们创建的所有模块
import sys
import os
sys.path.append(os.getcwd())

from ai_trading.core_engine import AITradingEngine
from risk_management.system import AdvancedRiskManager
from analytics.dashboard import AnalyticsEngine, AlertSystem
from defi_arbitrage.opportunity_finder import ArbitrageBot
from nft_launchpad.core import NFTLaunchpad
from tokenomics.governance import TokenLaunchSystem, TokenAllocation
from project_management.deploy import ProjectTracker

# 导入测试网集成
from integration.testnet_integration import TestnetIntegration

# 导入自我进化模块
try:
    from self_evolution.integration import EnhancedWeb3MillionController
    EVOLUTION_AVAILABLE = True
except ImportError:
    EVOLUTION_AVAILABLE = False
    print("⚠️ 自我进化模块不可用，使用基础版本")


class TestnetWeb3MillionController:
    """测试网版Web3Million控制器"""
    
    def __init__(self, initial_capital: float = 10.0, test_mode: bool = True):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.target = 1000000.0  # 100万美元目标
        self.start_time = datetime.now()
        self.test_mode = test_mode
        
        # 初始化测试网集成
        self.testnet_integration = TestnetIntegration()
        
        # 初始化各模块
        self.trading_engine = AITradingEngine(initial_capital=initial_capital)
        self.risk_manager = AdvancedRiskManager(initial_capital=initial_capital)
        self.analytics = AnalyticsEngine()
        self.alert_system = AlertSystem(self.analytics)
        self.arbitrage_bot = ArbitrageBot(initial_capital=initial_capital)
        self.nft_launchpad = NFTLaunchpad()
        self.token_system = TokenLaunchSystem("Web3Million", "W3M", 1000000000)
        self.project_tracker = ProjectTracker()
        
        # 控制标志
        self.running = False
        self.modules = {}
        
        # 测试模式特定配置
        if self.test_mode:
            self._configure_test_mode()
    
    def _configure_test_mode(self):
        """配置测试模式"""
        print("🧪 启用测试模式配置...")
        
        # 降低风险参数
        self.risk_manager.max_position_size = 0.05  # 降低到5%
        self.risk_manager.max_drawdown = 0.10      # 降低到10%
        
        # 设置测试模式特定参数
        print("✅ 测试模式配置完成")
    
    async def initialize_systems(self):
        """初始化所有系统"""
        print("🚀 正在初始化Web3百万美元测试系统...")
        
        # 初始化测试网连接
        print("🔗 连接到测试网环境...")
        self.testnet_integration.connect_network('ethereum_sepolia')
        
        # 获取水龙头信息
        faucets = self.testnet_integration.get_faucet_info('ethereum_sepolia')
        print(f"💧 Sepolia测试网水龙头可用: {len(faucets)} 个")
        
        # 初始化NFT发行平台
        self.nft_launchpad.initialize_ipfs()
        
        # 发射代币
        allocation = TokenAllocation(
            community=0.4,
            team=0.15,
            advisors=0.05,
            treasury=0.2,
            staking_rewards=0.15,
            ecosystem_fund=0.05
        )
        self.token_system.launch_token(allocation, initial_price=0.001)
        
        # 更新项目追踪
        self.project_tracker.update_module_status("Web3Million", "Project Deployment", "completed", [
            "ai_trading/core_engine.py",
            "risk_management/system.py", 
            "analytics/dashboard.py",
            "defi_arbitrage/opportunity_finder.py",
            "nft_launchpad/core.py",
            "tokenomics/governance.py",
            "project_management/deploy.py",
            "testnet_controller.py"
        ])
        
        print("✅ 测试系统初始化完成!")
    
    async def run_trading_cycle(self):
        """运行交易循环"""
        print("💱 启动AI交易引擎 (测试模式)...")
        
        cycle_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 模拟交易执行（测试模式下更保守）
                simulated_profit = self.current_capital * 0.0005  # 模拟0.05%的日收益（更保守）
                self.current_capital += simulated_profit
                
                # 更新风险管理系统
                self.risk_manager.update_capital(self.current_capital)
                
                # 记录交易到分析系统
                trade_record = {
                    'profit': simulated_profit,
                    'return': 0.0005
                }
                self.risk_manager.record_trade(trade_record)
                
                # 每10个周期报告一次
                if cycle_count % 10 == 0:
                    print(f"📈 测试交易周期 {cycle_count}: 资产 = ${self.current_capital:.4f}, "
                          f"ROI = {(self.current_capital/self.initial_capital-1)*100:.2f}%")
                
                # 检查风险限制
                if not self.risk_manager.should_continue_trading():
                    print("⚠️ 风险管理系统触发停止条件")
                    break
                
                cycle_count += 1
                await asyncio.sleep(1)  # 模拟实际交易间隔
                
            except Exception as e:
                print(f"❌ 交易循环错误: {e}")
                await asyncio.sleep(5)
    
    async def run_arbitrage_scan(self):
        """运行套利扫描"""
        print("🔍 启动DeFi套利扫描 (测试模式)...")
        
        # 启动套利机器人
        await self.arbitrage_bot.analyzer.initialize()
        
        scan_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 获取池信息
                pools = await self.arbitrage_bot.analyzer.fetch_all_pools()
                
                # 寻找套利机会
                triangle_ops = self.arbitrage_bot.analyzer.find_triangular_arbitrage_opportunities(pools)
                cross_ops = self.arbitrage_bot.analyzer.find_cross_dex_arbitrage(pools)
                
                all_ops = triangle_ops + cross_ops
                
                # 执行发现的机会（测试模式下更保守）
                for opportunity in all_ops[:1]:  # 只执行第1个机会（更保守）
                    if self.current_capital >= 0.5:  # 更低的最低要求
                        simulated_profit = min(opportunity.net_profit, self.current_capital * 0.005)  # 更小的收益
                        self.current_capital += simulated_profit
                        self.arbitrage_bot.total_profit += simulated_profit
                        self.arbitrage_bot.executed_trades += 1
                        
                        print(f"⚡ 测试套利执行: ${simulated_profit:.4f} -> 总资产 ${self.current_capital:.4f}")
                
                if scan_count % 5 == 0:
                    print(f"🔄 扫描周期 {scan_count}: 发现 {len(all_ops)} 个套利机会")
                
                scan_count += 1
                await asyncio.sleep(3)  # 每3秒扫描一次
                
            except Exception as e:
                print(f"❌ 套利扫描错误: {e}")
                await asyncio.sleep(10)
    
    async def monitor_systems(self):
        """监控系统状态"""
        print("👁️ 启动系统监控...")
        
        while self.running and self.current_capital < self.target:
            try:
                # 获取实时仪表板数据
                dashboard_data = self.analytics.get_real_time_dashboard()
                
                # 检查警报
                alerts = self.alert_system.check_alerts()
                if alerts:
                    for alert in alerts:
                        print(f"🚨 警报 [{alert['severity']}]: {alert['message']}")
                
                # 获取性能指标
                metrics = self.analytics.get_performance_metrics(days=1)
                if metrics:
                    print(f"📊 日性能: {metrics.get('total_trades', 0)} 交易, "
                          f"${metrics.get('total_profit', 0):.2f} 收益")
                
                # 获取代币系统状态
                network_state = self.token_system.get_network_state()
                print(f"🪙 W3M代币: ${network_state['token_info']['market_cap']:.2f} 市值")
                
                # 获取项目进度
                progress_report = self.project_tracker.get_project_report("Web3Million")
                print(f"🎯 项目进度: {progress_report.get('progress', 0):.1f}%")
                
                # 测试网特定监控
                if self.test_mode:
                    validation = await self.testnet_integration.validate_test_environment()
                    print(f"🧪 测试环境状态: {'✅' if validation.get('overall_status', False) else '⚠️'}")
                
                await asyncio.sleep(30)  # 每30秒监控一次
                
            except Exception as e:
                print(f"❌ 监控错误: {e}")
                await asyncio.sleep(60)
    
    async def run_nft_launchpad_business(self):
        """运行NFT发行平台业务"""
        print("🎨 启动NFT业务 (测试模式)...")
        
        # 创建示例NFT集合
        from nft_launchpad.core import CollectionConfig, NFTStandard
        
        config = CollectionConfig(
            name="Web3Million Genesis (Test)",
            symbol="W3MGT",
            description="Web3Million项目测试网创世NFT系列",
            royalty_percentage=2.5,
            royalty_recipient="0x1234567890123456789012345678901234567890",
            max_supply=1000,
            price_per_mint=0.01,  # 更低的价格用于测试
            standard=NFTStandard.ERC721,
            metadata_base_uri="https://api.test.web3million.com/metadata/"
        )
        
        # 启动集合（在真实环境中会部署智能合约）
        collection_id = await self.nft_launchpad.launch_collection(config, "0xCreator")
        
        # 模拟NFT销售
        sales_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 模拟销售NFT
                if sales_count % 20 == 0:  # 每20次循环模拟一次销售（更保守）
                    revenue = config.price_per_mint * 5  # 5个NFT的收入
                    self.current_capital += revenue
                    print(f"🛍️ NFT销售: +${revenue:.2f} -> 总资产 ${self.current_capital:.2f}")
                
                sales_count += 1
                await asyncio.sleep(10)  # 每10秒模拟一次销售机会
                
            except Exception as e:
                print(f"❌ NFT业务错误: {e}")
                await asyncio.sleep(30)
    
    async def run_tokenomics_growth(self):
        """运行代币经济成长"""
        print("💹 启动代币经济增长引擎 (测试模式)...")
        
        growth_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 模拟代币价格上涨（测试模式下更平缓）
                current_price = self.token_system.token_econ.market_cap / self.token_system.token_econ.circulating_supply
                price_increase = current_price * 0.0002  # 每次循环增加0.02%（更保守）
                
                # 更新市值
                self.token_system.token_econ.market_cap += self.token_system.token_econ.circulating_supply * price_increase
                
                # 如果我们持有一些代币，计算纸面收益
                token_holdings = 5000  # 较少的持仓量（测试模式）
                paper_gains = token_holdings * price_increase
                self.current_capital += paper_gains * 0.05  # 更小的实现比例
                
                if growth_count % 20 == 0:
                    current_price = self.token_system.token_econ.market_cap / self.token_system.token_econ.circulating_supply
                    fdv = self.token_system.token_econ.calculate_fully_diluted_valuation(current_price)
                    print(f"📈 W3M价格: ${current_price:.6f}, FDV: ${fdv:,.2f}")
                
                growth_count += 1
                await asyncio.sleep(5)  # 每5秒更新一次
                
            except Exception as e:
                print(f"❌ 代币经济错误: {e}")
                await asyncio.sleep(15)
    
    async def start(self):
        """启动整个系统"""
        print(f"🧪 Web3百万美元测试系统启动!")
        print(f"💰 初始资金: ${self.initial_capital}")
        print(f"🎯 目标: ${self.target}")
        print(f"📊 预计增长: {(self.target/self.initial_capital-1)*100:.0f}倍")
        print(f"🛡️  模式: 测试网安全模式")
        
        await self.initialize_systems()
        
        self.running = True
        
        # 创建任务
        tasks = [
            asyncio.create_task(self.run_trading_cycle()),
            asyncio.create_task(self.run_arbitrage_scan()),
            asyncio.create_task(self.monitor_systems()),
            asyncio.create_task(self.run_nft_launchpad_business()),
            asyncio.create_task(self.run_tokenomics_growth())
        ]
        
        try:
            # 等待所有任务完成（或达到目标）
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n🛑 用户中断")
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止系统"""
        print("\n🛑 停止Web3百万美元测试系统...")
        self.running = False
        
        # 关闭资源
        if hasattr(self.arbitrage_bot.analyzer, 'close'):
            asyncio.create_task(self.arbitrage_bot.analyzer.close())
    
    def get_status_report(self) -> Dict:
        """获取系统状态报告"""
        time_elapsed = datetime.now() - self.start_time
        
        return {
            "current_capital": self.current_capital,
            "initial_capital": self.initial_capital,
            "target_capital": self.target,
            "progress_percentage": (self.current_capital / self.target) * 100,
            "time_elapsed": str(time_elapsed),
            "systems_running": self.running,
            "trading_status": getattr(self.arbitrage_bot, 'executed_trades', 0),
            "test_mode": self.test_mode,
            "project_progress": self.project_tracker.get_project_report("Web3Million")
        }


async def main():
    """主函数"""
    print("🧪 启动测试网版Web3Million系统...")
    controller = TestnetWeb3MillionController(initial_capital=10.0, test_mode=True)
    
    try:
        await controller.start()
    except KeyboardInterrupt:
        print("\n\n👋 Web3百万美元测试系统已暂停")
        status = controller.get_status_report()
        print(f"当前状态: ${status['current_capital']:.2f} / ${status['target_capital']}")
        print(f"测试模式: {status['test_mode']}")
    except Exception as e:
        print(f"\n\n💥 系统致命错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())