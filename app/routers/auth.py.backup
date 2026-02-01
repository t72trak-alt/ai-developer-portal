from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import User
router = APIRouter(prefix="/api/auth", tags=["authentication"])
# Модели данных
class UserRegister(BaseModel):
    email: str
    name: str
    password: str
class UserLogin(BaseModel):
    email: str
    password: str
@router.post("/register")
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    # Простая проверка - пользователь уже существует?
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        return {"error": "Пользователь уже существует"}
    # Простая версия без хеширования (только для теста)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=user_data.password  # В реальном приложении нужно хешировать!
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Пользователь создан", "user_id": new_user.id}
@router.post("/login")
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or user.hashed_password != login_data.password:
        return {"error": "Неверные учетные данные"}
    return {"message": "Вход успешен", "user_id": user.id}
@router.get("/test")
async def test():
    return {"message": "Auth работает"}
