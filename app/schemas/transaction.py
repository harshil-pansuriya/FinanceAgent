from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime
from typing import Optional
from uuid import UUID

# Natural language input from user
class NaturalLanguageInput(BaseModel):
    user_id: str = Field(..., max_length=20)
    text: str = Field(..., min_length=10, description="Natural language transaction: 'bought groceries of 300$ today from supermarket'")

# Parsed transaction
class TransactionParsed(BaseModel):
    amount: Decimal
    merchant: Optional[str]
    transaction_date: date
    category: str  # AI-categorized

# Transaction response
class TransactionResponse(BaseModel):
    id: UUID
    user_id: str
    amount: Decimal
    description: str
    category: str
    merchant: Optional[str]
    transaction_date: date
    created_at: datetime

    class Config:
        from_attributes = True

# Search with natural language
class TransactionSearch(BaseModel):
    user_id: str
    query: str = Field(..., description="Natural language search: 'show me grocery expenses last month' or 'transactions above 200$ this week'")