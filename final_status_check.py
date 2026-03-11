#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Web3Million 最终状态检查 - 正确列名"""

import sqlite3
import json
import os
from datetime import datetime

workspace = r"C:\Users\noah\.openclaw\workspace"

print("=" * 60)
print("Web3Million 交易状态汇报")
print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 1. evolution_state.json
evolution_state_path = os.path.join(workspace, "evolution_state.json")
if os.path.exists(evolution_state_path):
    with open(evolution_state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    print(f"\n【进化状态】")
    print(f"   时间戳：{state.get('timestamp', 'N/A')}")
    print(f"   当前资金：${state.get('capital', 0):.2f}")
    print(f"   反馈次数：{state.get('feedback_count', 0)}")
    initial_capital = 10.0
    current_capital = state.get('capital', 10.0)
    growth = ((current_capital - initial_capital) / initial_capital) * 100
    print(f"   初始资金：${initial_capital:.2f}")
    print(f"   增长率：{growth:.1f}%")
    print(f"   增长倍数：{current_capital / initial_capital:.1f}x")

# 2. web3million.db - trade_records
db_path = os.path.join(workspace, "web3million.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n【交易记录】")
    cursor.execute("SELECT COUNT(*) FROM trade_records")
    total_trades = cursor.fetchone()[0]
    print(f"   总交易数：{total_trades}")
    
    cursor.execute("SELECT COUNT(*) FROM trade_records WHERE status='closed'")
    closed_trades = cursor.fetchone()[0]
    print(f"   已完成：{closed_trades}")
    
    cursor.execute("SELECT COUNT(*) FROM trade_records WHERE status='open'")
    open_trades = cursor.fetchone()[0]
    print(f"   进行中：{open_trades}")
    
    # PnL 统计 (使用 profit_usd 列)
    cursor.execute("SELECT SUM(profit_usd) FROM trade_records WHERE profit_usd IS NOT NULL AND status='closed'")
    total_pnl = cursor.fetchone()[0]
    print(f"   总盈亏：${total_pnl:.2f}" if total_pnl else "   总盈亏：$0.00")
    
    cursor.execute("SELECT SUM(profit_usd) FROM trade_records WHERE profit_usd IS NOT NULL AND profit_usd > 0 AND status='closed'")
    win_pnl = cursor.fetchone()[0]
    print(f"   总盈利：${win_pnl:.2f}" if win_pnl else "   总盈利：$0.00")
    
    cursor.execute("SELECT SUM(profit_usd) FROM trade_records WHERE profit_usd IS NOT NULL AND profit_usd < 0 AND status='closed'")
    loss_pnl = cursor.fetchone()[0]
    print(f"   总亏损：${loss_pnl:.2f}" if loss_pnl else "   总亏损：$0.00")
    
    cursor.execute("SELECT COUNT(*) FROM trade_records WHERE profit_usd IS NOT NULL AND profit_usd > 0 AND status='closed'")
    wins = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trade_records WHERE profit_usd IS NOT NULL AND profit_usd < 0 AND status='closed'")
    losses = cursor.fetchone()[0]
    
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    print(f"   盈利次数：{wins} | 亏损次数：{losses}")
    print(f"   胜率：{win_rate:.1f}%")
    
    # 最近交易
    print(f"\n   最近 5 笔交易:")
    cursor.execute("""
        SELECT symbol, side, open_price, close_price, profit_usd, status, open_time 
        FROM trade_records 
        ORDER BY open_time DESC 
        LIMIT 5
    """)
    for row in cursor.fetchall():
        status_mark = "[OPEN]" if row[5] == 'open' else "[CLOSED]"
        pnl_str = f"${row[4]:.2f}" if row[4] else "N/A"
        print(f"   {status_mark} {row[0]} {row[1]} | 开仓：{row[2]} | 平仓：{row[3]} | 盈亏：{pnl_str} | {row[6]}")
    
    # 未平仓位
    print(f"\n【未平仓位】")
    cursor.execute("""
        SELECT symbol, side, open_price, amount_usd, open_time 
        FROM trade_records 
        WHERE status='open'
        ORDER BY open_time DESC
    """)
    open_positions = cursor.fetchall()
    if open_positions:
        for pos in open_positions:
            print(f"   - {pos[0]} {pos[1]} | 开仓：{pos[2]} | 金额：${pos[3]} | {pos[4]}")
    else:
        print("   无未平仓位")
    
    # 时间范围
    print(f"\n【数据时间范围】")
    cursor.execute("SELECT MIN(open_time), MAX(open_time) FROM trade_records")
    time_range = cursor.fetchone()
    if time_range[0]:
        print(f"   最早：{time_range[0]}")
        print(f"   最新：{time_range[1]}")
    
    conn.close()

# 3. 日志文件
print(f"\n【日志文件】")
log_files = ["v7_2_output.log", "v7_2_run.log", "v6_output.log"]
for log in log_files:
    log_path = os.path.join(workspace, log)
    if os.path.exists(log_path):
        size = os.path.getsize(log_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
        status = "活跃" if (datetime.now() - mtime).days < 7 else "陈旧"
        print(f"   [{status}] {log}: {size} bytes | 最后更新：{mtime.strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"   [不存在] {log}")

print("\n" + "=" * 60)
print("汇报完成")
print("=" * 60)
