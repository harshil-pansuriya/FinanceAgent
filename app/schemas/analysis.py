from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List
from datetime import datetime

# Category spending summary
class CategorySpending(BaseModel):
    category: str
    total_spent: Decimal
    average_spend: Decimal

# Analysis response (after 1 week/month)
class SpendingAnalysis(BaseModel):
    user_id: str
    analysis_period: str  # "1 week", "1 month"
    total_spent: Decimal
    categories: List[CategorySpending]

# AI recommendation
class Recommendation(BaseModel):
    text: str
    category: str
    priority: str  # "high", "medium", "low"

# Complete financial insights
class FinancialInsights(BaseModel):
    user_id: str
    spending_analysis: SpendingAnalysis
    recommendations: List[Recommendation]
    generated_at: datetime

# Natural language analysis request
class AnalysisRequest(BaseModel):
    user_id: str
    query: str = Field(..., description="Natural language: 'show my spending analysis for last week' or 'give recommendations for this month'")