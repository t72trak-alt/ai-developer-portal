from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
# Импортируем роутер аутентификации
from app.routers import auth
app = FastAPI(title="AI Developer Portal", version="1.0")
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
@app.get("/test-api")
async def test_api():
    return {"message": "API работает", "status": "ok"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
