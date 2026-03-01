@echo off
REM Clear proxy environment variables
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=
REM Run the trader
python perp_trader_v7_2.py
