from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.models import User

# Импортируем секретный ключ из main с обработкой ошибки
try:
    from app.main import SECRET_KEY, ALGORITHM
except ImportError:
    # Значения по умолчанию, если не удалось импортировать
    SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
    ALGORITHM = "HS256"
    print("⚠️ dependencies.py: Используются значения SECRET_KEY/ALGORITHM по умолчанию")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(
    request: Request = None,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Получить текущего пользователя из токена"""
    
    # 1. Пробуем взять токен из Depends (OAuth2PasswordBearer)
    access_token = token
    
    # 2. Если нет, пробуем из заголовка Authorization
    if not access_token and request:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            access_token = auth_header.replace("Bearer ", "")
    
    # 3. Если нет, пробуем из cookies
    if not access_token and request:
        access_token = request.cookies.get("access_token")
    
    # 4. Если нет, пробуем из query string (для WebSocket)
    if not access_token and request:
        access_token = request.query_params.get("token")
    
    # 5. Если нет токена - ошибка
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован: токен отсутствует",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 6. Декодируем токен
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен: отсутствует sub",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Недействительный токен: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 7. Получаем пользователя из БД по ID
    try:
        user_id_int = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен: некорректный ID пользователя",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
):
    """Получить текущего администратора"""
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    
    return current_user