"""
代币经济学模型与治理系统
包含代币发行、质押、治理等功能
"""

import asyncio
import hashlib
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime, timedelta
import math
from decimal import Decimal


class TokenType(Enum):
    GOVERNANCE = "governance"
    UTILITY = "utility"
    REWARD = "reward"
    LP = "lp_token"


@dataclass
class TokenAllocation:
    community: float  # 社区分配百分比
    team: float  # 团队分配百分比
    advisors: float  # 顾问分配百分比
    treasury: float  # 基金会/金库分配百分比
    staking_rewards: float  # 质押奖励分配百分比
    ecosystem_fund: float  # 生态基金分配百分比


@dataclass
class VestingSchedule:
    cliff_months: int  # 锁定期（月）
    vesting_months: int  # 解锁期（月）
    start_date: datetime  # 开始日期


@dataclass
class Proposal:
    id: str
    title: str
    description: str
    proposer: str
    votes_for: int
    votes_against: int
    start_time: datetime
    end_time: datetime
    executed: bool
    quorum: float  # 最低投票门槛


class TokenEconomics:
    """代币经济学核心类"""
    
    def __init__(self, token_name: str, token_symbol: str, total_supply: int):
        self.token_name = token_name
        self.token_symbol = token_symbol
        self.total_supply = total_supply
        self.circulating_supply = 0
        self.market_cap = 0
        self.token_holders = {}
        self.staking_pool = 0
        self.treasury_balance = 0
        self.emission_schedule = []
        self.price_history = []
        
    def allocate_tokens(self, allocation: TokenAllocation):
        """分配代币"""
        allocations = {
            'community': int(self.total_supply * allocation.community),
            'team': int(self.total_supply * allocation.team),
            'advisors': int(self.total_supply * allocation.advisors),
            'treasury': int(self.total_supply * allocation.treasury),
            'staking_rewards': int(self.total_supply * allocation.staking_rewards),
            'ecosystem_fund': int(self.total_supply * allocation.ecosystem_fund)
        }
        
        print(f"💰 {self.token_name} 代币分配:")
        for category, amount in allocations.items():
            percentage = (amount / self.total_supply) * 100
            print(f"  {category}: {amount:,} ({percentage:.2f}%)")
        
        return allocations
    
    def calculate_apr(self, staked_amount: float, reward_rate: float) -> float:
        """计算年化收益率"""
        # 简化的APR计算
        apr = (reward_rate * 365 * 24 * 60 * 60) / staked_amount * 100
        return min(apr, 1000)  # 限制最大APR为1000%
    
    def calculate_token_price(self, market_cap: float, circulating_supply: float) -> float:
        """计算代币价格"""
        if circulating_supply == 0:
            return 0
        return market_cap / circulating_supply
    
    def calculate_fully_diluted_valuation(self, current_price: float) -> float:
        """计算完全稀释估值"""
        return current_price * self.total_supply


class StakingRewards:
    """质押奖励系统"""
    
    def __init__(self, token_economics: TokenEconomics):
        self.token_econ = token_economics
        self.stakers = {}
        self.reward_rate = 0.05  # 每秒奖励率（简化）
        self.total_staked = 0
        self.reward_pool = 0
        self.last_update = datetime.now()
    
    def stake_tokens(self, user_address: str, amount: float):
        """质押代币"""
        if user_address not in self.stakers:
            self.stakers[user_address] = {
                'amount': 0,
                'rewards': 0,
                'last_claim': datetime.now()
            }
        
        self.stakers[user_address]['amount'] += amount
        self.total_staked += amount
        self.token_econ.token_holders[user_address] -= amount  # 从持有者账户扣除
        
        print(f"🔒 {user_address} 质押了 {amount} {self.token_econ.token_symbol}")
    
    def unstake_tokens(self, user_address: str, amount: float):
        """解除质押"""
        if user_address not in self.stakers:
            print("❌ 用户未质押任何代币")
            return False
        
        staker = self.stakers[user_address]
        if amount > staker['amount']:
            print("❌ 解除质押数量超过质押数量")
            return False
        
        # 先领取奖励
        self.claim_rewards(user_address)
        
        staker['amount'] -= amount
        self.total_staked -= amount
        self.token_econ.token_holders[user_address] += amount  # 返回到持有者账户
        
        print(f"🔓 {user_address} 解除质押 {amount} {self.token_econ.token_symbol}")
        return True
    
    def claim_rewards(self, user_address: str) -> float:
        """领取奖励"""
        if user_address not in self.stakers:
            return 0
        
        staker = self.stakers[user_address]
        time_passed = (datetime.now() - staker['last_claim']).total_seconds()
        
        # 计算奖励（简化计算）
        rewards = staker['amount'] * self.reward_rate * time_passed
        staker['rewards'] += rewards
        staker['last_claim'] = datetime.now()
        
        # 添加到用户余额
        if user_address not in self.token_econ.token_holders:
            self.token_econ.token_holders[user_address] = 0
        self.token_econ.token_holders[user_address] += rewards
        
        print(f"🎁 {user_address} 领取了 {rewards:.4f} {self.token_econ.token_symbol} 奖励")
        return rewards
    
    def calculate_pending_rewards(self, user_address: str) -> float:
        """计算待领取奖励"""
        if user_address not in self.stakers:
            return 0
        
        staker = self.stakers[user_address]
        time_passed = (datetime.now() - staker['last_claim']).total_seconds()
        return staker['amount'] * self.reward_rate * time_passed


