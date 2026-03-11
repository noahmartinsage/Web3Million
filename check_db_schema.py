#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库表结构"""

import sqlite3
import os
from datetime import datetime

workspace = r"C:\Users\noah\.openclaw\workspace"
db_path = os.path.join(workspace, "web3million.db")

print("=" * 60)
print("web3million.db 表结构检查")
print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(f"\n所有表：{tables}")

# 检查每个表的结构
for table in tables:
    print(f"\n{'='*40}")
    print(f"表：{table}")
    print(f"{'='*40}")
    
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"列结构:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")
    
    # 获取记录数
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"记录数：{count}")
    
    # 获取前 3 条记录
    if count > 0:
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        print(f"示例数据:")
        for row in rows:
            print(f"   {row}")

conn.close()

print("\n" + "=" * 60)
