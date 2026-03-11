import sqlite3

conn = sqlite3.connect('trading.db')
cursor = conn.cursor()

# 查询总 PnL 和交易次数
cursor.execute('SELECT SUM(pnl) as total_pnl, COUNT(*) as trade_count FROM trade_records')
result = cursor.fetchone()
print(f'Total PnL: {result[0]}')
print(f'Trade Count: {result[1]}')

# 查询当前余额
cursor.execute('SELECT balance FROM account_balance ORDER BY timestamp DESC LIMIT 1')
balance = cursor.fetchone()
print(f'Current Balance: {balance[0] if balance else "N/A"}')

# 查询最近 5 笔交易
cursor.execute('SELECT timestamp, symbol, side, pnl FROM trade_records ORDER BY timestamp DESC LIMIT 5')
recent = cursor.fetchall()
print('\nRecent Trades:')
for trade in recent:
    print(f'  {trade[0]} | {trade[1]} | {trade[2]} | PnL: {trade[3]}')

conn.close()