class GovernanceSystem:
    """治理系统"""
    
    def __init__(self, token_economics: TokenEconomics):
        self.token_econ = token_economics
        self.proposals = {}
        self.votes = {}
        self.voting_power_cache = {}
        self.quorum_threshold = 0.05  # 5%的代币持有者参与才能通过提案
    
    def create_proposal(self, title: str, description: str, proposer: str) -> str:
        """创建提案"""
        proposal_id = str(uuid.uuid4())
        
        proposal = Proposal(
            id=proposal_id,
            title=title,
            description=description,
            proposer=proposer,
            votes_for=0,
            votes_against=0,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=7),  # 7天投票期
            executed=False,
            quorum=self.quorum_threshold
        )
        
        self.proposals[proposal_id] = proposal
        print(f"📜 新提案 #{proposal_id}: {title}")
        return proposal_id
    
    def vote_on_proposal(self, proposal_id: str, voter: str, vote_for: bool) -> bool:
        """对提案投票"""
        if proposal_id not in self.proposals:
            print("❌ 提案不存在")
            return False
        
        proposal = self.proposals[proposal_id]
        if datetime.now() > proposal.end_time:
            print("❌ 投票已结束")
            return False
        
        # 检查投票权（基于质押数量）
        voting_power = self._calculate_voting_power(voter)
        if voting_power <= 0:
            print("❌ 没有足够的投票权")
            return False
        
        vote_key = f"{proposal_id}:{voter}"
        if vote_key in self.votes:
            print("❌ 已投过票")
            return False
        
        # 记录投票
        self.votes[vote_key] = {
            'proposal_id': proposal_id,
            'voter': voter,
            'vote_for': vote_for,
            'voting_power': voting_power,
            'timestamp': datetime.now()
        }
        
        if vote_for:
            proposal.votes_for += voting_power
        else:
            proposal.votes_against += voting_power
        
        print(f"🗳️ {voter} 对提案 #{proposal_id} {'赞成' if vote_for else '反对'} (投票权: {voting_power})")
        return True
    
    def execute_proposal(self, proposal_id: str) -> bool:
        """执行提案"""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        if proposal.executed:
            print("❌ 提案已被执行")
            return False
        
        if datetime.now() < proposal.end_time:
            print("❌ 投票尚未结束")
            return False
        
        # 检查是否达到法定人数
        total_votes = proposal.votes_for + proposal.votes_against
        quorum_met = total_votes >= (self.token_econ.total_supply * proposal.quorum)
        
        if not quorum_met:
            print("❌ 未达到法定投票人数")
            return False
        
        # 检查是否获得多数支持
        if proposal.votes_for > proposal.votes_against:
            proposal.executed = True
            print(f"✅ 提案 #{proposal_id} 已通过并执行")
            return True
        else:
            print(f"❌ 提案 #{proposal_id} 未通过")
            return False
    
    def _calculate_voting_power(self, address: str) -> float:
        """计算投票权"""
        # 投票权基于质押数量
        if address in self.token_econ.stakers:
            return self.token_econ.stakers[address]['amount']
        return 0
    
    def get_proposal_status(self, proposal_id: str) -> Dict:
        """获取提案状态"""
        if proposal_id not in self.proposals:
            return {}
        
        proposal = self.proposals[proposal_id]
        total_votes = proposal.votes_for + proposal.votes_against
        
        return {
            'id': proposal.id,
            'title': proposal.title,
            'votes_for': proposal.votes_for,
            'votes_against': proposal.votes_against,
            'total_votes': total_votes,
            'quorum_met': total_votes >= (self.token_econ.total_supply * proposal.quorum),
            'passed': proposal.votes_for > proposal.votes_against,
            'executed': proposal.executed,
            'time_remaining': (proposal.end_time - datetime.now()).total_seconds() if datetime.now() < proposal.end_time else 0
        }


