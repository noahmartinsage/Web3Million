#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动 v7.2 交易员 - 直接运行版本"""
import os
import sys

# 清除所有代理
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        try:
            del os.environ[key]
        except:
            pass

# 直接运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入并运行
import importlib.util
spec = importlib.util.spec_from_file_location("perp_trader_v7_2", "perp_trader_v7_2.py")
module = importlib.util.module_from_spec(spec)

print("=" * 50)
print("🦊 Web3Million v7.2 启动中...")
print("=" * 50)
sys.stdout.flush()

spec.loader.exec_module(module)
