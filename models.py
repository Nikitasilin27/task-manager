from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True, index=True)  # Изменено на timezone=True
    priority = Column(String, nullable=False, default="Medium")
    reminder = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, nullable=False, index=True)
