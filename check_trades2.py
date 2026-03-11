import sqlite3
conn = sqlite3.connect('C:\\Users\\noah\\.openclaw\\workspace\\web3million.db')
cursor = conn.cursor()

print("=== 交易记录 (最近20条) ===")
cursor.execute("SELECT id, symbol, side, open_price, close_price, amount_usd, profit_usd, result, open_time, close_time FROM trade_records ORDER BY open_time DESC LIMIT 20")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"ID:{row[0]} {row[1]} {row[2]} 开仓:{row[3]} 平仓:{row[4]} 金额:{row[5]}U 盈亏:{row[6]}U 结果:{row[7]}")
        print(f"  开仓:{row[8]} 平仓:{row[9]}")
else:
    print("无交易记录")

print("\n=== 账户统计 ===")
cursor.execute("SELECT SUM(profit_usd) as total_pnl, COUNT(*) as total_trades FROM trade_records")
stats = cursor.fetchone()
print(f"总交易数：{stats[1]}")
print(f"总盈亏：{stats[0] if stats[0] else 0} USDT")

cursor.execute("SELECT COUNT(*) FROM trade_records WHERE result='盈利'")
wins = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM trade_records WHERE result='亏损'")
losses = cursor.fetchone()[0]
print(f"盈利笔数：{wins}")
print(f"亏损笔数：{losses}")

conn.close()
