from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
import jwt
from datetime import datetime, timedelta
from app.database import get_db
from app.models import User
from app.routers import auth, chat, projects, admin, services, stats
from app.dependencies import get_current_user
import os
import mimetypes
import urllib.parse

app = FastAPI(title="AI Developer Portal", version="1.0")

# ========== CORS для WebSocket ==========
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# ========================================

SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ========== ПОДКЛЮЧЕНИЕ РОУТЕРОВ ==========
app.include_router(auth.router)      # /api/auth/*
app.include_router(chat.router)       # /api/chat/*
app.include_router(projects.router)   # /api/projects/*
app.include_router(admin.router)      # /api/admin/*
app.include_router(services.router)   # /api/services/*
app.include_router(stats.router)      # /api/stats/*
# ==========================================

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ========== ЭНДПОЙНТЫ ДЛЯ РАБОТЫ С ФАЙЛАМИ ДОГОВОРОВ ==========

# База данных договоров с информацией о доступных форматах
CONTRACTS_DB = {
    1: {
        "id": 1,
        "number": "ДОГ-2025-001",
        "name": "Разработка веб-портала",
        "client": "ООО \"ТехноПром\"",
        "date": "2025-01-15",
        "amount": 450000,
        "original_file": "ДОГ-2025-001.txt",
        "available_formats": ["txt", "docx", "pdf", "xlsx"]
    },
    2: {
        "id": 2,
        "number": "ДОГ-2025-042",
        "name": "Мобильное приложение",
        "client": "ИП Иванов А.А.",
        "date": "2025-02-10",
        "amount": 780000,
        "original_file": "ДОГ-2025-042.txt",
        "available_formats": ["txt", "docx", "pdf", "xlsx"]
    },
    3: {
        "id": 3,
        "number": "ДОГ-2024-128",
        "name": "Автоматизация отчетности",
        "client": "АО \"СтройИнвест\"",
        "date": "2024-11-05",
        "amount": 320000,
        "original_file": "ДОГ-2024-128.txt",
        "available_formats": ["txt", "docx", "pdf", "xlsx"]
    },
    4: {
        "id": 4,
        "number": "ДОГ-2025-089",
        "name": "SEO-оптимизация",
        "client": "ООО \"МедиаГрупп\"",
        "date": "2025-03-01",
        "amount": 180000,
        "original_file": "ДОГ-2025-089.txt",
        "available_formats": ["txt", "docx", "pdf", "xlsx"]
    },
    5: {
        "id": 5,
        "number": "ДОГ-2024-256",
        "name": "Разработка LMS",
        "client": "ЧУ ДПО \"Образование+\"",
        "date": "2024-09-20",
        "amount": 950000,
        "original_file": "ДОГ-2024-256.txt",
        "available_formats": ["txt", "docx", "pdf", "xlsx"]
    },
    6: {
        "id": 6,
        "number": "ДОГ-2025-103",
        "name": "Система управления складом",
        "client": "ООО \"ЛогистикПро\"",
        "date": "2025-03-15",
        "amount": 1250000,
        "original_file": "ДОГ-2025-103.txt",
        "available_formats": ["txt", "docx", "pdf", "xlsx"]
    }
}

@app.get("/api/contracts/list")
async def get_contracts_list():
    """Получить список всех договоров"""
    return list(CONTRACTS_DB.values())

@app.get("/api/contracts/info/{contract_id}")
async def get_contract_info(contract_id: int):
    """Получить информацию о конкретном договоре"""
    if contract_id not in CONTRACTS_DB:
        raise HTTPException(status_code=404, detail="Contract not found")
    return CONTRACTS_DB[contract_id]

