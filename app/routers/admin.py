from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import app.database as database
import app.models as models
import app.schemas as schemas
from app.dependencies import get_current_user
from sqlalchemy import func, inspect

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"]
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_admin(user: models.User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    return user

# ================ ПОЛЬЗОВАТЕЛИ ================
@router.get("/users")
async def get_all_users(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить всех пользователей"""
    check_admin(current_user)
    users = db.query(models.User).all()
    return {
        "status": "success",
        "count": len(users),
        "users": users
    }

# ================ ПРОЕКТЫ ================
@router.get("/projects")
async def get_all_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все проекты"""
    check_admin(current_user)
    projects = db.query(models.Project).all()
    return {
        "status": "success",
        "count": len(projects),
        "projects": projects
    }

# ================ КЛИЕНТЫ (CLIENT DETAILS) ================

@router.get("/clients/{user_id}")
async def get_client_details(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить реквизиты клиента по ID пользователя"""
    check_admin(current_user)
    
    client_details = db.query(models.ClientDetails).filter(
        models.ClientDetails.user_id == user_id
    ).first()
    
    if not client_details:
        # Если реквизитов нет, создаем пустые
        client_details = models.ClientDetails(user_id=user_id)
        db.add(client_details)
        db.commit()
        db.refresh(client_details)
    
    return client_details

@router.put("/clients/{user_id}")
async def update_client_details(
    user_id: int,
    details_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить реквизиты клиента"""
    check_admin(current_user)
    
    client_details = db.query(models.ClientDetails).filter(
        models.ClientDetails.user_id == user_id
    ).first()
    
    if not client_details:
        # Если реквизитов нет, создаем новые
        client_details = models.ClientDetails(user_id=user_id)
        db.add(client_details)
        db.flush()
    
    # Обновляем поля
    for field, value in details_data.items():
        if hasattr(client_details, field):
            setattr(client_details, field, value)
    
    client_details.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client_details)
    
    return client_details

@router.get("/clients/{user_id}/statistics")
async def get_client_statistics(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику для карточки клиента"""
    check_admin(current_user)
    
    # Проверяем существование пользователя
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Считаем сообщения
    total_messages = db.query(models.Message).filter(
        (models.Message.sender_id == user_id) | (models.Message.receiver_id == user_id)
    ).count()
    
    # Считаем проекты
    total_projects = db.query(models.Project).filter(
        models.Project.user_id == user_id
    ).count()
    
    # Считаем транзакции и сумму
    total_transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id
    ).count()
    
    total_payments_sum = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.status == "completed"
    ).scalar() or 0.0
    
    return {
        "total_messages": total_messages,
        "total_projects": total_projects,
        "total_transactions": total_transactions,
        "total_payments_sum": float(total_payments_sum)
    }

# ================ УСЛУГИ ================
@router.get("/services")
async def get_all_services(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все услуги"""
    check_admin(current_user)
    
    inspector = inspect(db.bind)
    if 'services' not in inspector.get_table_names():
        return {
            "status": "success",
            "count": 0,
            "services": [],
            "message": "Таблица услуг не создана"
        }
    
    services = db.query(models.Service).all()
    
    services_list = []
    for service in services:
        service_dict = {
            "id": service.id,
            "name": service.title,
            "title": service.title,
            "description": service.short_description or service.full_description,
            "short_description": service.short_description,
            "full_description": service.full_description,
            "price": service.price_range,
            "price_range": service.price_range,
            "category": "development",
            "icon": service.icon,
            "features": service.features,
            "technologies": service.technologies,
            "duration": service.duration,
            "order_index": service.order_index,
            "is_active": service.is_active,
            "created_at": service.created_at,
            "updated_at": service.updated_at
        }
        services_list.append(service_dict)
    
    return {
        "status": "success",
        "count": len(services_list),
        "services": services_list
    }

@router.post("/services")
async def create_service(
    service_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать новую услугу"""
    check_admin(current_user)
    
    inspector = inspect(db.bind)
    if 'services' not in inspector.get_table_names():
        from app.database import Base
        Base.metadata.create_all(bind=db.bind, tables=[models.Service.__table__])
    
    new_service = models.Service(
        title=service_data.get("name") or service_data.get("title", "Новая услуга"),
        icon=service_data.get("icon", "🔧"),
        short_description=service_data.get("description") or service_data.get("short_description", ""),
        full_description=service_data.get("full_description", ""),
        features=service_data.get("features", []),
        technologies=service_data.get("technologies", []),
        price_range=service_data.get("price") or service_data.get("price_range", "0"),
        duration=service_data.get("duration", "1 час"),
        order_index=service_data.get("order_index", 0),
        is_active=service_data.get("is_active", True),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    
    return {
        "status": "success",
        "message": "Услуга создана",
        "service": {
            "id": new_service.id,
            "name": new_service.title,
            "title": new_service.title,
            "description": new_service.short_description,
            "price": new_service.price_range,
            "icon": new_service.icon,
            "is_active": new_service.is_active
        }
    }

@router.put("/services/{service_id}")
async def update_service(
    service_id: int,
    service_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить услугу"""
    check_admin(current_user)
    
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    if "name" in service_data or "title" in service_data:
        service.title = service_data.get("name") or service_data.get("title", service.title)
    if "description" in service_data or "short_description" in service_data:
        service.short_description = service_data.get("description") or service_data.get("short_description", service.short_description)
    if "full_description" in service_data:
        service.full_description = service_data["full_description"]
    if "price" in service_data or "price_range" in service_data:
        service.price_range = service_data.get("price") or service_data.get("price_range", service.price_range)
    if "icon" in service_data:
        service.icon = service_data["icon"]
    if "features" in service_data:
        service.features = service_data["features"]
    if "technologies" in service_data:
        service.technologies = service_data["technologies"]
    if "duration" in service_data:
        service.duration = service_data["duration"]
    if "order_index" in service_data:
        service.order_index = service_data["order_index"]
    if "is_active" in service_data:
        service.is_active = service_data["is_active"]
    
    service.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(service)
    
    return {
        "status": "success",
        "message": "Услуга обновлена",
        "service": {
            "id": service.id,
            "name": service.title,
            "title": service.title,
            "description": service.short_description,
            "price": service.price_range,
            "icon": service.icon,
            "is_active": service.is_active
        }
    }

@router.delete("/services/{service_id}")
async def delete_service(
    service_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить услугу"""
    check_admin(current_user)
    
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    db.delete(service)
    db.commit()
    
    return {
        "status": "success",
        "message": "Услуга удалена"
    }

# ================ ТРАНЗАКЦИИ ================
@router.get("/transactions")
async def get_all_transactions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Получить все транзакции"""
    check_admin(current_user)
    
    inspector = inspect(db.bind)
    if 'transactions' not in inspector.get_table_names():
        return {
            "status": "success",
            "count": 0,
            "transactions": [],
            "message": "Таблица транзакций не создана"
        }
    
    transactions = db.query(models.Transaction).order_by(
        models.Transaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    total = db.query(models.Transaction).count()
    
    return {
        "status": "success",
        "count": len(transactions),
        "total": total,
        "transactions": transactions
    }

@router.get("/transactions/stats")
async def get_transactions_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Статистика по транзакциям"""
    check_admin(current_user)
    
    inspector = inspect(db.bind)
    if 'transactions' not in inspector.get_table_names():
        return {
            "status": "success",
            "stats": {
                "total_transactions": 0,
                "total_revenue": 0,
                "average_amount": 0,
                "last_month_revenue": 0
            }
        }
    
    total_transactions = db.query(models.Transaction).count()
    total_revenue = db.query(func.sum(models.Transaction.amount)).scalar() or 0
    average_amount = total_revenue / total_transactions if total_transactions > 0 else 0
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    last_month_revenue = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.created_at >= thirty_days_ago
    ).scalar() or 0
    
    return {
        "status": "success",
        "stats": {
            "total_transactions": total_transactions,
            "total_revenue": float(total_revenue),
            "average_amount": float(average_amount),
            "last_month_revenue": float(last_month_revenue)
        }
    }

# ================ СТАТИСТИКА ================
@router.get("/stats")
async def get_admin_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику для админ-панели"""
    check_admin(current_user)
    
    total_users = db.query(models.User).count()
    total_projects = db.query(models.Project).count()
    total_services = db.query(models.Service).count()
    
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(models.User).filter(
        models.User.created_at >= thirty_days_ago
    ).count()
    
    return {
        "status": "success",
        "stats": {
            "total_users": total_users,
            "total_projects": total_projects,
            "total_services": total_services,
            "active_users": active_users,
            "revenue": 0,
            "growth_rate": 0
        }
    }

# ================ АРХИВ ПРОЕКТОВ (ДОБАВЛЕНО) ================
@router.get("/archive/projects")
async def get_archive_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = None
):
    """Получить проекты для архива
    Категории: completed (выполненные), in_progress (в работе), pending (заявки)
    """
    check_admin(current_user)
    
    # Базовый запрос
    query = db.query(models.Project)
    
    # Фильтр по категории
    if category in ['completed', 'in_progress', 'pending']:
        query = query.filter(models.Project.status == category)
    
    projects = query.order_by(models.Project.created_at.desc()).all()
    
    # Форматируем результат
    result = []
    for project in projects:
        user = db.query(models.User).filter(models.User.id == project.user_id).first()
        
        # Русские названия категорий
        category_names = {
            'pending': 'Заявка',
            'in_progress': 'В работе',
            'completed': 'Выполнен',
            'cancelled': 'Отменён'
        }
        
        result.append({
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "category": project.status,
            "category_name": category_names.get(project.status, project.status),
            "user_id": project.user_id,
            "user_name": user.name if user else "Неизвестный",
            "created_at": project.created_at.isoformat() if project.created_at else None
        })
    
    return {
        "status": "success",
        "count": len(result),
        "projects": result
    }

@router.get("/archive/stats")
async def get_archive_stats(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику по категориям архива"""
    check_admin(current_user)
    
    stats = {
        "pending": db.query(models.Project).filter(models.Project.status == 'pending').count(),
        "in_progress": db.query(models.Project).filter(models.Project.status == 'in_progress').count(),
        "completed": db.query(models.Project).filter(models.Project.status == 'completed').count(),
        "cancelled": db.query(models.Project).filter(models.Project.status == 'cancelled').count()
    }
    stats["total"] = sum(stats.values())
    
    return {
        "status": "success",
        "stats": stats
    }

@router.put("/archive/projects/{project_id}/category")
async def change_project_category(
    project_id: int,
    category_data: dict,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Изменить категорию проекта в архиве"""
    check_admin(current_user)
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    
    new_category = category_data.get("category")
    if new_category not in ['pending', 'in_progress', 'completed', 'cancelled']:
        raise HTTPException(status_code=400, detail="Некорректная категория")
    
    project.status = new_category
    if hasattr(project, 'updated_at'):
        project.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"Проект перемещён в категорию {new_category}"
    }