# MEV Bot 🤖⚡

以太坊MEV（Maximal Extractable Value）机器人套件

## 📁 项目结构

```
mev_bot/
├── MEV_BOT_PLAN.md          # 开发计划文档
├── README.md                 # 本文件
├── mempool_listener.py       # Mempool监听器
├── arbitrage_detector.py     # 套利机会检测器
├── flashbots_sender.py       # Flashbots交易发送器
└── contracts/                # 智能合约（待添加）
    └── arbitrage.sol         # 套利合约
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install web3 asyncio eth-account
```

### 2. 配置RPC节点

编辑各文件中的 `RPC_URL`，替换为你的节点URL：
- Alchemy: https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
- Infura: https://mainnet.infura.io/v3/YOUR_KEY
- 自建节点: http://localhost:8545

### 3. 运行监听器

```bash
python mempool_listener.py
```

### 4. 运行套利检测器

```bash
python arbitrage_detector.py
```

## 📚 核心模块

### Mempool监听器 (`mempool_listener.py`)
- 实时监听以太坊待处理交易
- 识别DEX交易（Uniswap、SushiSwap等）
- 过滤高价值交易
- 提供交易类型检测

### 套利检测器 (`arbitrage_detector.py`)
- 跨DEX价格监控
- 实时套利机会发现
- 支持多交易对扫描
- 潜在利润计算

### Flashbots发送器 (`flashbots_sender.py`)
- Flashbots Bundle发送
- 隐私交易支持
- Bundle模拟执行
- 避免被抢跑

## ⚙️ 配置说明

### 最小利润阈值
```python
detector = ArbitrageDetector(
    min_profit_usd=10.0,      # 最小利润$10
    min_price_diff_pct=0.5    # 最小价差0.5%
)
```

### 扫描间隔
```python
listener = MempoolListener(
    scan_interval=0.5  # 0.5秒扫描一次
)
```

## ⚠️ 注意事项

1. **安全性**：
   - 永远不要在代码中硬编码私钥
   - 使用环境变量或加密存储
   - 测试网充分验证后再上主网

2. **成本**：
   - 需要ETH支付Gas费
   - 推荐使用Flashbots避免被抢跑
   - 套利失败会损失Gas费

3. **竞争**：
   - MEV市场竞争激烈
   - 需要优化Gas golfing
   - 低延迟节点是关键

## 📖 学习资源

- [Flashbots官方文档](https://docs.flashbots.net/)
- [以太坊MEV指南](https://ethereum.org/developers/docs/mev/)
- [WTF-Ethers Flashbots教程](https://github.com/WTFAcademy/WTF-Ethers/blob/main/25_Flashbots/readme.md)

## 🔄 开发进度

- [x] Mempool监听器 v1.0
- [x] 套利检测器 v1.0
- [x] Flashbots发送器 v1.0
- [ ] 套利智能合约
- [ ] 三明治攻击检测
- [ ] 清算机器人
- [ ] 主网部署

## 📊 预期收益

| 策略 | 风险 | 月收益预期 |
|------|------|-----------|
| DEX套利 | 低 | $500-2000 |
| 三明治攻击 | 中 | $2000-10000 |
| 清算机器人 | 低 | $1000-5000 |

## 🦊 关于

由妲己 AI Agent开发，作为Web3Million项目的一部分。

---

*最后更新：2026-03-14*
