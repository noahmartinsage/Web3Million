#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 Web3Million 交易状态和 PnL"""

import sqlite3
import json
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

workspace = r"C:\Users\noah\.openclaw\workspace"

print("=" * 60)
print("Web3Million 交易状态检查")
print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# 1. 检查 evolution_state.json
evolution_state_path = os.path.join(workspace, "evolution_state.json")
if os.path.exists(evolution_state_path):
    with open(evolution_state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    print(f"\n📊 进化状态:")
    print(f"   时间戳：{state.get('timestamp', 'N/A')}")
    print(f"   当前资金：${state.get('capital', 0):.2f}")
    print(f"   反馈次数：{state.get('feedback_count', 0)}")
    print(f"   集成状态：{state.get('integration_active', False)}")
else:
    print("\n⚠️ evolution_state.json 不存在")

# 2. 检查 trading.db
trading_db = os.path.join(workspace, "trading.db")
if os.path.exists(trading_db):
    try:
        conn = sqlite3.connect(trading_db)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"\n💾 trading.db 表列表：{tables}")
        
        # 检查 trade_records 表
        if 'trade_records' in tables:
            cursor.execute("SELECT COUNT(*) FROM trade_records")
            trade_count = cursor.fetchone()[0]
            print(f"   交易记录数：{trade_count}")
            
            cursor.execute("SELECT SUM(pnl) FROM trade_records WHERE pnl IS NOT NULL")
            total_pnl = cursor.fetchone()[0]
            print(f"   总 PnL: ${total_pnl:.2f}" if total_pnl else "   总 PnL: $0.00")
            
            cursor.execute("SELECT * FROM trade_records ORDER BY timestamp DESC LIMIT 5")
            recent = cursor.fetchall()
            if recent:
                print(f"\n   最近 5 笔交易:")
                for r in recent:
                    print(f"   - {r}")
        else:
            print("   ⚠️ trade_records 表不存在")
        
        # 检查 positions 表
        if 'positions' in tables:
            cursor.execute("SELECT COUNT(*) FROM positions")
            pos_count = cursor.fetchone()[0]
            print(f"\n   当前持仓数：{pos_count}")
            
            cursor.execute("SELECT * FROM positions WHERE status='open'")
            open_positions = cursor.fetchall()
            if open_positions:
                print(f"   未平仓位:")
                for p in open_positions:
                    print(f"   - {p}")
        
        conn.close()
    except Exception as e:
        print(f"\n⚠️ 读取 trading.db 失败：{e}")
else:
    print("\n⚠️ trading.db 不存在")

# 3. 检查 web3million.db
web3million_db = os.path.join(workspace, "web3million.db")
if os.path.exists(web3million_db):
    try:
        conn = sqlite3.connect(web3million_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"\n💾 web3million.db 表列表：{tables}")
        
        conn.close()
    except Exception as e:
        print(f"\n⚠️ 读取 web3million.db 失败：{e}")

# 4. 检查输出日志文件
log_files = [
    "v7_2_output.log",
    "v7_2_run.log",
    "v6_output.log"
]

print("\n📄 日志文件状态:")
for log in log_files:
    log_path = os.path.join(workspace, log)
    if os.path.exists(log_path):
        size = os.path.getsize(log_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
        print(f"   ✓ {log}: {size} bytes, 最后更新：{mtime.strftime('%Y-%m-%d %H:%M')}")
        
        # 读取最后 10 行
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-10:]
                if lines:
                    print(f"      最后 10 行:")
                    for line in lines[-5:]:
                        print(f"      {line.strip()[:100]}")
        except:
            pass
    else:
        print(f"   ✗ {log}: 不存在")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
