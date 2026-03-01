import sqlite3
conn = sqlite3.connect('trading_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cursor.fetchall())

# Check trades
cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 10")
print("\nRecent Trades:")
for row in cursor.fetchall():
    print(row)

conn.close()
