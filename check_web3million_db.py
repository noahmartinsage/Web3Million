#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 web3million.db 详细状态"""

import sqlite3
import os
from datetime import datetime

workspace = r"C:\Users\noah\.openclaw\workspace"
db_path = os.path.join(workspace, "web3million.db")

print("=" * 60)
print("web3million.db 详细状态")
print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. trade_records 表
print("\n1. trade_records 表:")
cursor.execute("SELECT COUNT(*) FROM trade_records")
count = cursor.fetchone()[0]
print(f"   总交易数：{count}")

cursor.execute("SELECT SUM(pnl) FROM trade_records WHERE pnl IS NOT NULL")
total_pnl = cursor.fetchone()[0]
print(f"   总 PnL: ${total_pnl:.2f}" if total_pnl else "   总 PnL: $0.00")

cursor.execute("SELECT SUM(pnl) FROM trade_records WHERE pnl IS NOT NULL AND pnl > 0")
win_pnl = cursor.fetchone()[0]
print(f"   总盈利: ${win_pnl:.2f}" if win_pnl else "   总盈利：$0.00")

cursor.execute("SELECT SUM(pnl) FROM trade_records WHERE pnl IS NOT NULL AND pnl < 0")
loss_pnl = cursor.fetchone()[0]
print(f"   总亏损: ${loss_pnl:.2f}" if loss_pnl else "   总亏损：$0.00")

cursor.execute("SELECT COUNT(*) FROM trade_records WHERE pnl IS NOT NULL AND pnl > 0")
wins = cursor.fetchone()[0]
print(f"   盈利次数：{wins}")

cursor.execute("SELECT COUNT(*) FROM trade_records WHERE pnl IS NOT NULL AND pnl < 0")
losses = cursor.fetchone()[0]
print(f"   亏损次数：{losses}")

win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
print(f"   胜率：{win_rate:.1f}%")

# 最近 5 笔交易
print("\n   最近 5 笔交易:")
cursor.execute("""
    SELECT symbol, side, entry_price, exit_price, pnl, timestamp 
    FROM trade_records 
    WHERE pnl IS NOT NULL 
    ORDER BY timestamp DESC 
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"   - {row[0]} {row[1]} | 入场：{row[2]} | 出场：{row[3]} | PnL: ${row[4]:.2f} | {row[5]}")

# 2. 当前持仓
print("\n2. 当前持仓 (positions):")
cursor.execute("SELECT COUNT(*) FROM trade_records WHERE exit_price IS NULL OR exit_price = 0")
open_positions = cursor.fetchone()[0]
print(f"   未平仓位：{open_positions}")

if open_positions > 0:
    cursor.execute("""
        SELECT symbol, side, entry_price, amount, timestamp 
        FROM trade_records 
        WHERE exit_price IS NULL OR exit_price = 0
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   - {row[0]} {row[1]} | 入场：{row[2]} | 数量：{row[3]} | {row[4]}")

# 3. 资金变化
print("\n3. 资金余额:")
cursor.execute("SELECT * FROM users LIMIT 1")
user = cursor.fetchone()
if user:
    print(f"   用户数据：{user}")

# 4. exchange_config
print("\n4. 交易所配置:")
cursor.execute("SELECT * FROM exchange_config LIMIT 1")
config = cursor.fetchone()
if config:
    print(f"   配置：{config}")

# 5. 最新记录时间
print("\n5. 数据时间范围:")
cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM trade_records")
time_range = cursor.fetchone()
if time_range[0]:
    print(f"   最早记录：{time_range[0]}")
    print(f"   最新记录：{time_range[1]}")

conn.close()

print("\n" + "=" * 60)
