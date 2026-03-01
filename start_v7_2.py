#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动 v7.2 交易员 - 清除代理设置"""
import os
import sys

# 清除所有代理相关环境变量
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]

# 现在导入并运行交易员
print("已清除代理设置，启动 v7.2 交易员...")
exec(open('perp_trader_v7_2.py', encoding='utf-8').read())
