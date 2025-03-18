from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, func
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

Base = declarative_base()

class PriorityEnum(PyEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True, index=True)
    priority = Column(String(10), nullable=False, default=PriorityEnum.MEDIUM.value)
    reminder = Column(Boolean, default=False, index=True)
    completed = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), 
                        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    user_id = Column(Integer, nullable=False, index=True)
    
    # Создаём составной индекс для частых запросов
    __table_args__ = (
        Index('idx_user_deadline', user_id, deadline),
        Index('idx_user_completed', user_id, completed),
        Index('idx_reminder_deadline', reminder, deadline),
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title[:20]}...', user_id={self.user_id})>"

# Дополнительная модель для хранения настроек пользователя (можно использовать в будущем)
class UserSettings(Base):
    __tablename__ = "user_settings"
    
    user_id = Column(Integer, primary_key=True, index=True)
    timezone = Column(String(50), default="UTC")
    reminder_time = Column(Integer, default=60)  # За сколько минут до дедлайна напоминать
    reminder_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), 
                        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, timezone='{self.timezone}')>"
