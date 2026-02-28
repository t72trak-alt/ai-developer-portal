from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import List, Dict
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
        self.user_connections: Dict[int, WebSocket] = {}  # user_id -> websocket
    
    async def connect(self, websocket: WebSocket, user_id: int = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket
            print(f"🔌 Пользователь {user_id} подключен. Всего: {len(self.active_connections)}")
        else:
            print(f"🔌 Подключение без user_id. Всего: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, user_id: int = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
        print(f"🔌 Отключен. Осталось: {len(self.active_connections)}")
    
    async def send_to_user(self, user_id: int, message: dict):
        """Отправить сообщение конкретному пользователю"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
                print(f"📤 Сообщение отправлено пользователю {user_id}")
                return True
            except Exception as e:
                print(f"❌ Ошибка отправки пользователю {user_id}: {e}")
                return False
        else:
            print(f"⚠️ Пользователь {user_id} не в сети")
            return False
    
    async def send_to_admin(self, message: dict):
        """Отправить сообщение админу (ID=1)"""
        return await self.send_to_user(1, message)
    
    async def broadcast(self, message: dict, exclude_user: int = None):
        """Отправить сообщение всем подключенным пользователям"""
        for user_id, connection in self.user_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.get("/check-db")
async def check_db(db: Session = Depends(get_db)):
    """Проверить, какая БД реально используется"""
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

@router.get("/test-users")
async def test_users(db: Session = Depends(get_db)):
    """Тестовый эндпоинт для проверки пользователей в БД"""
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
    """Получить историю сообщений для конкретного пользователя"""
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
            print(f"  📝 Сообщение {i+1}: id={msg.id}, sender={msg.sender_id}, receiver={msg.receiver_id}")
            result.append({
                "id": msg.id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "is_from_admin": msg.sender_id == 1,
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
    """Получить общее количество сообщений"""
    try:
        total = db.query(Message).count()
        print(f"📊 Общее количество сообщений в БД: {total}")
        return {"total": total}
    except Exception as e:
        print(f"❌ Ошибка stats/total: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.websocket("/ws/chat/0")
async def websocket_admin_endpoint(websocket: WebSocket):
    """WebSocket эндпоинт для администратора"""
    print(f"\n{'='*50}")
    print(f"🔌 АДМИН ПОДКЛЮЧАЕТСЯ К WEBSOCKET")
    print(f"{'='*50}")
    
    await manager.connect(websocket, user_id=1)
    db = SessionLocal()
    ping_task = None
    
    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": 1,
            "timestamp": datetime.now().isoformat()
        })
        print("✅ Админ подключен")
        
        async def send_ping():
            try:
                while True:
                    await asyncio.sleep(20)
                    try:
                        await websocket.send_json({"type": "ping"})
                    except:
                        break
            except asyncio.CancelledError:
                raise
        
        ping_task = asyncio.create_task(send_ping())
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "pong":
                    continue
                
                if message_type == "admin_message":
                    target_user_id = message_data.get("user_id")
                    content = message_data.get("content")
                    message_id = message_data.get("message_id")
                    
                    if not target_user_id or not content:
                        continue
                    
                    print(f"📨 Админ -> Пользователь {target_user_id}: {content}")
                    
                    # Сохраняем сообщение
                    db_message = Message(
                        content=content,
                        sender_id=1,
                        receiver_id=target_user_id,
                        created_at=datetime.now()
                    )
                    db.add(db_message)
                    db.commit()
                    db.refresh(db_message)
                    
                    print(f"💾 Сообщение сохранено в БД, id={db_message.id}")
                    
                    # Формируем сообщение для отправки
                    message_response = {
                        "type": "new_message",
                        "message_id": message_id or str(db_message.id),
                        "user_id": target_user_id,
                        "content": content,
                        "sender_id": 1,
                        "is_from_admin": True,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Отправляем админу (подтверждение)
                    await websocket.send_json(message_response)
                    print(f"📤 Подтверждение отправлено админу")
                    
                    # Отправляем пользователю, если он онлайн
                    sent = await manager.send_to_user(target_user_id, message_response)
                    if sent:
                        print(f"📤 Сообщение доставлено пользователю {target_user_id}")
                    else:
                        print(f"⏸️ Пользователь {target_user_id} не в сети, сообщение сохранено в БД")
                    
            except WebSocketDisconnect:
                print("❌ WebSocket админа отключен")
                break
            except Exception as e:
                print(f"❌ Ошибка в обработчике админа: {e}")
                import traceback
                traceback.print_exc()
                break
                    
    finally:
        if ping_task:
            ping_task.cancel()
        manager.disconnect(websocket, user_id=1)
        db.close()
        print("🔌 Ресурсы освобождены")

@router.websocket("/ws/chat/{user_id}")
async def websocket_user_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket эндпоинт для обычного пользователя"""
    print(f"\n{'='*50}")
    print(f"👤 ПОЛЬЗОВАТЕЛЬ {user_id} ПОДКЛЮЧАЕТСЯ К WEBSOCKET")
    print(f"{'='*50}")
    
    await manager.connect(websocket, user_id=user_id)
    db = SessionLocal()
    ping_task = None
    
    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        print(f"✅ Пользователь {user_id} подключен")
        
        async def send_ping():
            try:
                while True:
                    await asyncio.sleep(20)
                    try:
                        await websocket.send_json({"type": "ping"})
                    except:
                        break
            except asyncio.CancelledError:
                raise
        
        ping_task = asyncio.create_task(send_ping())
        
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "pong":
                    continue
                
                if message_type == "message":
                    content = message_data.get("content", "")
                    message_id = message_data.get("message_id")
                    
                    if not content:
                        continue
                    
                    print(f"📨 Пользователь {user_id} -> Админ: {content}")
                    
                    # Сохраняем сообщение
                    message = Message(
                        sender_id=user_id,
                        receiver_id=1,
                        content=content,
                        created_at=datetime.now()
                    )
                    db.add(message)
                    db.commit()
                    db.refresh(message)
                    
                    print(f"💾 Сообщение сохранено в БД, id={message.id}")
                    
                    # Формируем сообщение для отправки
                    message_response = {
                        "type": "new_message",
                        "message_id": message_id or str(message.id),
                        "user_id": user_id,
                        "content": content,
                        "sender_id": user_id,
                        "is_from_admin": False,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Отправляем пользователю (подтверждение)
                    await websocket.send_json(message_response)
                    print(f"📤 Подтверждение отправлено пользователю {user_id}")
                    
                    # Отправляем админу
                    sent = await manager.send_to_user(1, message_response)
                    if sent:
                        print(f"📤 Сообщение доставлено админу")
                    else:
                        print(f"⏸️ Админ не в сети, сообщение сохранено в БД")
                    
            except WebSocketDisconnect:
                print(f"❌ WebSocket пользователя {user_id} отключен")
                break
            except Exception as e:
                print(f"❌ Ошибка в обработчике пользователя {user_id}: {e}")
                import traceback
                traceback.print_exc()
                break
                    
    finally:
        if ping_task:
            ping_task.cancel()
        manager.disconnect(websocket, user_id=user_id)
        db.close()
        print(f"🔌 Ресурсы для пользователя {user_id} освобождены")