@app.get("/api/contracts/file/{contract_id}")
async def get_contract_file(contract_id: int, format: str = None):
    """
    Эндпоинт для получения файла договора
    - contract_id: ID договора
    - format: желаемый формат (txt, docx, pdf, xlsx) - если не указан, вернёт оригинал
    Файлы открываются в РОДНОМ ФОРМАТЕ (Word, PDF, Excel)
    """
    print(f"=== ЗАПРОС ФАЙЛА: contract_id={contract_id}, format={format} ===")
    
    if contract_id not in CONTRACTS_DB:
        print(f"❌ Договор {contract_id} не найден в БД")
        raise HTTPException(status_code=404, detail="Contract not found")
    
    contract = CONTRACTS_DB[contract_id]
    print(f"✅ Договор найден: {contract['number']}")
    
    # Определяем какой файл отдавать
    if format and format in contract["available_formats"]:
        # Формируем имя файла в запрошенном формате
        base_name = contract["original_file"].replace('.txt', '')
        filename = f"{base_name}.{format}"
        print(f"🔍 Ищем файл в формате {format}: {filename}")
        
        possible_paths = [
            os.path.join("app", "static", "contracts", filename),
            os.path.join("static", "contracts", filename)
        ]
    else:
        # Отдаём оригинальный файл
        filename = contract["original_file"]
        print(f"🔍 Ищем оригинальный файл: {filename}")
        possible_paths = [
            os.path.join("app", "static", "contracts", filename),
            os.path.join("static", "contracts", filename)
        ]
    
    # Ищем файл
    for file_path in possible_paths:
        print(f"  Проверяем путь: {file_path}")
        if os.path.exists(file_path):
            print(f"✅ Файл НАЙДЕН: {file_path}")
            print(f"  Размер файла: {os.path.getsize(file_path)} байт")
            
            # Определяем media type на основе расширения для родного формата
            ext = os.path.splitext(file_path)[1].lower()
            
            # Правильные MIME-типы для каждого формата
            media_types = {
                '.txt': 'text/plain; charset=utf-8',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.pdf': 'application/pdf',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            media_type = media_types.get(ext, 'application/octet-stream')
            
            # Для всех файлов используем inline (открытие в браузере/приложении)
            disposition = 'inline'
            
            # Кодируем имя файла для корректной обработки русских символов
            filename_display = os.path.basename(file_path)
            filename_encoded = urllib.parse.quote(filename_display)
            
            print(f"📤 Отправляем файл: {filename_display}")
            print(f"  Media type: {media_type} (родной формат)")
            print(f"  Disposition: {disposition} (открытие в приложении)")
            
            # Возвращаем файл с правильными заголовками
            return FileResponse(
                path=file_path,
                filename=filename_display,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"{disposition}; filename*=UTF-8''{filename_encoded}"
                }
            )
    
    # Если файл не найден
    print(f"❌ Файл НЕ НАЙДЕН ни по одному пути")
    raise HTTPException(status_code=404, detail=f"File not found for contract {contract_id} in format {format or 'original'}")

