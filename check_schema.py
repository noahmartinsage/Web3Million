import sqlite3
conn = sqlite3.connect('C:\\Users\\noah\\.openclaw\\workspace\\web3million.db')
cursor = conn.cursor()

print("=== trade_records 表结构 ===")
cursor.execute("PRAGMA table_info(trade_records)")
cols = cursor.fetchall()
for col in cols:
    print(f"  {col[1]} ({col[2]})")

conn.close()
