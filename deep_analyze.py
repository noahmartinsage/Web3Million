#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子蜂群 - 深度交易分析
分析 5,023 笔历史交易，找出亏损模式和根本原因
"""
import os, sys, io, json, re
from datetime import datetime
from collections import defaultdict

# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🔬 Web3Million 量子蜂群 - 深度交易分析")
print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 读取日志
log_file = 'quantum_hive.log'
if not os.path.exists(log_file):
    print(f"错误：{log_file} 不存在")
    sys.exit(1)

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    lines = content.split('\n')

print(f"\n【1】日志基础统计")
print(f"  日志总行数：{len(lines):,}")

# 提取所有交易记录
trades = []
wins = []
losses = []
symbols = defaultdict(list)
hourly_stats = defaultdict(lambda: {'win': 0, 'loss': 0})

# 解析每行日志
for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # 匹配 WIN/LOSS 记录
    if 'WIN' in line or 'LOSS' in line:
        # 提取智能体编号
        agent_match = re.search(r'\[A(\d+)\]', line)
        agent_id = agent_match.group(1) if agent_match else 'Unknown'
        
        # 提取交易对
        symbol_match = re.search(r'(BTC|ETH|SOL)/USDT', line)
        symbol = symbol_match.group(1) if symbol_match else 'Unknown'
        
        # 判断盈亏
        is_win = 'WIN' in line
        
        trades.append({
            'agent': agent_id,
            'symbol': symbol,
            'is_win': is_win,
            'line': line[:100]
        })
        
        if is_win:
            wins.append(line)
            hourly_stats[symbol[:3]]['win'] += 1
        else:
            losses.append(line)
            hourly_stats[symbol[:3]]['loss'] += 1
        
        if symbol != 'Unknown':
            symbols[symbol].append(is_win)

print(f"  解析交易记录：{len(trades):,}")
print(f"  WIN 数量：{len(wins):,}")
print(f"  LOSS 数量：{len(losses):,}")

if len(trades) > 0:
    win_rate = len(wins) / len(trades) * 100
    print(f"  胜率：{win_rate:.2f}%")

# 按智能体分析
print(f"\n【2】按智能体分析")
agent_stats = defaultdict(lambda: {'win': 0, 'loss': 0})
for trade in trades:
    agent = trade['agent']
    if trade['is_win']:
        agent_stats[agent]['win'] += 1
    else:
        agent_stats[agent]['loss'] += 1

for agent in sorted(agent_stats.keys()):
    stats = agent_stats[agent]
    total = stats['win'] + stats['loss']
    if total > 0:
        rate = stats['win'] / total * 100
        print(f"  智能体 A{agent}: WIN={stats['win']}, LOSS={stats['loss']}, 胜率={rate:.1f}%")

# 按交易对分析
print(f"\n【3】按交易对分析")
for symbol in sorted(symbols.keys()):
    results = symbols[symbol]
    wins_count = sum(1 for r in results if r)
    losses_count = len(results) - wins_count
    total = len(results)
    rate = wins_count / total * 100 if total > 0 else 0
    print(f"  {symbol}: 总交易={total}, WIN={wins_count}, LOSS={losses_count}, 胜率={rate:.1f}%")

# 按小时分析（如果有时间戳）
print(f"\n【4】盈亏模式分析")
# 分析连续亏损
consecutive_losses = []
current_streak = 0
for trade in trades:
    if not trade['is_win']:
        current_streak += 1
    else:
        if current_streak > 1:
            consecutive_losses.append(current_streak)
        current_streak = 0

if consecutive_losses:
    avg_streak = sum(consecutive_losses) / len(consecutive_losses)
    max_streak = max(consecutive_losses)
    print(f"  连续亏损次数统计:")
    print(f"    最大连续亏损：{max_streak} 次")
    print(f"    平均连续亏损：{avg_streak:.1f} 次")
    print(f"    出现次数：{len(consecutive_losses)} 次")

# 分析胜率低的根本原因
print(f"\n【5】问题诊断")
overall_win_rate = len(wins) / len(trades) * 100 if len(trades) > 0 else 0

if overall_win_rate < 40:
    print("  ⚠️ 胜率低于 40% - 策略存在严重问题")
    
    # 检查是否有特定交易对表现差
    worst_symbol = None
    worst_rate = 100
    for symbol in sorted(symbols.keys()):
        results = symbols[symbol]
        wins_count = sum(1 for r in results if r)
        rate = wins_count / len(results) * 100 if results else 0
        if rate < worst_rate:
            worst_rate = rate
            worst_symbol = symbol
    
    if worst_symbol:
        print(f"  - 最差交易对：{worst_symbol} (胜率 {worst_rate:.1f}%)")
    
    # 检查智能体表现差异
    worst_agent = None
    worst_agent_rate = 100
    for agent in sorted(agent_stats.keys()):
        stats = agent_stats[agent]
        total = stats['win'] + stats['loss']
        if total > 0:
            rate = stats['win'] / total * 100
            if rate < worst_agent_rate:
                worst_agent_rate = rate
                worst_agent = agent
    
    if worst_agent:
        print(f"  - 最差智能体：A{worst_agent} (胜率 {worst_agent_rate:.1f}%)")
    
    print("\n  💡 建议改进方向:")
    print("    1. 收紧入场条件 (提高信号阈值)")
    print("    2. 增加趋势过滤 (只在趋势方向交易)")
    print("    3. 添加成交量确认")
    print("    4. 考虑多时间框架确认")
    print("    5. 优化止损/止盈比例")

# 保存分析结果
print(f"\n【6】分析完成")
output_file = 'deep_analysis_result.json'
analysis_result = {
    'total_trades': len(trades),
    'wins': len(wins),
    'losses': len(losses),
    'win_rate': len(wins) / len(trades) * 100 if len(trades) > 0 else 0,
    'by_symbol': {},
    'by_agent': {}
}

for symbol in sorted(symbols.keys()):
    results = symbols[symbol]
    wins_count = sum(1 for r in results if r)
    analysis_result['by_symbol'][symbol] = {
        'total': len(results),
        'wins': wins_count,
        'win_rate': wins_count / len(results) * 100 if results else 0
    }

for agent in sorted(agent_stats.keys()):
    stats = agent_stats[agent]
    total = stats['win'] + stats['loss']
    analysis_result['by_agent'][agent] = {
        'wins': stats['win'],
        'losses': stats['loss'],
        'win_rate': stats['win'] / total * 100 if total > 0 else 0
    }

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, indent=2, ensure_ascii=False)

print(f"  详细结果已保存到：{output_file}")
print("=" * 80)
print("分析完成!")
print("=" * 80)
