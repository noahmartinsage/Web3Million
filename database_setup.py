"""
Web3Million数据库模型 - SQLAlchemy 2.0 ORM模型
实现完整的关系型数据库模型，支持量化交易系统的所有数据需求
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, DECIMAL, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 创建基类
Base = declarative_base()

class User(Base):
    """
    用户表（users）
    存储系统用户信息
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='用户唯一ID')
    username = Column(String(50), unique=True, nullable=False, comment='登录账号')
    password_hash = Column(String(255), nullable=False, comment='加密后的密码（bcrypt算法）')
    email = Column(String(100), unique=True, comment='预留邮箱（用于找回密码）')
    create_time = Column(DateTime, default=func.now(), nullable=False, comment='用户创建时间')
    last_login_time = Column(DateTime, comment='最后登录时间')
    status = Column(Integer, default=1, nullable=False, comment='用户状态（1=正常，0=禁用）')

    # 关系定义
    login_logs = relationship("LoginLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class ExchangeConfig(Base):
    """
    交易所配置表（exchange_config）
    存储交易所API配置信息
    """
    __tablename__ = 'exchange_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='配置ID')
    exchange_name = Column(String(20), unique=True, nullable=False, comment='交易所名称（binance/okx）')
    api_key = Column(String(255), nullable=False, comment='API Key（加密存储）')
    api_secret = Column(String(255), nullable=False, comment='API Secret（加密存储）')
    api_passphrase = Column(String(255), comment='API密码（仅OKX需要，加密存储）')
    is_enabled = Column(Boolean, default=True, nullable=False, comment='是否启用该交易所')
    is_testnet = Column(Boolean, default=True, nullable=False, comment='是否使用测试网（1=模拟盘）')
    create_time = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='最后更新时间')

    def __repr__(self):
        return f"<ExchangeConfig(exchange_name='{self.exchange_name}', is_enabled={self.is_enabled})>"

class AIConfig(Base):
    """
    AI模型配置表（ai_config）
    存储AI模型配置和权重信息
    """
    __tablename__ = 'ai_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='配置ID')
    api_key = Column(String(255), nullable=False, comment='OpenAI兼容API Key（加密存储）')
    base_url = Column(String(255), nullable=False, comment='API Base URL（如DeepSeek地址）')
    model_name = Column(String(50), nullable=False, comment='模型名称（如deepseek-chat）')
    weight_cycle = Column(String(20), default="0 0 * * 0", nullable=False, comment='权重调整周期（Cron表达式）')
    is_enabled = Column(Boolean, default=True, nullable=False, comment='是否启用AI权重优化')
    base_weights = Column(JSON, nullable=False, comment='基础权重（{"onchain":30,...}）')
    current_weights = Column(JSON, nullable=False, comment='当前生效权重')
    create_time = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='最后更新时间')

    def __repr__(self):
        return f"<AIConfig(model_name='{self.model_name}', is_enabled={self.is_enabled})>"

class TradeConfig(Base):
    """
    交易配置表（trade_config）
    存储交易参数配置
    """
    __tablename__ = 'trade_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='配置ID')
    symbol = Column(String(20), default="BTC/USDT", nullable=False, comment='默认交易对')
    cycle = Column(Integer, default=15, nullable=False, comment='交易周期（分钟）')
    single_amount = Column(DECIMAL(10, 2), default=10.00, nullable=False, comment='单笔交易金额（U）')
    risk_ratio = Column(DECIMAL(3, 2), default=1.80, nullable=False, comment='止盈止损风险比')
    max_risk_ratio = Column(DECIMAL(3, 2), default=0.05, nullable=False, comment='单笔风险上限（账户资金比例）')
    forced_liquidation_ratio = Column(DECIMAL(5, 2), default=110.00, nullable=False, comment='强制平仓保证金比例（%）')
    volatility_protection = Column(Boolean, default=True, nullable=False, comment='是否启用波动保护')
    volatility_threshold = Column(DECIMAL(3, 2), default=3.00, nullable=False, comment='波动保护阈值（%）')
    create_time = Column(DateTime, default=func.now(), nullable=False, comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment='最后更新时间')

    def __repr__(self):
        return f"<TradeConfig(symbol='{self.symbol}', cycle={self.cycle})>"

