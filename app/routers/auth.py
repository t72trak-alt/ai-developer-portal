from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets
router = APIRouter(prefix="/api/auth", tags=["auth"])
# Настройки JWT (должны совпадать с main.py)
SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# Функция хеширования пароля
def hash_password(password: str, salt: str = None) -> tuple:
    """Хеширование пароля с солью"""
    if salt is None:
        salt = secrets.token_hex(16)
    # Создаем хеш: sha256(пароль + соль)
    hash_obj = hashlib.sha256()
    hash_obj.update(f"{password}{salt}".encode('utf-8'))
    hashed_password = hash_obj.hexdigest()
    return hashed_password, salt
def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Проверка пароля"""
    test_hash, _ = hash_password(password, salt)
    return test_hash == hashed_password
def create_access_token(email: str):
    """Создание JWT токена"""
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token
# Модели
class UserCreate(BaseModel):
    email: str
    name: str
    password: str
class UserLogin(BaseModel):
    email: str
    password: str
@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли пользователь
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    # Хешируем пароль
    hashed_password, salt = hash_password(user.password)
    # Создаем нового пользователя
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        salt=salt
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": "Пользователь успешно зарегистрирован",
        "email": new_user.email,
        "name": new_user.name
    }
@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # Ищем пользователя
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    # Проверяем пароль
    if not verify_password(user.password, db_user.hashed_password, db_user.salt):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    # Создаем токен
    access_token = create_access_token(user.email)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": db_user.email,
        "name": db_user.name
    }
@router.get("/test")
async def test():
    return {"message": "Auth router работает"}
