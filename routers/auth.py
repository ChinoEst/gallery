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
import logging
from dotenv import load_dotenv
import os


#a tool for pick up token from request
#get this: headers = {"Authorization": f"Bearer {token}"}
security = HTTPBearer()


#for app.include_router(auth.router)
router = APIRouter(prefix="/auth", tags=["auth"])
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


#lock
def hash_password(password: str):
    logging.info("[INFO] hashing password...")
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


#verify
def verify_password(plain: str, hashed: str):
    logging.info("[INFO] verifying password...")
    return bcrypt.checkpw(plain.encode(), hashed.encode())


#create token for who connects
def create_token(username: str, role: str):
    logging.info("[INFO] creating token...")
    expire = datetime.utcnow() + timedelta(hours=24)
    data = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(data, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))


#register new account
#router: router = APIRouter(prefix="/auth", tags=["auth"])
#path: auth/register  <-call this,   not def register
#return format: TokenResponse
@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    #check whether user exist by SQL
    logging.info("[INFO] checking if user exists...")
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        logging.warning("[WARNING] user already exists")
        raise HTTPException(status_code=400, detail="帳號已存在")
    
    #create new user 
    user = User(username=body.username, password=hash_password(body.password))
    logging.info(f"[INFO] user {user.username} created successfully!")

    #add new user to SQLAlchemy by models.user : __tablename__ = "users"
    db.add(user)
    await db.commit()
    logging.info(f"[INFO] user {user.username} add to database successfully!")

    #give token who registers
    token = create_token(user.username, user.role)
    return {"token": token}



#path:auth/login
#type:post(add)
#return format: TokenResponse
@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password):
        logging.warning("[WARNING] failed to login")
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    token = create_token(user.username, user.role)
    logging.info(f"[INFO] user {user.username} logged in successfully!")
    return {"token": token}


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        logging.info("[INFO] verifying token...")
        payload = jwt.decode(credentials.credentials, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        logging.info("[INFO] token verification finished!")
        return payload
    except:
        logging.warning("[WARNING] invalid token")
        raise HTTPException(status_code=401, detail="Token 無效")
    

#verify admin
def verify_admin(payload = Depends(verify_token)):
    if payload["role"] != "admin":
        logging.warning(f"[WARNING] user {payload['sub']} with role {payload['role']} tried to access admin-only resource")
        raise HTTPException(status_code=403, detail="權限不足")