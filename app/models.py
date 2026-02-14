from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    salt = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    projects = relationship("Project", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    client_details = relationship("ClientDetails", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    icon = Column(String(50))
    short_description = Column(String(300))
    full_description = Column(Text)
    features = Column(JSON)
    technologies = Column(JSON)
    price_range = Column(String(100))
    duration = Column(String(100))
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    projects = relationship("Project", back_populates="service")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String, default="pending")
    user_id = Column(Integer, ForeignKey("users.id"))
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", back_populates="projects")
    service = relationship("Service", back_populates="projects")
    transactions = relationship("Transaction", back_populates="project")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_owner = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # <--- ИСПРАВЛЕНО: было project_id
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    amount = Column(Integer)
    currency = Column(String, default="RUB")
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", back_populates="transactions")
    project = relationship("Project", back_populates="transactions")

# НОВАЯ МОДЕЛЬ: ClientDetails
class ClientDetails(Base):
    """Детальная информация о клиенте (реквизиты)"""
    __tablename__ = "client_details"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Юридическая информация
    company_name = Column(String, nullable=True)  # Название компании
    legal_address = Column(String, nullable=True)  # Юридический адрес
    actual_address = Column(String, nullable=True)  # Фактический адрес
    contact_phone = Column(String, nullable=True)  # Контактный телефон
    contact_email = Column(String, nullable=True)  # Контактный email (может отличаться от логина)
    messenger_contact = Column(String, nullable=True)  # Контакт в мессенджере
    
    # Налоговые реквизиты
    inn = Column(String, nullable=True)  # ИНН
    kpp = Column(String, nullable=True)  # КПП
    ogrn = Column(String, nullable=True)  # ОГРН
    
    # Банковские реквизиты
    bank_name = Column(String, nullable=True)  # Название банка
    bik = Column(String, nullable=True)  # БИК
    checking_account = Column(String, nullable=True)  # Расчетный счет
    correspondent_account = Column(String, nullable=True)  # Корреспондентский счет
    
    # Руководитель
    director_name = Column(String, nullable=True)  # ФИО руководителя
    director_basis = Column(String, nullable=True)  # Действует на основании
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем
    user = relationship("User", back_populates="client_details")
    
    def __repr__(self):
        return f"<ClientDetails for user {self.user_id}>"