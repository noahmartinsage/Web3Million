#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check v6 trading system status"""
import sqlite3
import os
import json
from datetime import datetime

# Check database
db_path = os.path.join(os.path.dirname(__file__), 'web3million.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Total trades
cursor.execute('SELECT COUNT(*) FROM trade_records')
total_trades = cursor.fetchone()[0]

# Trade statistics
cursor.execute('''
    SELECT 
        SUM(profit_usd) as total_pnl, 
        COUNT(*) as total_trades,
        SUM(CASE WHEN profit_usd > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN profit_usd < 0 THEN 1 ELSE 0 END) as losses
    FROM trade_records 
    WHERE status = "closed"
''')
row = cursor.fetchone()
total_pnl = row[0] if row[0] else 0
wins = row[2] if row[2] else 0
losses = row[3] if row[3] else 0

# Check state file
state_file = os.path.join(os.path.dirname(__file__), 'v6_state.json')
state_exists = os.path.exists(state_file)
state_data = None
if state_exists:
    with open(state_file, 'r') as f:
        state_data = json.load(f)

# Check account balance
import ccxt
exchange = ccxt.okx({
    'apiKey': 'b71ee824-5524-4cde-b818-b8e294c27d56',
    'secret': '76122A8879980469F474F042135584DB',
    'password': 'Qian159.',
    'testnet': True,
    'enableRateLimit': True,
})

balance = exchange.fetch_balance()
usdt_balance = balance['total'].get('USDT', 0)

print("=" * 60)
print("V6 Trading System Status Report")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print(f"Account Balance: {usdt_balance} USDT")
print(f"Target: $5,000 USDT")
print(f"Progress: {usdt_balance/50:.1f}%")
print()
print("Trading Statistics:")
print(f"  Total Trades: {total_trades}")
print(f"  Wins: {wins}")
print(f"  Losses: {losses}")
print(f"  Win Rate: {wins/total_trades*100:.1f}%" if total_trades > 0 else "  Win Rate: N/A")
print(f"  Total PnL: {total_pnl:.2f} USDT")
print()
print("State File:")
print(f"  v6_state.json exists: {state_exists}")
if state_data:
    print(f"  Last trade time: {state_data.get('last_trade_time', 'N/A')}")
    print(f"  Total PnL (state): {state_data.get('total_pnl', 0):.2f} USDT")
print("=" * 60)

conn.close()
