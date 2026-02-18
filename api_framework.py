"""
Web3Million API接口框架 - FastAPI基础架构和认证系统
实现完整的API接口层，支持量化交易系统的前后端分离架构
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database_setup import User, ExchangeConfig, AIConfig, TradeConfig, Base
from database_setup import get_database_url, init_database
# 初始化数据库连接和Session
engine, SessionLocal = init_database()
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="Web3Million API",
    description="Web3Million量化交易系统API接口",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "web3million-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic模型定义
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    create_time: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class ExchangeConfigUpdate(BaseModel):
    exchange_name: str
    api_key: str
    api_secret: str
    api_passphrase: Optional[str] = None
    is_enabled: bool = True
    is_testnet: bool = True

class AIConfigUpdate(BaseModel):
    api_key: str
    base_url: str
    model_name: str
    weight_cycle: str = "0 0 * * 0"
    is_enabled: bool = True
    base_weights: Dict[str, int] = {"onchain": 30, "tech": 35, "sentiment": 5, "trend": 20}

class TradeConfigUpdate(BaseModel):
    symbol: str = "BTC/USDT"
    cycle: int = 15
    single_amount: float = 10.00
    risk_ratio: float = 1.80
    max_risk_ratio: float = 0.05
    forced_liquidation_ratio: float = 110.00
    volatility_protection: bool = True
    volatility_threshold: float = 3.00

# 辅助函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.JWTError:
        raise credentials_exception
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API路由
@app.get("/")
async def root():
    return {"message": "Welcome to Web3Million API", "version": "1.0.0"}

@app.post("/api/auth/login", response_model=Token)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口
    """
    user = authenticate_user(db, login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    user.last_login_time = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        username=user_create.username,
        password_hash=hashed_password,
        email=user_create.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.get("/api/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    """
    return current_user

# 配置接口
@app.get("/api/config/exchange", response_model=Dict[str, Any])
async def get_exchange_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取交易所配置
    """
    configs = db.query(ExchangeConfig).all()
    return {
        "configs": [{"id": c.id, "exchange_name": c.exchange_name, "is_enabled": c.is_enabled, 
                     "is_testnet": c.is_testnet, "create_time": c.create_time} for c in configs]
    }

@app.put("/api/config/exchange")
async def update_exchange_config(config_update: ExchangeConfigUpdate, 
                                current_user: User = Depends(get_current_user), 
                                db: Session = Depends(get_db)):
    """
    更新交易所配置
    """
    # 检查是否已存在该交易所配置
    existing_config = db.query(ExchangeConfig).filter(
        ExchangeConfig.exchange_name == config_update.exchange_name
    ).first()
    
    if existing_config:
        # 更新现有配置
        existing_config.api_key = config_update.api_key
        existing_config.api_secret = config_update.api_secret
        existing_config.api_passphrase = config_update.api_passphrase
        existing_config.is_enabled = config_update.is_enabled
        existing_config.is_testnet = config_update.is_testnet
    else:
        # 创建新配置
        new_config = ExchangeConfig(
            exchange_name=config_update.exchange_name,
            api_key=config_update.api_key,
            api_secret=config_update.api_secret,
            api_passphrase=config_update.api_passphrase,
            is_enabled=config_update.is_enabled,
            is_testnet=config_update.is_testnet
        )
        db.add(new_config)
    
    db.commit()
    return {"message": "Configuration updated successfully"}

@app.get("/api/config/ai", response_model=Dict[str, Any])
async def get_ai_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取AI模型配置
    """
    config = db.query(AIConfig).first()
    if config:
        return {
            "id": config.id,
            "model_name": config.model_name,
            "is_enabled": config.is_enabled,
            "weight_cycle": config.weight_cycle,
            "base_weights": config.base_weights,
            "current_weights": config.current_weights
        }
    else:
        return {"message": "No AI configuration found"}

@app.put("/api/config/ai")
async def update_ai_config(config_update: AIConfigUpdate, 
                          current_user: User = Depends(get_current_user), 
                          db: Session = Depends(get_db)):
    """
    更新AI模型配置
    """
    # 检查是否已存在AI配置
    existing_config = db.query(AIConfig).first()
    
    if existing_config:
        # 更新现有配置
        existing_config.api_key = config_update.api_key
        existing_config.base_url = config_update.base_url
        existing_config.model_name = config_update.model_name
        existing_config.weight_cycle = config_update.weight_cycle
        existing_config.is_enabled = config_update.is_enabled
        existing_config.base_weights = config_update.base_weights
        existing_config.current_weights = config_update.base_weights  # 初始化当前权重为基线权重
    else:
        # 创建新配置
        new_config = AIConfig(
            api_key=config_update.api_key,
            base_url=config_update.base_url,
            model_name=config_update.model_name,
            weight_cycle=config_update.weight_cycle,
            is_enabled=config_update.is_enabled,
            base_weights=config_update.base_weights,
            current_weights=config_update.base_weights
        )
        db.add(new_config)
    
    db.commit()
    return {"message": "AI Configuration updated successfully"}

@app.get("/api/config/trade", response_model=Dict[str, Any])
async def get_trade_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    获取交易配置
    """
    config = db.query(TradeConfig).first()
    if config:
        return {
            "id": config.id,
            "symbol": config.symbol,
            "cycle": config.cycle,
            "single_amount": float(config.single_amount),
            "risk_ratio": float(config.risk_ratio),
            "max_risk_ratio": float(config.max_risk_ratio),
            "forced_liquidation_ratio": float(config.forced_liquidation_ratio),
            "volatility_protection": config.volatility_protection,
            "volatility_threshold": float(config.volatility_threshold)
        }
    else:
        return {"message": "No trade configuration found"}

@app.put("/api/config/trade")
async def update_trade_config(config_update: TradeConfigUpdate, 
                             current_user: User = Depends(get_current_user), 
                             db: Session = Depends(get_db)):
    """
    更新交易配置
    """
    # 检查是否已存在交易配置
    existing_config = db.query(TradeConfig).first()
    
    if existing_config:
        # 更新现有配置
        existing_config.symbol = config_update.symbol
        existing_config.cycle = config_update.cycle
        existing_config.single_amount = config_update.single_amount
        existing_config.risk_ratio = config_update.risk_ratio
        existing_config.max_risk_ratio = config_update.max_risk_ratio
        existing_config.forced_liquidation_ratio = config_update.forced_liquidation_ratio
        existing_config.volatility_protection = config_update.volatility_protection
        existing_config.volatility_threshold = config_update.volatility_threshold
    else:
        # 创建新配置
        new_config = TradeConfig(
            symbol=config_update.symbol,
            cycle=config_update.cycle,
            single_amount=config_update.single_amount,
            risk_ratio=config_update.risk_ratio,
            max_risk_ratio=config_update.max_risk_ratio,
            forced_liquidation_ratio=config_update.forced_liquidation_ratio,
            volatility_protection=config_update.volatility_protection,
            volatility_threshold=config_update.volatility_threshold
        )
        db.add(new_config)
    
    db.commit()
    return {"message": "Trade Configuration updated successfully"}

# 健康检查接口
@app.get("/health")
async def health_check():
    """
    系统健康检查接口
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "Web3Million API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)