class YieldFarming:
    """收益农业系统"""
    
    def __init__(self, token_economics: TokenEconomics):
        self.token_econ = token_economics
        self.farms = {}
        self.user_positions = {}
    
    def create_farm(self, farm_id: str, reward_token: str, staking_token: str, 
                   total_reward: float, duration_days: int):
        """创建农场"""
        self.farms[farm_id] = {
            'reward_token': reward_token,
            'staking_token': staking_token,
            'total_reward': total_reward,
            'duration': timedelta(days=duration_days),
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(days=duration_days),
            'total_staked': 0,
            'reward_per_second': total_reward / (duration_days * 24 * 60 * 60)
        }
        print(f"🌾 新农场已创建: {farm_id}")
    
    def deposit(self, farm_id: str, user: str, amount: float):
        """存入代币"""
        if farm_id not in self.farms:
            print("❌ 农场不存在")
            return
        
        farm = self.farms[farm_id]
        if datetime.now() > farm['end_time']:
            print("❌ 农场已结束")
            return
        
        if user not in self.user_positions:
            self.user_positions[user] = {}
        
        if farm_id not in self.user_positions[user]:
            self.user_positions[user][farm_id] = {
                'amount': 0,
                'reward_debt': 0
            }
        
        # 领取之前奖励
        self.claim_rewards(farm_id, user)
        
        # 存入
        self.user_positions[user][farm_id]['amount'] += amount
        farm['total_staked'] += amount
        
        print(f"📥 {user} 存入 {amount} {farm['staking_token']} 到农场 {farm_id}")
    
    def claim_rewards(self, farm_id: str, user: str) -> float:
        """领取农场奖励"""
        if user not in self.user_positions or farm_id not in self.user_positions[user]:
            return 0
        
        farm = self.farms[farm_id]
        position = self.user_positions[user][farm_id]
        
        # 计算应得奖励
        if farm['total_staked'] > 0:
            reward = (position['amount'] * farm['reward_per_second'] * 
                     (datetime.now() - farm['start_time']).total_seconds())
            position['reward_debt'] = reward
            
            # 添加到用户余额
            if user not in self.token_econ.token_holders:
                self.token_econ.token_holders[user] = 0
            self.token_econ.token_holders[user] += reward
            
            print(f"🏆 {user} 从农场 {farm_id} 领取 {reward:.4f} {farm['reward_token']} 奖励")
            return reward
        
        return 0


class TokenLaunchSystem:
    """代币发射系统"""
    
    def __init__(self, token_name: str, token_symbol: str, total_supply: int):
        self.token_econ = TokenEconomics(token_name, token_symbol, total_supply)
        self.staking = StakingRewards(self.token_econ)
        self.governance = GovernanceSystem(self.token_econ)
        self.yield_farming = YieldFarming(self.token_econ)
        self.launched = False
    
    def launch_token(self, allocation: TokenAllocation, initial_price: float = 0.01):
        """发射代币"""
        if self.launched:
            print("❌ 代币已发射")
            return
        
        # 分配代币
        allocated = self.token_econ.allocate_tokens(allocation)
        
        # 设置初始流通供应量（例如，先释放20%）
        initial_circulating = int(self.token_econ.total_supply * 0.2)
        self.token_econ.circulating_supply = initial_circulating
        
        # 分配给早期参与者
        community_amount = allocated['community']
        for i in range(100):  # 假设有100个早期支持者
            addr = f"0xearly_supporter_{i}"
            amount = community_amount // 100
            self.token_econ.token_holders[addr] = amount
        
        # 设置初始市值
        self.token_econ.market_cap = initial_circulating * initial_price
        
        self.launched = True
        print(f"🚀 {self.token_econ.token_name} ({self.token_econ.token_symbol}) 代币已发射!")
        print(f"📈 初始价格: ${initial_price}")
        print(f"市值: ${self.token_econ.market_cap:,.2f}")
    
    def get_network_state(self) -> Dict:
        """获取网络状态"""
        return {
            'token_info': {
                'name': self.token_econ.token_name,
                'symbol': self.token_econ.token_symbol,
                'total_supply': self.token_econ.total_supply,
                'circulating_supply': self.token_econ.circulating_supply,
                'market_cap': self.token_econ.market_cap
            },
            'staking_info': {
                'total_staked': self.staking.total_staked,
                'staker_count': len(self.staking.stakers)
            },
            'governance_info': {
                'proposal_count': len(self.governance.proposals),
                'voter_count': len(set(v['voter'] for v in self.governance.votes.values()))
            }
        }


# 使用示例
if __name__ == "__main__":
    # 创建代币发射系统
    launch_system = TokenLaunchSystem("Web3Million", "W3M", 1000000000)  # 10亿代币
    
    # 定义代币分配
    allocation = TokenAllocation(
        community=0.4,      # 40% 社区
        team=0.15,         # 15% 团队
        advisors=0.05,     # 5% 顾问
        treasury=0.2,      # 20% 基金会
        staking_rewards=0.15,  # 15% 质押奖励
        ecosystem_fund=0.05    # 5% 生态基金
    )
    
    # 发射代币
    launch_system.launch_token(allocation, initial_price=0.001)  # 初始价格$0.001
    
    # 获取网络状态
    network_state = launch_system.get_network_state()
    print(f"\n📊 网络状态:\n{json.dumps(network_state, indent=2, default=str)}")
    
    # 演示质押功能
    launch_system.staking.stake_tokens("0xinvestor1", 10000)
    launch_system.staking.stake_tokens("0xinvestor2", 5000)
    
    # 演示治理功能
    proposal_id = launch_system.governance.create_proposal(
        "增加营销预算", 
        "批准额外的营销预算用于推广代币", 
        "0xproposer"
    )
    
    # 演示收益农业
    launch_system.yield_farming.create_farm(
        "w3m_usdc_farm", 
        "W3M", 
        "W3M-USDC LP", 
        100000,  # 10万W3M奖励
        365      # 365天
    )
    
    launch_system.yield_farming.deposit("w3m_usdc_farm", "0xfarmer1", 1000)