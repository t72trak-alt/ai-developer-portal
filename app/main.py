from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from .database import get_db
from .models import User
# Импортируем роутер аутентификации
from app.routers import auth
app = FastAPI(title="AI Developer Portal", version="1.0")# JWT настройки
SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)
    db = next(get_db())
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
# Подключаем роутер аутентификации
app.include_router(auth.router)
# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    services = [
        {
            "icon": "🎯",
            "title": "Промпт-инжиниринг",
            "items": [
                "Создание и оптимизация промптов для текста, изображений, аудио, видео",
                "Разработка контекстных систем для ИИ-ассистентов",
                "Интеграция с ChatGPT, Claude, Gemini, YandexGPT и др."
            ]
        },
        {
            "icon": "🤖",
            "title": "Разработка ИИ-решений",
            "items": [
                "ИИ-ассистенты и чат-боты",
                "Мультиагентные системы и автономные агенты",
                "MVP ИИ-продуктов 'под ключ'"
            ]
        },
        {
            "icon": "🔧",
            "title": "Интеграция ИИ в бизнес",
            "items": [
                "Внедрение ИИ в CRM (AmoCRM), мессенджеры, соцсети",
                "Автоматизация маркетинга, продаж и поддержки",
                "Создание систем аналитики на основе ИИ"
            ]
        },
        {
            "icon": "📊",
            "title": "Автоматизация бизнес-процессов",
            "items": [
                "Аудит и поиск точек для автоматизации",
                "Создание ИИ-инструментов для HR (прескрининг резюме)",
                "Анализ звонков, генерация контента"
            ]
        }
    ]
    portfolio = [
        {
            "title": "Illustraitor AI",
            "description": "Chrome-расширение для генерации изображений через DALL-E 3",
            "metrics": "15+ стилей генерации, 99% uptime",
            "link": "https://illustraitor-ai-v2.onrender.com"
        },
        {
            "title": "SMM-эксперт с ИИ",
            "description": "Автоматизация ведения соцсетей (ВКонтакте)",
            "metrics": "Снижение времени с 4 часов до 15 минут в день",
            "link": "#"
        }
    ]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services,
        "portfolio": portfolio
    })
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.name,
        "created_at": current_user.created_at
    }
@app.get("/test-api")
async def test_api():
    return {"message": "API работает", "status": "ok"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


