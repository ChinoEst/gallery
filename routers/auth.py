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




#a tool for pick up token from request
#get this: headers = {"Authorization": f"Bearer {token}"}
security = HTTPBearer()

DEV_MODE = False

#for app.include_router(auth.router)
router = APIRouter(prefix="/auth", tags=["auth"])
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"


#lock
def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


#verify
def verify_password(plain: str, hashed: str):
    return bcrypt.checkpw(plain.encode(), hashed.encode())


#create token for who connects
def create_token(username: str, role: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    data = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


#register new account
#router: router = APIRouter(prefix="/auth", tags=["auth"])
#path: auth/register  <-call this,   not def register
#return format: TokenResponse
@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    #check whether user exist by SQL
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="帳號已存在")
    
    #create new user 
    user = User(username=body.username, password=hash_password(body.password))

    #add new user to SQLAlchemy by models.user : __tablename__ = "users"
    db.add(user)
    await db.commit()

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