class TradeRecord(Base):
    """
    交易记录表（trade_records）
    存储交易历史记录
    """
    __tablename__ = 'trade_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='交易记录ID')
    exchange_name = Column(String(20), nullable=False, comment='交易所名称')
    symbol = Column(String(20), nullable=False, comment='交易对')
    side = Column(String(10), nullable=False, comment='交易方向（long/short）')
    open_price = Column(DECIMAL(16, 8), nullable=False, comment='开仓价格')
    close_price = Column(DECIMAL(16, 8), comment='平仓价格')
    amount_usd = Column(DECIMAL(10, 2), nullable=False, comment='开仓金额（U）')
    contract_amount = Column(DECIMAL(16, 8), nullable=False, comment='合约数量（币数）')
    stop_loss = Column(DECIMAL(16, 8), nullable=False, comment='止损价格')
    take_profit = Column(DECIMAL(16, 8), nullable=False, comment='止盈价格')
    profit_usd = Column(DECIMAL(10, 2), comment='实际盈亏（U）')
    status = Column(String(20), default='open', nullable=False, comment='交易状态（open/closed/failed）')
    result = Column(String(10), comment='盈亏结果（win/loss，仅平仓后有值）')
    open_time = Column(DateTime, default=func.now(), nullable=False, comment='开仓时间')
    close_time = Column(DateTime, comment='平仓时间')
    open_order_id = Column(String(100), nullable=False, comment='开仓订单ID')
    close_order_id = Column(String(100), comment='平仓订单ID')
    remark = Column(String(255), comment='备注（手动/自动交易、异常说明）')

    def __repr__(self):
        return f"<TradeRecord(id={self.id}, symbol='{self.symbol}', side='{self.side}', status='{self.status}')>"

class IndicatorData(Base):
    """
    指标数据表（indicator_data）
    存储技术指标计算结果
    """
    __tablename__ = 'indicator_data'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='指标记录ID')
    symbol = Column(String(20), nullable=False, comment='交易对')
    datetime = Column(DateTime, default=func.now(), nullable=False, comment='数据时间')
    macd_score = Column(Integer, nullable=False, comment='MACD得分（-10~+10）')
    rsi_score = Column(Integer, nullable=False, comment='RSI得分（-10~+10）')
    kdj_score = Column(Integer, nullable=False, comment='KDJ得分（-10~+10）')
    tech_total = Column(Integer, nullable=False, comment='技术总分（-35~+35）')
    onchain_score = Column(Integer, nullable=False, comment='链上数据得分（-15~+15）')
    sentiment_score = Column(Integer, nullable=False, comment='舆情情感得分（-5~+5）')
    trend_score = Column(Integer, nullable=False, comment='趋势得分（-20~+20）')
    weighted_total = Column(DECIMAL(5, 2), nullable=False, comment='加权总分')
    trade_signal = Column(String(10), nullable=False, comment='交易信号（long/short/wait）')
    weights = Column(JSON, nullable=False, comment='计算时使用的权重')

    def __repr__(self):
        return f"<IndicatorData(symbol='{self.symbol}', datetime='{self.datetime}', weighted_total={self.weighted_total})>"

class OnchainData(Base):
    """
    链上数据表（onchain_data）
    存储链上资金流动数据
    """
    __tablename__ = 'onchain_data'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='链上数据ID')
    symbol = Column(String(20), nullable=False, comment='币种（BTC/ETH）')
    datetime = Column(DateTime, default=func.now(), nullable=False, comment='数据时间')
    whale_transfer_type = Column(String(20), nullable=False, comment='巨鲸转账类型（to_exchange/from_exchange/neutral）')
    whale_transfer_amount = Column(DECIMAL(16, 8), nullable=False, comment='巨鲸转账金额（币数）')
    exchange_net_flow = Column(DECIMAL(16, 8), nullable=False, comment='交易所24小时净流入（币数）')
    onchain_score = Column(Integer, nullable=False, comment='链上数据得分（-15~+15）')
    source = Column(String(50), default='AkShare', nullable=False, comment='数据来源')

    def __repr__(self):
        return f"<OnchainData(symbol='{self.symbol}', whale_transfer_type='{self.whale_transfer_type}', onchain_score={self.onchain_score})>"

