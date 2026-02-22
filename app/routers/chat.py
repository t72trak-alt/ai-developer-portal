from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import List
import json
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio

from app.database import SessionLocal, get_db
from app.models import Message, User

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 WebSocket подключен. Всего подключений: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"🔌 WebSocket отключен. Осталось: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Ошибка отправки сообщения: {e}")

manager = ConnectionManager()

# ========== ЭНДПОИНТ ДЛЯ ПРОВЕРКИ БД ==========
@router.get("/check-db")
async def check_db(db: Session = Depends(get_db)):
    """
    Проверить, какая БД реально используется
    """
    try:
        db_url = str(db.bind.url)
        user_count = db.query(User).count()
        users = db.query(User).all()
        
        return {
            "db_url": db_url,
            "user_count": user_count,
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "is_admin": u.is_admin
                } for u in users
            ]
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }

# ========== ТЕСТОВЫЙ ЭНДПОИНТ ДЛЯ ПРОВЕРКИ ПОЛЬЗОВАТЕЛЕЙ ==========
@router.get("/test-users")
async def test_users(db: Session = Depends(get_db)):
    """
    Тестовый эндпоинт для проверки пользователей в БД
    """
    try:
        print("\n🔍 ТЕСТОВЫЙ ЗАПРОС: ПОЛУЧЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ")
        users = db.query(User).all()
        result = {
            "count": len(users),
            "users": [
                {
                    "id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "is_admin": u.is_admin
                } for u in users
            ]
        }
        print(f"✅ Найдено пользователей: {len(users)}")
        return result
    except Exception as e:
        print(f"❌ Ошибка в test-users: {str(e)}")
        return {"error": str(e)}

