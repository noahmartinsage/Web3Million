"""
自我进化系统与Web3Million主系统的集成模块
"""

import asyncio
import threading
import time
from datetime import datetime
import json
import sys
import os
from typing import Dict, Any

# 添加路径以便导入其他模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from self_evolution.evolution_core import AutonomousAgent
from main_controller import Web3MillionController


class EvolutionaryIntegration:
    """进化系统集成器"""
    
    def __init__(self, web3_controller: Web3MillionController):
        self.web3_controller = web3_controller
        self.autonomous_agent = AutonomousAgent()
        self.integration_active = False
        self.evolutionary_feedback = []
        self.performance_monitor = None
        
    def initialize_integration(self):
        """初始化集成"""
        print("🔄 初始化自我进化系统集成...")
        
        # 初始化自主代理
        self.autonomous_agent.initialize()
        
        # 设置性能监控
        self.performance_monitor = self.PerformanceMonitor(self.web3_controller)
        
        self.integration_active = True
        print("✅ 自我进化系统集成初始化完成")
    
    async def run_evolutionary_cycle(self):
        """运行进化循环"""
        print("🔬 启动自我进化循环...")
        
        # 启动自主代理的生命周期
        agent_task = asyncio.create_task(self.autonomous_agent.run_lifecycle())
        
        cycle_count = 0
        while self.integration_active:
            try:
                # 收集性能数据
                performance_data = self.performance_monitor.get_current_performance()
                
                # 将性能数据反馈给进化系统
                feedback = self._generate_feedback(performance_data)
                self.evolutionary_feedback.append(feedback)
                
                # 基于进化系统的建议调整Web3Million参数
                self._apply_evolutionary_adjustments()
                
                cycle_count += 1
                
                if cycle_count % 5 == 0:
                    print(f"🌱 进化周期 {cycle_count}: 性能评分 {performance_data.get('roi', 0):.4f}, "
                          f"资产 ${self.web3_controller.current_capital:.2f}")
                
                # 每隔一段时间保存进化状态
                if cycle_count % 20 == 0:
                    self._save_evolution_state()
                
                await asyncio.sleep(2)  # 每2秒进行一次进化调整
                
            except Exception as e:
                print(f"❌ 进化循环错误: {e}")
                await asyncio.sleep(5)
    
    def _generate_feedback(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成反馈数据"""
        return {
            'timestamp': datetime.now(),
            'performance_data': performance_data,
            'capital_change': self.web3_controller.current_capital - self.web3_controller.initial_capital,
            'success_indicator': performance_data.get('roi', 0) > 0,
            'market_conditions': performance_data.get('market_condition', 'unknown')
        }
    
    def _apply_evolutionary_adjustments(self):
        """应用进化调整"""
        # 这里会根据自主代理的建议调整Web3Million的参数
        # 示例：调整风险参数
        if hasattr(self.web3_controller.risk_manager, 'max_position_size'):
            # 基于进化系统的学习结果调整风险参数
            new_risk_level = 0.2  # 这里应该是基于学习的实际计算
            self.web3_controller.risk_manager.max_position_size = new_risk_level
    
    def _save_evolution_state(self):
        """保存进化状态"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'capital': self.web3_controller.current_capital,
            'integration_active': self.integration_active,
            'feedback_count': len(self.evolutionary_feedback),
            'agent_status': self.autonomous_agent.adaptive_system.get_evolution_status()
        }
        
        with open('evolution_state.json', 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    class PerformanceMonitor:
        """性能监控器"""
        
        def __init__(self, controller: Web3MillionController):
            self.controller = controller
        
        def get_current_performance(self) -> Dict[str, Any]:
            """获取当前性能数据"""
            roi = (self.controller.current_capital - self.controller.initial_capital) / self.controller.initial_capital
            profit = self.controller.current_capital - self.controller.initial_capital
            
            return {
                'roi': roi,
                'profit': profit,
                'current_capital': self.controller.current_capital,
                'initial_capital': self.controller.initial_capital,
                'market_condition': 'volatile',  # 模拟市场条件
                'risk_score': 0.5,  # 模拟风险评分
                'trading_activity': self.controller.arbitrage_bot.executed_trades
            }


class EnhancedWeb3MillionController(Web3MillionController):
    """增强版Web3Million控制器，集成了自我进化能力"""
    
    def __init__(self, initial_capital: float = 10.0):
        super().__init__(initial_capital)
        self.evolution_integration = EvolutionaryIntegration(self)
        self.evolution_thread = None
        
    async def initialize_systems(self):
        """初始化增强系统"""
        print("🚀 初始化增强版Web3Million系统...")
        
        # 初始化原始系统
        await super().initialize_systems()
        
        # 初始化进化集成
        self.evolution_integration.initialize_integration()
        
        print("✅ 增强版Web3Million系统初始化完成")
    
    async def start_with_evolution(self):
        """启动带进化的系统"""
        print("🌟 启动具备自我进化的Web3Million系统...")
        
        await self.initialize_systems()
        
        self.running = True
        
        # 创建任务
        tasks = [
            asyncio.create_task(self.run_trading_cycle()),
            asyncio.create_task(self.run_arbitrage_scan()),
            asyncio.create_task(self.monitor_systems()),
            asyncio.create_task(self.run_nft_launchpad_business()),
            asyncio.create_task(self.run_tokenomics_growth()),
            asyncio.create_task(self.evolution_integration.run_evolutionary_cycle())  # 进化循环
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


async def main():
    """主函数"""
    print("🤖 启动具备自我进化的Web3Million系统...")
    
    # 创建增强版控制器
    controller = EnhancedWeb3MillionController(initial_capital=10.0)
    
    try:
        await controller.start_with_evolution()
    except KeyboardInterrupt:
        print("\n\n👋 具备自我进化的Web3Million系统已暂停")
        status = controller.get_status_report()
        print(f"📊 最终状态: ${status['current_capital']:.2f} / ${status['target_capital']}")
    except Exception as e:
        print(f"\n\n💥 系统致命错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main())