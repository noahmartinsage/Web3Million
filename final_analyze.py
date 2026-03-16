#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million 量子蜂群 - 最终版交易分析
修复：正确处理日志格式
"""
import os, sys, io, json, re
from datetime import datetime
from collections import defaultdict

# Windows 强制 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("🔬 Web3Million 量子蜂群 - 最终版交易分析")
print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 读取日志
log_file = 'quantum_hive.log'
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 按行分割
lines = content.split('\n')
print(f"\n【1】基础统计")
print(f"  日志总行数：{len(lines):,}")

# 提取所有 WIN/LOSS 记录
# 格式：[A1] WIN +$0.0000 | Bal: $0.0000 或 [A1] LOSS $-0.0000 | Bal: $0.0000
# 需要找到前面的交易对信息

# 先提取所有包含 WIN/LOSS 的行
win_loss_lines = []
for line in lines:
    line = line.strip()
    if line and ('WIN' in line or 'LOSS' in line):
        win_loss_lines.append(line)

print(f"  WIN/LOSS 记录数：{len(win_loss_lines):,}")

# 分析每条记录
trades = []
wins = []
losses = []
symbols = defaultdict(list)
agents = defaultdict(list)

# 用于追踪当前上下文的交易对
current_symbols = {}  # agent -> symbol

# 遍历所有行，建立上下文
for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # 查找买卖记录，建立 agent->symbol 映射
    buy_match = re.search(r'\[(A\d+)\] (BUY|SELL) (BTC|ETH|SOL)/USDT', line)
    if buy_match:
        agent = buy_match.group(1)
        symbol = buy_match.group(3)
        current_symbols[agent] = symbol
    
    # 查找 WIN/LOSS 记录
    win_loss_match = re.search(r'\[(A\d+)\] (WIN|LOSS)', line)
    if win_loss_match:
        agent = win_loss_match.group(1)
        result = win_loss_match.group(2)
        symbol = current_symbols.get(agent, 'Unknown')
        is_win = (result == 'WIN')
        
        trades.append({
            'agent': agent,
            'symbol': symbol,
            'is_win': is_win
        })
        
        if is_win:
            wins.append(line)
        else:
            losses.append(line)
        
        symbols[symbol].append(is_win)
        agents[agent].append(is_win)

print(f"  解析交易记录：{len(trades):,}")
print(f"  WIN 数量：{len(wins):,}")
print(f"  LOSS 数量：{len(losses):,}")

if len(trades) > 0:
    win_rate = len(wins) / len(trades) * 100
    print(f"  胜率：{win_rate:.2f}%")

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

# 连续亏损分析
print(f"\n【4】连续亏损分析")
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
    print(f"  最大连续亏损：{max_streak} 次")
    print(f"  平均连续亏损：{avg_streak:.1f} 次")
    print(f"  连续亏损事件数：{len(consecutive_losses)} 次")
else:
    print("  无明显连续亏损模式")

# 问题诊断
print(f"\n【5】问题诊断与根本原因分析")
overall_win_rate = len(wins) / len(trades) * 100 if len(trades) > 0 else 0

if overall_win_rate < 40:
    print(f"  ❌ 胜率低于 40% - 策略存在严重问题 (当前：{overall_win_rate:.1f}%)")
    print()
    print("  根本原因分析:")
    
    # 检查是否所有智能体都差
    if agent_summary:
        avg_agent_rate = sum(a['win_rate'] for a in agent_summary) / len(agent_summary)
        print(f"  1. 所有智能体平均胜率：{avg_agent_rate:.1f}% (一致性差)")
    
    # 检查交易对表现
    if symbol_summary:
        for s in symbol_summary:
            if s['win_rate'] < 40:
                print(f"  2. {s['symbol']} 胜率仅{s['win_rate']:.1f}%")
    
    print()
    print("  核心问题:")
    print("    - 入场信号太弱/太频繁 (需要提高阈值)")
    print("    - 缺乏有效的趋势过滤 (需要多时间框架确认)")
    print("    - 止损可能过紧或止盈过高 (需要优化盈亏比)")
    print("    - 没有成交量确认 (需要添加成交量过滤)")
    print()
    print("  💡 建议改进方向:")
    print("    1. 收紧入场条件 (提高 RSI/MACD 阈值)")
    print("    2. 增加多时间框架趋势确认 (1h/4h 确认)")
    print("    3. 添加成交量过滤 (>80% 均量)")
    print("    4. 优化止损/止盈比例 (建议 1:2 或 1:3)")
    print("    5. 考虑只在最佳智能体/交易对交易")
else:
    print(f"  ✅ 胜率 {overall_win_rate:.1f}% 尚可，可以继续优化")

# 保存结果
print(f"\n【6】保存结果")
result = {
    'timestamp': datetime.now().isoformat(),
    'total_trades': len(trades),
    'wins': len(wins),
    'losses': len(losses),
    'win_rate': overall_win_rate,
    'by_agent': agent_summary,
    'by_symbol': symbol_summary
}

output_file = 'final_analysis_result.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"  详细结果已保存到：{output_file}")
print("=" * 80)
print("分析完成!")
print("=" * 80)
