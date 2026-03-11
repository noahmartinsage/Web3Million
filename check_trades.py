import sqlite3
conn = sqlite3.connect('C:\\Users\\noah\\.openclaw\\workspace\\web3million.db')
cursor = conn.cursor()

print("=== 交易记录 ===")
cursor.execute("SELECT * FROM trade_records ORDER BY rowid DESC LIMIT 20")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(row)
else:
    print("无交易记录")

print("\n=== 账户统计 ===")
cursor.execute("SELECT SUM(profit_loss) as total_pnl, COUNT(*) as total_trades FROM trade_records")
stats = cursor.fetchone()
print(f"总交易数：{stats[1]}")
print(f"总盈亏：{stats[0] if stats[0] else 0} USDT")

conn.close()
