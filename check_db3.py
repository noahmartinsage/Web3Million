import sqlite3
conn = sqlite3.connect('web3million.db')
cursor = conn.cursor()

# Check trade_records
cursor.execute("SELECT * FROM trade_records ORDER BY id DESC LIMIT 10")
print("Recent Trade Records:")
for row in cursor.fetchall():
    print(row)

# Check balance
cursor.execute("SELECT * FROM balance_history ORDER BY id DESC LIMIT 5")
print("\nBalance History:")
for row in cursor.fetchall():
    print(row)

conn.close()
