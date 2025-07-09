from sqlalchemy import Column, String, DECIMAL, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(20), primary_key=True)
    monthly_income = Column(DECIMAL(10, 2), nullable=False)
    savings_goal = Column(Text, nullable=False)
    target_amount = Column(DECIMAL(10, 2), nullable=False)
    target_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow())

    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    merchant = Column(String(255), nullable=True)
    transaction_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    user = relationship("User", back_populates="transactions")

class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String(20), ForeignKey("users.user_id"), primary_key=True)
    preferences = Column(JSONB, default=lambda: {})
    updated_at = Column(DateTime,default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    user = relationship("User", back_populates="preferences")
