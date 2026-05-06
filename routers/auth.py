from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from datetime import datetime, timedelta
from database import get_db
from models import User
from schemas import UserRegister, UserLogin, TokenResponse
import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials





security = HTTPBearer()
DEV_MODE = False
router = APIRouter(prefix="/auth", tags=["auth"])
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"


def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str):
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(username: str, role: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    data = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="帳號已存在")
    user = User(username=body.username, password=hash_password(body.password))
    db.add(user)
    await db.commit()
    token = create_token(user.username, user.role)
    return {"token": token}

@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    token = create_token(user.username, user.role)
    return {"token": token}


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if DEV_MODE:
        return {"sub": "admin", "role": "admin"}
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Token 無效")