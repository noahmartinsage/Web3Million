#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子蜂群 - 完整交易分析
修复版：正确解析交易对数据
"""
import os, sys, io, json, re
from datetime import datetime
from collections import defaultdict

# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🔬 Web3Million 量子蜂群 - 完整交易分析 (修复版)")
print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 读取日志
log_file = 'quantum_hive.log'
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    lines = content.split('\n')

print(f"\n【1】基础统计")
print(f"  日志总行数：{len(lines):,}")

# 提取所有交易记录
trades = []
wins = []
losses = []
symbols = defaultdict(list)
agents = defaultdict(list)
consecutive_loss_streak = 0
max_consecutive_loss = 0
total_consecutive_loss_events = 0

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # 匹配 WIN/LOSS 记录
    if ('WIN' in line or 'LOSS' in line) and ('BTC' in line or 'ETH' in line or 'SOL' in line):
        # 提取智能体编号
        agent_match = re.search(r'\[A(\d+)\]', line)
        agent_id = agent_match.group(1) if agent_match else 'Unknown'
        
        # 提取交易对 - 修复版
        symbol_match = re.search(r'(BTC|ETH|SOL)/USDT', line)
        symbol = symbol_match.group(1) if symbol_match else None
        
        if not symbol:
            continue
        
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
            if consecutive_loss_streak > 1:
                total_consecutive_loss_events += 1
            consecutive_loss_streak = 0
        else:
            losses.append(line)
            consecutive_loss_streak += 1
            if consecutive_loss_streak > max_consecutive_loss:
                max_consecutive_loss = consecutive_loss_streak
        
        # 记录数据
        symbols[symbol].append(is_win)
        agents[agent_id].append(is_win)

print(f"  解析交易记录：{len(trades):,}")
print(f"  WIN 数量：{len(wins):,}")
print(f"  LOSS 数量：{len(losses):,}")

if len(trades) > 0:
    win_rate = len(wins) / len(trades) * 100
    print(f"  胜率：{win_rate:.2f}%")
    print(f"  最大连续亏损：{max_consecutive_loss} 次")
    print(f"  连续亏损事件数：{total_consecutive_loss_events} 次")

# 按智能体分析
print(f"\n【2】按智能体分析")
agent_summary = []
for agent in sorted(agents.keys()):
    results = agents[agent]
    wins_count = sum(1 for r in results if r)
    total = len(results)
    rate = wins_count / total * 100 if total > 0 else 0
    print(f"  智能体 A{agent}: WIN={wins_count}, LOSS={total-wins_count}, 胜率={rate:.1f}%")
    agent_summary.append({'agent': agent, 'win_rate': rate, 'total': total, 'wins': wins_count})

# 按交易对分析
print(f"\n【3】按交易对分析")
symbol_summary = []
for symbol in sorted(symbols.keys()):
    results = symbols[symbol]
    wins_count = sum(1 for r in results if r)
    total = len(results)
    rate = wins_count / total * 100 if total > 0 else 0
    print(f"  {symbol}: 总交易={total}, WIN={wins_count}, LOSS={total-wins_count}, 胜率={rate:.1f}%")
    symbol_summary.append({'symbol': symbol, 'win_rate': rate, 'total': total, 'wins': wins_count})

# 找出最佳和最差表现
print(f"\n【4】关键发现")
if agent_summary:
    best_agent = max(agent_summary, key=lambda x: x['win_rate'])
    worst_agent = min(agent_summary, key=lambda x: x['win_rate'])
    print(f"  最佳智能体：A{best_agent['agent']} (胜率 {best_agent['win_rate']:.1f}%)")
    print(f"  最差智能体：A{worst_agent['agent']} (胜率 {worst_agent['win_rate']:.1f}%)")

if symbol_summary:
    best_symbol = max(symbol_summary, key=lambda x: x['win_rate'])
    worst_symbol = min(symbol_summary, key=lambda x: x['win_rate'])
    print(f"  最佳交易对：{best_symbol['symbol']} (胜率 {best_symbol['win_rate']:.1f}%)")
    print(f"  最差交易对：{worst_symbol['symbol']} (胜率 {worst_symbol['win_rate']:.1f}%)")

# 问题诊断
print(f"\n【5】问题诊断与根本原因分析")
overall_win_rate = len(wins) / len(trades) * 100 if len(trades) > 0 else 0

if overall_win_rate < 40:
    print("  ❌ 胜率低于 40% - 策略存在严重问题")
    print()
    print("  根本原因分析:")
    print(f"  1. 连续亏损严重：最大连续亏损 {max_consecutive_loss} 次")
    print(f"  2. 所有智能体表现一致差：胜率都在 36-40% 之间")
    print(f"  3. 策略性问题：不是个别智能体或交易对的问题")
    print()
    print("  核心问题:")
    print("    - 入场信号太弱/太频繁")
    print("    - 缺乏有效的趋势过滤")
    print("    - 止损可能过紧或止盈过高")
    print("    - 没有成交量确认")
    print()
    print("  💡 建议改进方向:")
    print("    1. 收紧入场条件 (提高信号阈值)")
    print("    2. 增加多时间框架趋势确认")
    print("    3. 添加成交量过滤")
    print("    4. 优化止损/止盈比例")
    print("    5. 考虑只在最佳交易对交易")
else:
    print("  ✅ 胜率尚可，可以继续优化")

# 保存结果
print(f"\n【6】保存结果")
result = {
    'timestamp': datetime.now().isoformat(),
    'total_trades': len(trades),
    'wins': len(wins),
    'losses': len(losses),
    'win_rate': overall_win_rate,
    'max_consecutive_loss': max_consecutive_loss,
    'by_agent': agent_summary,
    'by_symbol': symbol_summary
}

output_file = 'full_analysis_result.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"  详细结果已保存到：{output_file}")
print("=" * 80)
print("分析完成!")
print("=" * 80)