@app.get("/api/contracts/formats/{contract_id}")
async def get_available_formats(contract_id: int):
    """Получить список доступных форматов для договора"""
    if contract_id not in CONTRACTS_DB:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Проверяем, какие форматы реально существуют
    contract = CONTRACTS_DB[contract_id]
    available_formats = []
    
    for format in contract["available_formats"]:
        base_name = contract["original_file"].replace('.txt', '')
        filename = f"{base_name}.{format}"
        
        # Проверяем в разных папках
        possible_paths = [
            os.path.join("app", "static", "contracts", filename),
            os.path.join("static", "contracts", filename)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                available_formats.append(format)
                break
    
    return {
        "contract_id": contract_id,
        "contract_number": contract["number"],
        "available_formats": available_formats
    }

# ============================================================

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    services_list = [
        {
            "icon": "🤖",
            "title": "AI-разработка",
            "items": [
                "Интеграция с языковыми моделями для чатов, ассистентов, ботов, игр",
                "Создание умных агентов для веб-приложений",
                "Взаимодействие с ChatGPT, Claude, Gemini, YandexGPT и др."
            ]
        },
        {
            "icon": "💻",
            "title": "Разработка веб-приложений",
            "items": [
                "Веб-приложения с ИИ-функциями",
                "Полный цикл разработки: от идеи до внедрения",
                "MVP ИИ-продуктов 'под ключ'"
            ]
        },
        {
            "icon": "🏢",
            "title": "Интеграция ИИ в бизнес",
            "items": [
                "Внедрение ИИ в CRM (AmoCRM), мессенджеры, соцсети",
                "Автоматизация маркетинга, продаж и поддержки",
                "Создание систем аналитики на основе ИИ"
            ]
        },
        {
            "icon": "⚙️",
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
            "description": "Chrome-расширение для генерации иллюстраций через DALL-E 3",
            "metrics": "15+ тысяч пользователей, 99% uptime",
            "link": "https://illustraitor-ai-v2.onrender.com"
        },
        {
            "title": "SMM-эксперт с ИИ",
            "description": "Автоматизация создания контента (тестирование)",
            "metrics": "Ускорение работы в 4 раза: с 15 часов до 1 часа в день",
            "link": "#"
        }
    ]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services_list,
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
    try:
        # ========== ИСПРАВЛЕНИЕ: Проверяем cookie ==========
        token = request.cookies.get("access_token")
        if not token:
            # Если нет cookie, пробуем заголовок Authorization
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        if not token:
            # Нет токена - редирект на логин
            return RedirectResponse(url="/login")
        
        # Декодируем токен вручную
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            if not user_id:
                return RedirectResponse(url="/login")
            
            # Получаем пользователя из БД
            db = next(get_db())
            user = db.query(User).filter(User.id == int(user_id)).first()
            db.close()
            
            if not user:
                return RedirectResponse(url="/login")
            
            # Всё хорошо - показываем личный кабинет
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "is_admin": user.is_admin
                }
            })
            
        except jwt.InvalidTokenError:
            return RedirectResponse(url="/login")
        except Exception as e:
            print(f"Ошибка в dashboard: {e}")
            return RedirectResponse(url="/login")
            
    except Exception as e:
        print(f"Критическая ошибка в dashboard: {e}")
        return RedirectResponse(url="/login")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    try:
        # ========== ИСПРАВЛЕНИЕ: Проверяем cookie ==========
        token = request.cookies.get("access_token")
        if not token:
            # Если нет cookie, пробуем получить из заголовка Authorization
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
        
        if not token:
            # Нет токена - редирект на логин
            return RedirectResponse(url="/login")
        
        # Декодируем токен вручную
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            
            if not user_id:
                return RedirectResponse(url="/login")
            
            # Получаем пользователя из БД
            db = next(get_db())
            user = db.query(User).filter(User.id == int(user_id)).first()
            db.close()
            
            if not user:
                return RedirectResponse(url="/login")
            
            if not user.is_admin:
                return RedirectResponse(url="/dashboard")
            
            # Всё хорошо - показываем админку
            return templates.TemplateResponse("admin.html", {
                "request": request,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "is_admin": user.is_admin
                }
            })
        except jwt.InvalidTokenError:
            return RedirectResponse(url="/login")
        except Exception as e:
            print(f"Ошибка в admin_page: {e}")
            return RedirectResponse(url="/login")
            
    except Exception as e:
        print(f"Критическая ошибка в admin_page: {e}")
        return RedirectResponse(url="/login")

@app.get("/test-api")
async def test_api():
    return {"message": "API работает", "status": "ok"}

# Дополнительные страницы
@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):
    return templates.TemplateResponse("contacts.html", {"request": request})

# ========== WebSocket для тестирования ==========
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

@app.websocket("/test-ws")
async def test_websocket(websocket: WebSocket):
    """
    Простой тестовый WebSocket endpoint
    """
    await websocket.accept()
    try:
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "status": "connected",
            "message": "WebSocket работает!",
            "timestamp": datetime.now().isoformat()
        })
        # Ожидаем сообщения от клиента
        while True:
            data = await websocket.receive_text()
            # Возвращаем эхо
            await websocket.send_json({
                "echo": data,
                "timestamp": datetime.now().isoformat(),
                "received": True
            })
    except WebSocketDisconnect:
        print("Клиент отключился от тестового WebSocket")

@app.get("/ws-test")
async def websocket_test_page(request: Request):
    """
    Страница для тестирования WebSocket
    """
    return templates.TemplateResponse("websocket_test.html", {"request": request})
# =================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)