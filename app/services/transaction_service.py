from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status
from typing import List
from decimal import Decimal
from datetime import date
from config.logger import logger
from database.models import Transaction
from schemas.transaction import NaturalLanguageInput, TransactionResponse, TransactionSearch
from services.user_service import UserService
from agents.finance_crew import FinanceCrew 

class TransactionService:
    
    user_service = UserService()
    
    async def create_transaction(self, db: AsyncSession, input_data: NaturalLanguageInput) -> TransactionResponse:
        """Process natural language transaction, categorize, and store it"""
        try:

            if not await self.user_service.user_exists(db, input_data.user_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            # Parse and categorize natural language input
            finance_crew = FinanceCrew()
            parsed_data = await finance_crew.parse_transaction(input_data.text, input_data.user_id, db)
            if not parsed_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to parse transaction")

            # transactions cannot be dated before the user's signup month
            user = await self.user_service.get_user_by_id(db, input_data.user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            created_date = user.created_at.date() if hasattr(user.created_at, 'date') else user.created_at
            first_allowed_date = date(created_date.year, created_date.month, 1)
            if parsed_data.transaction_date < first_allowed_date:
                blocked_month = first_allowed_date.strftime('%B %Y')
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transactions before {blocked_month} are not allowed"
                )

            new_transaction = Transaction(
                user_id=input_data.user_id,
                amount=parsed_data.amount,
                description=input_data.text,
                category=parsed_data.category,
                merchant=parsed_data.merchant,
                transaction_date=parsed_data.transaction_date
            )
            db.add(new_transaction)
            await db.commit()
            await db.refresh(new_transaction)

            logger.info(f"Transaction created for user {input_data.user_id}: {parsed_data.amount} ({parsed_data.category})")
            return TransactionResponse.model_validate(new_transaction)

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating transaction for user {input_data.user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create transaction")

    async def search_transactions(self, db: AsyncSession, search_data: TransactionSearch) -> List[TransactionResponse]:
        """Search transactions by category, date, or amount from natural language query"""
        try:
            if not await self.user_service.user_exists(db, search_data.user_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            finance_crew= FinanceCrew()
            filters = await finance_crew.parse_search_query(search_data.query)
            if not filters:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to parse search query")

            query = select(Transaction).filter_by(user_id=search_data.user_id)
            if filters.get("category"):
                query = query.filter(Transaction.category.ilike(f"%{filters['category']}%"))
            if filters.get("date"):
                query = query.filter(Transaction.transaction_date == filters["date"])
            if filters.get("start_date") and filters.get("end_date"):
                query = query.filter(and_(
                    Transaction.transaction_date >= filters["start_date"],
                    Transaction.transaction_date <= filters["end_date"]
                ))
            if filters.get("min_amount"):
                query = query.filter(Transaction.amount >= Decimal(str(filters["min_amount"])))
            if filters.get("max_amount"):
                query = query.filter(Transaction.amount <= Decimal(str(filters["max_amount"])))

            query = query.order_by(Transaction.transaction_date.desc())
            result = await db.execute(query)
            transactions = result.scalars().all()

            logger.info(f"Found {len(transactions)} transactions for user {search_data.user_id}")
            return [TransactionResponse.model_validate(t) for t in transactions]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error searching transactions for user {search_data.user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search transactions")

    async def get_total_spent_by_period(self, db: AsyncSession, user_id: str, start_date: date, end_date: date) -> Decimal:
        """Calculate total spent in a period for analysis"""
        try:
            if not await self.user_service.user_exists(db, user_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            result = await db.execute(
                select(func.sum(Transaction.amount))
                .filter(and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date
                ))
            )
            total = result.scalar() or Decimal('0.00')

            logger.info(f"Total spent for user {user_id} from {start_date} to {end_date}: {total}")
            return total

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calculating total spent for user {user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate total spent")