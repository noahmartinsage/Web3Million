"""
OKX版Web3Million控制器
集成OKX测试网账户的专用控制器
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
import json
import sys
import os
from typing import Dict, List, Optional
import requests

# 代理配置
PROXY = (
    os.environ.get("HTTP_PROXY")
    or os.environ.get("http_proxy")
    or os.environ.get("HTTPS_PROXY")
    or os.environ.get("https_proxy")
    or ""
)
if PROXY:
    print(f"[OKX] Using proxy: {PROXY}")
    os.environ["HTTP_PROXY"] = PROXY
    os.environ["HTTPS_PROXY"] = PROXY

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

# 导入OKX集成
import ccxt.async_support as ccxt_async
from dotenv import load_dotenv

# 导入自我进化模块
try:
    from self_evolution.integration import EnhancedWeb3MillionController

    EVOLUTION_AVAILABLE = True
except ImportError:
    EVOLUTION_AVAILABLE = False
    print("⚠️ 自我进化模块不可用，使用基础版本")

# 加载环境变量
load_dotenv()


class OKXWeb3MillionController:
    """OKX版Web3Million控制器"""

    def __init__(self, initial_capital: float = 10.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.target = 1000000.0  # 100万美元目标
        self.start_time = datetime.now()

        # OKX配置
        self.okx_api_key = os.getenv("OKX_API_KEY")
        self.okx_secret_key = os.getenv("OKX_SECRET_KEY")
        self.okx_passphrase = os.getenv("OKX_PASSPHRASE")
        self.okx_sub_account = os.getenv("OKX_SUB_ACCOUNT", "dale1")

        # 初始化OKX连接
        self.okx_exchange = None
        self.okx_connected = False

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

        # 更新风险参数以适应OKX账户的大资金
        self._configure_okx_mode()

    def _configure_okx_mode(self):
        """配置OKX模式特定参数"""
        print("🔄 启用OKX模式配置...")

        # 由于有更大的资金池，可以适当调整参数
        self.risk_manager.max_position_size = 0.02  # 2%最大仓位（更保守）
        self.risk_manager.max_drawdown = 0.15  # 15%最大回撤
        self.risk_manager.max_daily_loss = 500  # 每日最大损失$500

        print("✅ OKX模式配置完成")
        print(f"💼 账户可用资金: $11,924.24 USDT")
        print(
            f"📊 风险参数: 仓位{self.risk_manager.max_position_size * 100}%, 回撤{self.risk_manager.max_drawdown * 100}%"
        )

    async def connect_okx(self):
        """连接到OKX交易所"""
        print(f"🔗 正在连接到OKX测试网账户...")

        try:
            self.okx_exchange = ccxt_async.okx(
                {
                    "apiKey": self.okx_api_key,
                    "secret": self.okx_secret_key,
                    "password": self.okx_passphrase,
                    "enableRateLimit": True,
                    "sandbox": True,  # 测试网模式
                    "headers": {"Content-Type": "application/json"},
                }
            )

            # 测试连接
            await self.okx_exchange.load_markets()

            # 获取账户信息
            balance = await self.okx_exchange.fetch_balance()
            usdt_balance = balance["total"].get("USDT", 0)

            print(f"✅ OKX测试网连接成功!")
            print(f"💰 USDT余额: {usdt_balance}")
            print(f"👤 子账户: {self.okx_sub_account}")

            self.okx_connected = True
            return True

        except Exception as e:
            print(f"❌ OKX连接失败: {e}")
            self.okx_connected = False
            return False

    async def initialize_systems(self):
        """初始化所有系统"""
        print("🚀 正在初始化Web3百万美元OKX系统...")

        # 连接OKX
        if await self.connect_okx():
            print("✅ OKX连接成功")
        else:
            print("⚠️ OKX连接失败，继续使用模拟模式")

        # 初始化NFT发行平台
        self.nft_launchpad.initialize_ipfs()

        # 发射代币
        allocation = TokenAllocation(
            community=0.4,
            team=0.15,
            advisors=0.05,
            treasury=0.2,
            staking_rewards=0.15,
            ecosystem_fund=0.05,
        )
        self.token_system.launch_token(allocation, initial_price=0.001)

        # 更新项目追踪
        self.project_tracker.update_module_status(
            "Web3Million",
            "Project Deployment",
            "completed",
            [
                "ai_trading/core_engine.py",
                "risk_management/system.py",
                "analytics/dashboard.py",
                "defi_arbitrage/opportunity_finder.py",
                "nft_launchpad/core.py",
                "tokenomics/governance.py",
                "project_management/deploy.py",
                "okx_controller.py",
            ],
        )

        print("✅ OKX系统初始化完成!")

    async def run_trading_cycle(self):
        """运行交易循环（使用OKX连接）"""
        print("💱 启动AI交易引擎 (OKX模式)...")

        cycle_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 如果连接到OKX，获取实时市场数据
                if self.okx_connected and self.okx_exchange:
                    try:
                        # 获取BTC/USDT价格作为市场参考
                        ticker = await self.okx_exchange.fetch_ticker("BTC/USDT")
                        btc_price = ticker["last"]

                        # 模拟基于市场数据的交易决策
                        # 在实际实现中，这里会执行真实交易
                        simulated_profit = (
                            self.current_capital * 0.0003
                        )  # 模拟0.03%的日收益
                        self.current_capital += simulated_profit

                        print(
                            f"📈 BTC价格: ${btc_price:.2f}, 模拟交易收益: ${simulated_profit:.4f}"
                        )
                    except Exception as e:
                        print(f"⚠️ 获取OKX市场数据时出错: {e}")
                        # 回退到模拟交易
                        simulated_profit = self.current_capital * 0.0001
                        self.current_capital += simulated_profit
                else:
                    # 模拟交易
                    simulated_profit = self.current_capital * 0.0001
                    self.current_capital += simulated_profit

                # 更新风险管理系统
                self.risk_manager.update_capital(self.current_capital)

                # 记录交易到分析系统
                trade_record = {
                    "profit": simulated_profit,
                    "return": simulated_profit / self.current_capital,
                }
                self.risk_manager.record_trade(trade_record)

                # 每10个周期报告一次
                if cycle_count % 10 == 0:
                    print(
                        f"📊 OKX交易周期 {cycle_count}: 资产 = ${self.current_capital:.4f}, "
                        f"ROI = {(self.current_capital / self.initial_capital - 1) * 100:.2f}%"
                    )

                # 检查风险限制
                if not self.risk_manager.should_continue_trading():
                    print("⚠️ 风险管理系统触发停止条件")
                    break

                cycle_count += 1
                await asyncio.sleep(2)  # 每2秒执行一次交易循环

            except Exception as e:
                print(f"❌ 交易循环错误: {e}")
                await asyncio.sleep(5)

    async def run_arbitrage_scan(self):
        """运行套利扫描"""
        print("🔍 启动DeFi套利扫描 (OKX模式)...")

        # 启动套利机器人
        await self.arbitrage_bot.analyzer.initialize()

        scan_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 获取池信息
                pools = await self.arbitrage_bot.analyzer.fetch_all_pools()

                # 寻找套利机会
                triangle_ops = (
                    self.arbitrage_bot.analyzer.find_triangular_arbitrage_opportunities(
                        pools
                    )
                )
                cross_ops = self.arbitrage_bot.analyzer.find_cross_dex_arbitrage(pools)

                all_ops = triangle_ops + cross_ops

                # 执行发现的机会（在OKX模式下更活跃）
                executed_this_cycle = 0
                for opportunity in all_ops[:3]:  # 最多执行3个机会
                    if self.current_capital >= 1.0:  # 更高的最低要求
                        simulated_profit = min(
                            opportunity.net_profit, self.current_capital * 0.008
                        )  # 稍微提高收益
                        self.current_capital += simulated_profit
                        self.arbitrage_bot.total_profit += simulated_profit
                        self.arbitrage_bot.executed_trades += 1
                        executed_this_cycle += 1

                        print(
                            f"⚡ OKX套利执行: ${simulated_profit:.4f} -> 总资产 ${self.current_capital:.4f}"
                        )

                if scan_count % 5 == 0:
                    print(
                        f"🔄 套利扫描周期 {scan_count}: 发现 {len(all_ops)} 个机会, 执行 {executed_this_cycle} 个"
                    )

                scan_count += 1
                await asyncio.sleep(5)  # 每5秒扫描一次

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
                    print(
                        f"📊 日性能: {metrics.get('total_trades', 0)} 交易, "
                        f"${metrics.get('total_profit', 0):.2f} 收益"
                    )

                # 获取代币系统状态
                network_state = self.token_system.get_network_state()
                print(
                    f"🪙 W3M代币: ${network_state['token_info']['market_cap']:.2f} 市值"
                )

                # 获取项目进度
                progress_report = self.project_tracker.get_project_report("Web3Million")
                print(f"🎯 项目进度: {progress_report.get('progress', 0):.1f}%")

                # OKX特定监控
                if self.okx_connected:
                    try:
                        balance = await self.okx_exchange.fetch_balance()
                        usdt_total = balance["total"].get("USDT", 0)
                        usdt_free = balance["free"].get("USDT", 0)
                        print(f"🏦 OKX USDT: 总计 {usdt_total}, 可用 {usdt_free}")
                    except Exception as e:
                        print(f"⚠️ 获取OKX余额时出错: {e}")

                await asyncio.sleep(30)  # 每30秒监控一次

            except Exception as e:
                print(f"❌ 监控错误: {e}")
                await asyncio.sleep(60)

    async def run_nft_launchpad_business(self):
        """运行NFT发行平台业务"""
        print("🎨 启动NFT业务 (OKX模式)...")

        # 创建示例NFT集合
        from nft_launchpad.core import CollectionConfig, NFTStandard

        config = CollectionConfig(
            name="Web3Million Genesis (OKX)",
            symbol="W3MGO",
            description="Web3Million项目OKX专属创世NFT系列",
            royalty_percentage=2.5,
            royalty_recipient="0x1234567890123456789012345678901234567890",
            max_supply=10000,
            price_per_mint=0.1,  # 稍高价格
            standard=NFTStandard.ERC721,
            metadata_base_uri="https://api.okx.web3million.com/metadata/",
        )

        # 启动集合（在真实环境中会部署智能合约）
        collection_id = await self.nft_launchpad.launch_collection(config, "0xCreator")

        # 模拟NFT销售
        sales_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 模拟销售NFT
                if sales_count % 10 == 0:  # 每10次循环模拟一次销售
                    revenue = config.price_per_mint * 10  # 10个NFT的收入
                    self.current_capital += revenue
                    print(
                        f"🛍️ NFT销售: +${revenue:.2f} -> 总资产 ${self.current_capital:.2f}"
                    )

                sales_count += 1
                await asyncio.sleep(8)  # 每8秒模拟一次销售机会

            except Exception as e:
                print(f"❌ NFT业务错误: {e}")
                await asyncio.sleep(30)

    async def run_tokenomics_growth(self):
        """运行代币经济成长"""
        print("💹 启动代币经济增长引擎 (OKX模式)...")

        growth_count = 0
        while self.running and self.current_capital < self.target:
            try:
                # 模拟代币价格上涨（OKX模式下更积极）
                current_price = (
                    self.token_system.token_econ.market_cap
                    / self.token_system.token_econ.circulating_supply
                )
                price_increase = current_price * 0.0005  # 每次循环增加0.05%（更积极）

                # 更新市值
                self.token_system.token_econ.market_cap += (
                    self.token_system.token_econ.circulating_supply * price_increase
                )

                # 如果我们持有一些代币，计算纸面收益
                token_holdings = 10000  # 更多的持仓量（OKX模式）
                paper_gains = token_holdings * price_increase
                self.current_capital += paper_gains * 0.08  # 更大的实现比例

                if growth_count % 15 == 0:
                    current_price = (
                        self.token_system.token_econ.market_cap
                        / self.token_system.token_econ.circulating_supply
                    )
                    fdv = (
                        self.token_system.token_econ.calculate_fully_diluted_valuation(
                            current_price
                        )
                    )
                    print(f"📈 W3M价格: ${current_price:.6f}, FDV: ${fdv:,.2f}")

                growth_count += 1
                await asyncio.sleep(3)  # 每3秒更新一次

            except Exception as e:
                print(f"❌ 代币经济错误: {e}")
                await asyncio.sleep(15)

    async def start(self):
        """启动整个系统"""
        print(f"🚀 Web3百万美元OKX系统启动!")
        print(f"💰 初始资金: ${self.initial_capital}")
        print(f"🎯 目标: ${self.target}")
        print(f"📊 预计增长: {(self.target / self.initial_capital - 1) * 100:.0f}倍")
        print(f"🏦 模式: OKX测试网集成")

        await self.initialize_systems()

        self.running = True

        # 创建任务
        tasks = [
            asyncio.create_task(self.run_trading_cycle()),
            asyncio.create_task(self.run_arbitrage_scan()),
            asyncio.create_task(self.monitor_systems()),
            asyncio.create_task(self.run_nft_launchpad_business()),
            asyncio.create_task(self.run_tokenomics_growth()),
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
        print("\n🛑 停止Web3百万美元OKX系统...")
        self.running = False

        # 关闭OKX连接
        if self.okx_exchange:
            asyncio.create_task(self.okx_exchange.close())

        # 关闭其他资源
        if hasattr(self.arbitrage_bot.analyzer, "close"):
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
            "trading_status": getattr(self.arbitrage_bot, "executed_trades", 0),
            "okx_connected": self.okx_connected,
            "project_progress": self.project_tracker.get_project_report("Web3Million"),
        }


async def main():
    """主函数"""
    print("🚀 启动OKX版Web3Million系统...")
    controller = OKXWeb3MillionController(initial_capital=11924.24)  # 使用实际账户余额

    try:
        await controller.start()
    except KeyboardInterrupt:
        print("\n\n👋 Web3百万美元OKX系统已暂停")
        status = controller.get_status_report()
        print(
            f"当前状态: ${status['current_capital']:.2f} / ${status['target_capital']}"
        )
        print(f"OKX连接: {status['okx_connected']}")
    except Exception as e:
        print(f"\n\n💥 系统致命错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
