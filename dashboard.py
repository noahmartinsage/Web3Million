#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3Million Real-time Dashboard
- Quantum Hive agent status
- Real-time PnL tracking
- Million dollar goal progress
- Daji connection status
"""
import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Clear proxy settings
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(var, None)

try:
    import ccxt
except ImportError:
    print("Error: ccxt not found")
    sys.exit(1)

WORKSPACE = Path(__file__).parent

def get_python_processes():
    """Get Python process count"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'],
            capture_output=True, text=True, timeout=5, cwd=WORKSPACE
        )
        return int(result.stdout.strip())
    except:
        return 0

def get_account_balance():
    """Get account balance"""
    try:
        config_path = WORKSPACE / 'okx_config.json'
        if not config_path.exists():
            return 0.0
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        okx = ccxt.okx({
            'apiKey': config['api_key'],
            'secret': config['secret_key'],
            'password': config['passphrase'],
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'}
        })
        okx.set_sandbox_mode(True)
        okx.session.trust_env = False
        okx.session.proxies = {}
        
        balance = okx.fetch_balance()
        return float(balance['total'].get('USDT', 0))
    except Exception as e:
        return 0.0

def check_daji_connection():
    """Check Daji connection status"""
    soul_exists = (WORKSPACE / 'SOUL.md').exists()
    user_exists = (WORKSPACE / 'USER.md').exists()
    memory_exists = (WORKSPACE / 'MEMORY.md').exists()
    identity_exists = (WORKSPACE / 'IDENTITY.md').exists()
    
    return {
        'SOUL.md': soul_exists,
        'USER.md': user_exists,
        'MEMORY.md': memory_exists,
        'IDENTITY.md': identity_exists,
        'connected': soul_exists and user_exists and identity_exists
    }

def get_progress_to_million(current: float, target: float = 1000000.0) -> float:
    """Calculate million dollar goal progress"""
    return (current / target) * 100

def render_dashboard():
    """Render dashboard"""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get data
        python_count = get_python_processes()
        balance = get_account_balance()
        daji_status = check_daji_connection()
        progress = get_progress_to_million(balance)
        
        # Render
        print("=" * 80)
        print("  Web3Million Real-time Dashboard")
        print(f"  Time: {now}")
        print("=" * 80)
        
        print(f"\n[SYSTEM STATUS]")
        status_icon = "[OK]" if python_count > 0 else "[WARN]"
        print(f"  {status_icon} Quantum Hive Processes: {python_count}")
        
        print(f"\n[ACCOUNT]")
        print(f"  Balance: ${balance:.2f} USDT")
        print(f"  Target:  $1,000,000.00 USDT")
        print(f"  Progress: {progress:.4f}%")
        
        # Progress bar
        bar_width = 40
        filled = int(bar_width * progress / 100)
        bar = '=' * filled + '-' * (bar_width - filled)
        print(f"  [{bar}] {progress:.4f}%")
        
        print(f"\n[DAJI CONNECTION]")
        for file, exists in daji_status.items():
            if file != 'connected':
                icon = "[OK]" if exists else "[MISSING]"
                print(f"  {icon} {file}")
        
        connection_status = "[OK]" if daji_status['connected'] else "[WARN]"
        print(f"\n  {connection_status} Overall Connection: {'Connected' if daji_status['connected'] else 'Not Connected'}")
        
        print(f"\n[TARGET PROGRESS]")
        print(f"  Current: ${balance:.2f}")
        print(f"  Target:  $1,000,000.00")
        print(f"  Remaining: ${1000000 - balance:.2f}")
        
        print(f"\n[ACTION]")
        print("  Press Ctrl+C to exit")
        
        time.sleep(5)

if __name__ == '__main__':
    try:
        render_dashboard()
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
