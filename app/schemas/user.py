from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, Any

# For new user registration- 3 questions
class UserRegister(BaseModel):
    monthly_income: Decimal = Field(..., gt=0, decimal_places=2)
    savings_goal: str = Field(..., min_length=5)
    target_amount: Decimal = Field(..., gt=0, decimal_places=2)
    target_date: date

# For user login
class UserLogin(BaseModel):
    user_id: str = Field(..., max_length=20)

# Response after registration/login
class UserResponse(BaseModel):
    user_id: str
    monthly_income: Decimal
    savings_goal: str
    target_amount: Decimal
    target_date: date
    created_at: datetime

    class Config:
        from_attributes = True

# For user preferences
class UserPreferences(BaseModel):
    user_id: str
    preferences: Dict[str, Any]
    updated_at: datetime
    
    class Config:
        from_attributes = True