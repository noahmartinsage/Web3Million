// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title DEXArbitrage
 * @author 妲己 AI Agent
 * @notice 跨DEX套利智能合约 - 从价格差异中获利
 * @dev 使用闪电贷进行无本金套利
 */

// Uniswap V2 Router接口
interface IUniswapV2Router02 {
    function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts);
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
    function swapTokensForExactTokens(
        uint amountOut,
        uint amountInMax,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}

// Uniswap V2 Pair接口
interface IUniswapV2Pair {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

// 闪电贷接口（Aave）
interface IFlashLoanProvider {
    function flashLoan(
        address receiver,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

/**
 * @title DEXArbitrage
 * @dev 跨DEX套利合约
 */
contract DEXArbitrage is ReentrancyGuard, Ownable {
    
    // 事件
    event ArbitrageExecuted(
        address indexed tokenBuy,
        address indexed tokenSell,
        uint256 profit,
        uint256 timestamp
    );
    
    event FlashLoanExecuted(
        address indexed asset,
        uint256 amount,
        uint256 premium
    );
    
    // DEX路由器映射
    mapping(string => address) public dexRouters;
    
    // 支持的代币
    mapping(address => bool) public supportedTokens;
    
    // 利润接收地址
    address public profitReceiver;
    
    // 最小利润阈值（basis points）
    uint256 public minProfitBps = 50; // 0.5%
    
    // 紧急暂停
    bool public paused = false;
    
    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }
    
    constructor(address _profitReceiver) {
        profitReceiver = _profitReceiver;
        
        // 初始化主流DEX路由器（主网地址）
        dexRouters["uniswap_v2"] = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
        dexRouters["sushiswap"] = 0xd9e1cE17a264Dd44cAaC8B4b9D8B5675C6F0E8B0;
        
        // 初始化支持的主流代币
        supportedTokens[0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2] = true; // WETH
        supportedTokens[0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48] = true; // USDC
        supportedTokens[0xdAC17F958D2ee523a2206206994597C13D831ec7] = true; // USDT
        supportedTokens[0x6B175474E89094C44Da98b954EessdCdAE3F2725] = true; // DAI
    }
    
    /**
     * @notice 执行套利（不使用闪电贷，需要本金）
     * @param tokenA 代币A地址
     * @param tokenB 代币B地址
     * @param amountIn 输入金额
     * @param dexBuy 买入DEX名称
     * @param dexSell 卖出DEX名称
     */
    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        string calldata dexBuy,
        string calldata dexSell
    ) external nonReentrant whenNotPaused {
        require(supportedTokens[tokenA] && supportedTokens[tokenB], "Token not supported");
        
        address routerBuy = dexRouters[dexBuy];
        address routerSell = dexRouters[dexSell];
        require(routerBuy != address(0) && routerSell != address(0), "DEX not found");
        
        // 从调用者转入代币
        IERC20(tokenA).transferFrom(msg.sender, address(this), amountIn);
        
        // 执行套利路径：tokenA -> tokenB -> tokenA
        uint256 balanceBefore = IERC20(tokenA).balanceOf(address(this));
        
        // 第一步：在dexBuy买入tokenB
        address[] memory path1 = new address[](2);
        path1[0] = tokenA;
        path1[1] = tokenB;
        
        IERC20(tokenA).approve(routerBuy, amountIn);
        uint256[] memory amounts1 = IUniswapV2Router02(routerBuy).swapExactTokensForTokens(
            amountIn,
            0, // 接受任意数量（实际中应该设置最小值）
            path1,
            address(this),
            block.timestamp
        );
        
        // 第二步：在dexSell卖回tokenA
        uint256 amountB = amounts1[1];
        address[] memory path2 = new address[](2);
        path2[0] = tokenB;
        path2[1] = tokenA;
        
        IERC20(tokenB).approve(routerSell, amountB);
        uint256[] memory amounts2 = IUniswapV2Router02(routerSell).swapExactTokensForTokens(
            amountB,
            0,
            path2,
            address(this),
            block.timestamp
        );
        
        uint256 balanceAfter = IERC20(tokenA).balanceOf(address(this));
        uint256 profit = balanceAfter - balanceBefore;
        
        // 检查利润
        require(profit > 0, "No profit generated");
        
        // 发送利润
        IERC20(tokenA).transfer(profitReceiver, profit);
        
        // 发还本金
        IERC20(tokenA).transfer(msg.sender, balanceBefore);
        
        emit ArbitrageExecuted(tokenA, tokenB, profit, block.timestamp);
    }
    
    /**
     * @notice 使用闪电贷套利（无需本金）
     * @param flashLoanProvider 闪电贷提供者地址（如Aave）
     * @param asset 借款资产
     * @param amount 借款金额
     * @param params 编码的套利参数
     */
    function executeFlashLoanArbitrage(
        address flashLoanProvider,
        address asset,
        uint256 amount,
        bytes calldata params
    ) external onlyOwner {
        address[] memory assets = new address[](1);
        assets[0] = asset;
        
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0; // 0 = no debt, just flash loan
        
        IFlashLoanProvider(flashLoanProvider).flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            params,
            0
        );
    }
    
    /**
     * @notice 闪电贷回调函数
     * @dev Aave闪电贷标准接口
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        // 解码参数
        (
            address dexBuy,
            address dexSell,
            address tokenA,
            address tokenB
        ) = abi.decode(params, (address, address, address, address));
        
        // 执行套利逻辑（类似executeArbitrage）
        // ...（省略具体实现）
        
        // 归还闪电贷 + 手续费
        IERC20(asset).approve(msg.sender, amount + premium);
        
        emit FlashLoanExecuted(asset, amount, premium);
        
        return true;
    }
    
    /**
     * @notice 计算套利利润
     * @param router1 DEX1路由器
     * @param router2 DEX2路由器
     * @param tokenA 代币A
     * @param tokenB 代币B
     * @param amountIn 输入金额
     */
    function calculateProfit(
        address router1,
        address router2,
        address tokenA,
        address tokenB,
        uint256 amountIn
    ) external view returns (int256 profit, uint256 priceDiffBps) {
        // 获取DEX1价格
        address[] memory path1 = new address[](2);
        path1[0] = tokenA;
        path1[1] = tokenB;
        uint256[] memory amounts1 = IUniswapV2Router02(router1).getAmountsOut(amountIn, path1);
        
        // 获取DEX2价格
        address[] memory path2 = new address[](2);
        path2[0] = tokenB;
        path2[1] = tokenA;
        uint256[] memory amounts2 = IUniswapV2Router02(router2).getAmountsOut(amounts1[1], path2);
        
        // 计算利润
        profit = int256(amounts2[1]) - int256(amountIn);
        
        // 计算价差（basis points）
        if (amountIn > 0) {
            priceDiffBps = ((amounts2[1] - amountIn) * 10000) / amountIn;
        }
    }
    
    // 管理函数
    function setDexRouter(string calldata name, address router) external onlyOwner {
        dexRouters[name] = router;
    }
    
    function setSupportedToken(address token, bool supported) external onlyOwner {
        supportedTokens[token] = supported;
    }
    
    function setMinProfitBps(uint256 bps) external onlyOwner {
        minProfitBps = bps;
    }
    
    function setPaused(bool _paused) external onlyOwner {
        paused = _paused;
    }
    
    function withdraw(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
    }
    
    // 紧急提取
    function emergencyWithdraw(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner(), balance);
    }
}
