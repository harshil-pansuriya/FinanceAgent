from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List, Dict
from config.logger import logger
from database.models import Transaction
from schemas.user import UserResponse
from schemas.analysis import FinancialInsights, SpendingAnalysis, CategorySpending, Recommendation
from services.user_service import UserService
from services.transaction_service import TransactionService
from agents.finance_crew import FinanceCrew 

class AnalysisService:
    async def get_financial_insights(self, db: AsyncSession, user_id: str, period: str = "this month") -> FinancialInsights:
        """Generate automated financial insights for a user based on transaction history and savings goals"""
        try:
            user = await UserService().get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            user_response = UserResponse.model_validate(user)

            today = date.today()
            if period == "this month":
                start_date = today.replace(day=1)
                end_date = today
            elif period == "last month":
                end_date = today.replace(day=1) - relativedelta(days=1)
                start_date = end_date.replace(day=1)
            elif period == "all time":
                # Get user creation date as start
                creation_date = user.created_at.date() if user.created_at else today.replace(day=1)
                start_date = creation_date.replace(day=1)  # Full month from day 1
                end_date = today
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid period")

            # Get spending breakdown by category
            category_spending = await self._get_category_spending(db, user_id, start_date, end_date)
            # Calculate total spent
            total_spent = await TransactionService().get_total_spent_by_period(db, user_id, start_date, end_date)
            # Get monthly trends
            monthly_trend = await self._get_monthly_trend(db, user_id, today, period)  
            # Get top merchants
            top_merchants = await self._get_top_merchants(db, user_id, start_date, end_date)
            # Calculate goal progress
            goal_progress = await self._calculate_goal_progress(user_response, total_spent, today)
            # Budget vs actual comparison
            budget_comparison = await self._budget_comparison(user_response.monthly_income, total_spent)

            spending_analysis = SpendingAnalysis(user_id=user_id, analysis_period=period,
                                    total_spent=total_spent, categories=category_spending )

            finance_crew= FinanceCrew()
            recommendations = await finance_crew.generate_recommendations(
                user_id=user_id,
                spending_analysis=spending_analysis,
                monthly_trend=monthly_trend,
                goal_progress=goal_progress,
                budget_comparison=budget_comparison,
                top_merchants=top_merchants,
                db=db
            )

            insights = FinancialInsights(
                user_id=user_id,
                spending_analysis=spending_analysis,
                recommendations=recommendations,
                generated_at=datetime.utcnow()
            )

            logger.info(f"Generated financial insights for user {user_id} for {period}")
            return insights

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating financial insights for user {user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate financial insights")

    async def _get_category_spending(self, db: AsyncSession, user_id: str, start_date: date, end_date: date) -> List[CategorySpending]:
        """Get spending breakdown by category"""
        result = await db.execute(
            select(Transaction.category, func.sum(Transaction.amount).label("total_spent"), func.avg(Transaction.amount).label("average_spend"))
            .filter(and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            ))
            .group_by(Transaction.category)
        )
        categories = [
            CategorySpending(
                category=row.category,
                total_spent=row.total_spent or Decimal('0.00'),
                average_spend=row.average_spend or Decimal('0.00')
            )
            for row in result.fetchall()
        ]
        return categories

    async def _get_monthly_trend(self, db: AsyncSession, user_id: str, today: date, period: str) -> str:
        """Get detailed monthly trend for the past few months"""
        trend_data = []
    
        if period == "this month":
            # Just current month data
            start_date = today.replace(day=1)
            month_total = await TransactionService().get_total_spent_by_period(db, user_id, start_date, today)
            categories = await self._get_category_spending(db, user_id, start_date, today)
            top_categories = sorted(categories, key=lambda x: x.total_spent, reverse=True)[:3]
            
            return f"Current month ({start_date.strftime('%B %Y')}): ${month_total} total spending"
            
        elif period == "last month":
            # Just last month data
            end_date = today.replace(day=1) - relativedelta(days=1)
            start_date = end_date.replace(day=1)
            month_total = await TransactionService().get_total_spent_by_period(db, user_id, start_date, end_date)
            
            return f"Last month ({start_date.strftime('%B %Y')}): ${month_total} total spending"
        elif period == "all time":
            # Get user creation date
            user = await UserService().get_user_by_id(db, user_id)
            creation_date = user.created_at.date() if user.created_at else today.replace(day=1)
            start_date = creation_date.replace(day=1)
            # Calculate number of months from creation to now
            months_diff = (today.year - creation_date.year) * 12 + (today.month - creation_date.month) + 1
            months_to_show = min(months_diff, 6)  # Limit to last 6 months for performance
            
            for i in range(months_to_show):
                if i == 0:
                    # Current month (partial)
                    start_date = today.replace(day=1)
                    end_date = today
                else:
                    # Previous months
                    end_date = today.replace(day=1) - relativedelta(months=i) - relativedelta(days=1)
                    start_date = end_date.replace(day=1)

                month_total = await TransactionService().get_total_spent_by_period(db, user_id, start_date, end_date)
                categories = await self._get_category_spending(db, user_id, start_date, end_date)
                top_categories = sorted(categories, key=lambda x: x.total_spent, reverse=True)[:2]
                
                trend_data.append({
                    "month": start_date.strftime("%B %Y"),
                    "total_spent": str(month_total),
                    "top_categories": [f"{cat.category}: ${cat.total_spent}" for cat in top_categories]
                })

            # Build trend string
        creation_month = creation_date.replace(day=1)
        trend_str = f"Spending trends (since {creation_month.strftime('%B %Y')}):\n"
        for month in trend_data:
            trend_str += f"- {month['month']}: ${month['total_spent']}\n"
            for cat in month.get("top_categories", [])[:2]:
                trend_str += f"  • {cat}\n"
        
        return trend_str
    
    async def _get_top_merchants(self, db: AsyncSession, user_id: str, start_date: date, end_date: date) -> List[Dict]:
        """Get top merchants by spending amount and frequency"""
        result = await db.execute(
            select(Transaction.merchant, func.sum(Transaction.amount).label("total_spent"), func.count().label("frequency"))
            .filter(and_(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.merchant != None
            ))
            .group_by(Transaction.merchant)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(5)
        )
        return [
            {"name": row.merchant, "amount": row.total_spent or Decimal('0.00'), "frequency": row.frequency}
            for row in result.fetchall()
        ]

    async def _calculate_goal_progress(self, user: UserResponse, total_spent: Decimal, today: date) -> Dict:
        """Calculate savings goal progress"""
        months_to_goal = (user.target_date - today).days / 30.0
        current_savings = user.monthly_income - total_spent 
        progress_percentage = min((current_savings / user.target_amount * 100).quantize(Decimal('0.01')), Decimal('100.00'))
        return {
            "target_savings": user.target_amount,
            "current_savings": max(current_savings, Decimal('0.00')),
            "progress_percentage": progress_percentage,
            "months_to_goal": max(round(months_to_goal, 1), 0.0)
        }

    async def _budget_comparison(self, monthly_income: Decimal, total_spent: Decimal) -> Dict:
        spending_ratio = (total_spent / monthly_income * 100).quantize(Decimal('0.01')) if monthly_income > 0 else Decimal('0.00')
        return {
            "monthly_income": monthly_income,
            "total_spent": total_spent,
            "spending_ratio": spending_ratio,
            "status": "overspending" if spending_ratio > 80 else "within budget"
        }