class Alert(Base):
    """
    警报记录表（alerts）
    存储系统警报信息
    """
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='警报ID')
    alert_type = Column(String(20), nullable=False, comment='警报类型（trade/error/profit/backup）')
    title = Column(String(100), nullable=False, comment='警报标题')
    content = Column(Text, nullable=False, comment='警报详情')
    is_read = Column(Boolean, default=False, nullable=False, comment='是否已读（0=未读，1=已读）')
    is_pushed = Column(Boolean, default=False, nullable=False, comment='是否已推送到Telegram')
    create_time = Column(DateTime, default=func.now(), nullable=False, comment='警报生成时间')

    def __repr__(self):
        return f"<Alert(id={self.id}, alert_type='{self.alert_type}', title='{self.title}')>"

class BackupRecord(Base):
    """
    备份记录表（backup_records）
    存储数据库备份记录
    """
    __tablename__ = 'backup_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='备份ID')
    backup_type = Column(String(20), nullable=False, comment='备份类型（auto/manual）')
    file_path = Column(String(255), nullable=False, comment='备份文件路径')
    file_size = Column(Integer, nullable=False, comment='文件大小（字节）')
    status = Column(String(20), nullable=False, comment='备份状态（success/failed）')
    create_time = Column(DateTime, default=func.now(), nullable=False, comment='备份时间')
    operator = Column(String(50), nullable=False, comment='操作人（系统/用户名）')

    def __repr__(self):
        return f"<BackupRecord(id={self.id}, backup_type='{self.backup_type}', status='{self.status}')>"

class LoginLog(Base):
    """
    登录日志表（login_logs）
    存储用户登录记录
    """
    __tablename__ = 'login_logs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='日志ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    username = Column(String(50), nullable=False, comment='登录账号')
    ip_address = Column(String(50), nullable=False, comment='登录IP地址')
    user_agent = Column(Text, nullable=False, comment='浏览器/设备信息')
    status = Column(String(10), nullable=False, comment='登录状态（success/failed）')
    login_time = Column(DateTime, default=func.now(), nullable=False, comment='登录时间')
    remark = Column(String(255), comment='备注（失败原因等）')

    # 关系定义
    user = relationship("User", back_populates="login_logs")

    def __repr__(self):
        return f"<LoginLog(username='{self.username}', status='{self.status}', login_time='{self.login_time}')>"

# 创建索引
Index('idx_users_username', User.username)
Index('idx_exchange_config_name', ExchangeConfig.exchange_name)
Index('idx_trade_records_symbol_time', TradeRecord.symbol, TradeRecord.open_time.desc())
Index('idx_indicator_data_symbol_time', IndicatorData.symbol, IndicatorData.datetime.desc())
Index('idx_alerts_unread', Alert.is_read)
Index('idx_login_logs_user_time', LoginLog.user_id, LoginLog.login_time.desc())

def get_database_url():
    """获取数据库连接URL"""
    # 使用SQLite作为默认数据库，便于测试
    return "sqlite:///./web3million.db"

def init_database():
    """初始化数据库连接和创建表"""
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        echo=True,  # 在开发环境中显示SQL语句
        pool_pre_ping=True,  # 连接池预检查
        pool_recycle=3600,   # 连接回收时间
    )
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    # 创建会话工厂
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

if __name__ == "__main__":
    print("正在初始化Web3Million数据库模型...")
    engine, SessionLocal = init_database()
    print("数据库模型初始化完成！")
    print(f"已创建表: {[table.name for table in Base.metadata.tables.values()]}")