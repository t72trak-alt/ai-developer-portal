from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

# ============================================
# СУЩЕСТВУЮЩИЕ СХЕМЫ (ОСТАВЛЯЕМ КАК ЕСТЬ)
# ============================================

class UserCreate(BaseModel):
    email: str
    name: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    content: str
    sender_id: int
    user_id: int
    is_from_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class StatisticResponse(BaseModel):
    total_users: int
    total_services: int
    total_projects: int
    total_messages: int
    total_transactions: int
    active_users: int = 0
    revenue_today: str = "0,0"
    revenue_month: str = "0,0"
    
    class Config:
        from_attributes = True

class ServiceResponse(BaseModel):
    id: int
    title: str
    icon: str
    short_description: str
    full_description: str
    features: List[str]
    technologies: List[str]
    price_range: str
    duration: str
    order_index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    user_id: int
    service_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============================================
# НОВЫЕ СХЕМЫ ДЛЯ CLIENT DETAILS
# ============================================

class ClientDetailsBase(BaseModel):
    """Базовые поля реквизитов клиента"""
    company_name: Optional[str] = None
    legal_address: Optional[str] = None
    actual_address: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    messenger_contact: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    bank_name: Optional[str] = None
    bik: Optional[str] = None
    checking_account: Optional[str] = None
    correspondent_account: Optional[str] = None
    director_name: Optional[str] = None
    director_basis: Optional[str] = None

class ClientDetailsCreate(ClientDetailsBase):
    """Создание реквизитов (все поля опциональны)"""
    pass

class ClientDetailsUpdate(ClientDetailsBase):
    """Обновление реквизитов"""
    pass

class ClientDetailsResponse(ClientDetailsBase):
    """Ответ с реквизитами клиента"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ============================================
# РАСШИРЕННЫЕ СХЕМЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
# ============================================

class UserWithDetailsResponse(UserResponse):
    """Пользователь + его реквизиты"""
    client_details: Optional[ClientDetailsResponse] = None

# ============================================
# СТАТИСТИКА ДЛЯ КАРТОЧКИ КЛИЕНТА
# ============================================

class ClientStatistics(BaseModel):
    """Статистика для карточки клиента"""
    total_messages: int
    total_projects: int
    total_transactions: int
    total_payments_sum: float