@router.get("/history/{user_id}")
async def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    """
    Получить историю сообщений для конкретного пользователя
    """
    print(f"\n{'='*50}")
    print(f"🔥 ВЫЗВАНА get_chat_history ДЛЯ user_id={user_id}")
    print(f"{'='*50}")
    
    try:
        print(f"🔍 Ищем пользователя с id={user_id}...")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            print(f"❌ Пользователь с id={user_id} НЕ НАЙДЕН в БД!")
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        print(f"✅ Пользователь найден: {user.email} (админ: {user.is_admin})")
        print(f"🔍 Ищем сообщения для user_id={user_id}...")
        
        messages = db.query(Message).filter(
            (Message.sender_id == user_id) | (Message.receiver_id == user_id)
        ).order_by(Message.created_at.asc()).all()
        
        print(f"📊 Найдено сообщений: {len(messages)}")
        
        result = []
        for i, msg in enumerate(messages):
            print(f"  📝 Сообщение {i+1}: id={msg.id}, sender={msg.sender_id}, receiver={msg.receiver_id}, owner={msg.is_owner}")
            result.append({
                "id": msg.id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "is_from_admin": not msg.is_owner,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            })
        
        print(f"✅ Возвращаем {len(result)} сообщений")
        return result
        
    except HTTPException:
        print(f"⚠️ HTTP исключение: пользователь не найден")
        raise
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА в get_chat_history:")
        print(f"   Тип ошибки: {type(e).__name__}")
        print(f"   Текст ошибки: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"\n")
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории: {str(e)}")

@router.get("/stats/total")
async def get_total_messages(db: Session = Depends(get_db)):
    """
    Получить общее количество сообщений
    """
    try:
        total = db.query(Message).count()
        print(f"📊 Общее количество сообщений в БД: {total}")
        return {"total": total}
    except Exception as e:
        print(f"❌ Ошибка stats/total: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.websocket("/ws/chat/0")
async def websocket_admin_endpoint(websocket: WebSocket):
    """
    WebSocket эндпоинт для администратора (ID=0 означает админ)
    """
    print(f"\n{'='*50}")
    print(f"🔌 АДМИН ПОДКЛЮЧАЕТСЯ К WEBSOCKET")
    print(f"{'='*50}")
    
    await manager.connect(websocket)
    db = SessionLocal()
    ping_task = None
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
        print("✅ Админ подключен, приветствие отправлено")
        
        # Задача для отправки ping каждые 20 секунд
        async def send_ping():
            try:
                while True:
                    await asyncio.sleep(20)
                    try:
                        await websocket.send_json({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        })
                        print("📤 Ping отправлен")
                    except Exception as e:
                        print(f"❌ Ошибка отправки ping: {e}")
                        break
            except asyncio.CancelledError:
                print("📌 Ping задача отменена")
                raise
        
        ping_task = asyncio.create_task(send_ping())
        
        while True:
            try:
                data = await websocket.receive_text()
                print(f"📩 Получено сообщение от админа: {data[:100]}...")
                
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                # Обработка pong ответов
                if message_type == "pong":
                    print("📥 Получен pong")
                    continue
                
                if message_type == "admin_message":
                    target_user_id = message_data.get("user_id")
                    content = message_data.get("content")
                    
                    if not target_user_id or not content:
                        print("⚠️ Неполные данные сообщения")
                        continue
                    
                    print(f"📝 Сообщение для пользователя {target_user_id}: {content[:50]}...")
                    
                    try:
                        # Сохраняем сообщение в БД
                        db_message = Message(
                            content=content,
                            sender_id=1,  # ID админа
                            receiver_id=target_user_id,
                            is_owner=False,  # Админ - не владелец сообщения
                            created_at=datetime.now()
                        )
                        db.add(db_message)
                        db.commit()
                        
                        print(f"✅ Сообщение от админа СОХРАНЕНО в БД для user_id={target_user_id}")
                        print(f"   ID сообщения в БД: {db_message.id}")
                        
                        # Отправляем подтверждение админу
                        await websocket.send_json({
                            "type": "new_message",
                            "user_id": target_user_id,
                            "content": content,
                            "sender_id": 1,
                            "is_from_admin": True,
                            "created_at": datetime.now().isoformat()
                        })
                        
                        # Отправляем сообщение пользователю (если он в сети)
                        user_sent = False
                        for connection in manager.active_connections:
                            if connection != websocket:
                                try:
                                    await connection.send_json({
                                        "type": "new_message",
                                        "user_id": target_user_id,
                                        "content": content,
                                        "sender_id": 1,
                                        "is_from_admin": True,
                                        "created_at": datetime.now().isoformat()
                                    })
                                    user_sent = True
                                    print(f"📨 Сообщение от админа ДОСТАВЛЕНО пользователю {target_user_id}")
                                except Exception as e:
                                    print(f"❌ Ошибка отправки пользователю: {e}")
                        
                        if not user_sent:
                            print(f"⚠️ Пользователь {target_user_id} не в сети, сообщение сохранено в БД")
                        
                    except Exception as e:
                        db.rollback()
                        print(f"❌ ОШИБКА БД при сохранении сообщения от админа: {e}")
                        import traceback
                        traceback.print_exc()
                        
            except WebSocketDisconnect:
                print("🔌 АДМИН ОТКЛЮЧИЛСЯ")
                break
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
                continue
            except Exception as e:
                print(f"❌ Ошибка в цикле: {e}")
                import traceback
                traceback.print_exc()
                break
                
    except WebSocketDisconnect:
        print("🔌 АДМИН ОТКЛЮЧИЛСЯ")
    except Exception as e:
        print(f"❌ Ошибка в websocket_admin_endpoint: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if ping_task:
            ping_task.cancel()
        manager.disconnect(websocket)
        db.close()
        print("📁 Соединение с БД для админа закрыто")

@router.websocket("/ws/chat/{user_id}")
async def websocket_user_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket эндпоинт для обычного пользователя
    """
    print(f"\n{'='*50}")
    print(f"👤 ПОЛЬЗОВАТЕЛЬ {user_id} ПОДКЛЮЧАЕТСЯ К WEBSOCKET")
    print(f"{'='*50}")
    
    await manager.connect(websocket)
    db = SessionLocal()
    ping_task = None
    
    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        print(f"✅ Пользователь {user_id} подключен, приветствие отправлено")
        
        # Задача для отправки ping каждые 20 секунд
        async def send_ping():
            try:
                while True:
                    await asyncio.sleep(20)
                    try:
                        await websocket.send_json({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"📤 Ping отправлен пользователю {user_id}")
                    except Exception as e:
                        print(f"❌ Ошибка отправки ping: {e}")
                        break
            except asyncio.CancelledError:
                print(f"📌 Ping задача для пользователя {user_id} отменена")
                raise
        
        ping_task = asyncio.create_task(send_ping())
        
        while True:
            try:
                data = await websocket.receive_json()
                content = data.get("content", "")
                print(f"📩 Получено сообщение от пользователя {user_id}: {content[:100]}...")
                
                message_type = data.get("type")
                
                # Обработка pong ответов
                if message_type == "pong":
                    print(f"📥 Получен pong от пользователя {user_id}")
                    continue
                
                if message_type == "message":
                    if not content:
                        print("⚠️ Пустое сообщение")
                        continue
                    
                    try:
                        # Сохраняем сообщение в БД
                        message = Message(
                            sender_id=user_id,
                            receiver_id=1,  # ID админа
                            content=content,
                            is_owner=True,  # Пользователь - владелец сообщения
                            created_at=datetime.now()
                        )
                        db.add(message)
                        db.commit()
                        
                        print(f"✅ Сообщение от пользователя {user_id} СОХРАНЕНО в БД")
                        print(f"   ID сообщения в БД: {message.id}")
                        print(f"   Содержание: {content[:50]}...")
                        
                        # Подтверждение пользователю
                        await websocket.send_json({
                            "type": "new_message",
                            "user_id": user_id,
                            "content": content,
                            "sender_id": user_id,
                            "is_from_admin": False,
                            "created_at": datetime.now().isoformat()
                        })
                        
                        # Отправляем сообщение админу (если в сети)
                        admin_sent = False
                        for connection in manager.active_connections:
                            if connection != websocket:
                                try:
                                    await connection.send_json({
                                        "type": "new_message",
                                        "user_id": user_id,
                                        "content": content,
                                        "sender_id": user_id,
                                        "is_from_admin": False,
                                        "created_at": datetime.now().isoformat()
                                    })
                                    admin_sent = True
                                    print(f"📨 Сообщение от пользователя {user_id} ДОСТАВЛЕНО админу")
                                except Exception as e:
                                    print(f"❌ Ошибка отправки админу: {e}")
                        
                        if not admin_sent:
                            print("⚠️ Админ не в сети, сообщение сохранено в БД")
                        
                    except Exception as e:
                        db.rollback()
                        print(f"❌ ОШИБКА БД при сохранении сообщения от пользователя {user_id}: {e}")
                        import traceback
                        traceback.print_exc()
                        
            except WebSocketDisconnect:
                print(f"🔌 ПОЛЬЗОВАТЕЛЬ {user_id} ОТКЛЮЧИЛСЯ")
                break
            except Exception as e:
                print(f"❌ Ошибка в цикле для пользователя {user_id}: {e}")
                import traceback
                traceback.print_exc()
                break
                    
    except WebSocketDisconnect:
        print(f"🔌 ПОЛЬЗОВАТЕЛЬ {user_id} ОТКЛЮЧИЛСЯ")
    except Exception as e:
        print(f"❌ Ошибка в websocket_user_endpoint: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if ping_task:
            ping_task.cancel()
        manager.disconnect(websocket)
        db.close()
        print(f"📁 Соединение с БД для пользователя {user_id} закрыто")