from crewai import Crew, Process
from agents.transaction_parser import TransactionParserAgent
from agents.analysis_agent import AnalysisAgent
from services.transaction_service import TransactionService
from services.analysis import AnalysisService
from services.user_service import UserService
from schemas.transaction import NaturalLanguageInput, TransactionResponse, TransactionSearch
from schemas.analysis import FinancialInsights
from sqlalchemy.ext.asyncio import AsyncSession
from config.logger import logger
from fastapi import HTTPException, status
from typing import List

class FinanceWorkflow:
    def __init__(self):
        # Initialize agents
        self.transaction_agent = TransactionParserAgent()
        self.analysis_agent = AnalysisAgent()
        
        self.transaction_service = TransactionService()
        self.analysis_service = AnalysisService()
        self.user_service = UserService()

        self.crew = Crew(
            agents=[self.transaction_agent.transaction_agent, self.analysis_agent.agent],
            process=Process.sequential,  
            verbose=False
        )

    async def process_transaction(self, db: AsyncSession, input_data: NaturalLanguageInput) -> TransactionResponse:
        """Process a natural language transaction input and store it"""
        try:
            if not await self.user_service.user_exists(db, input_data.user_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            result = await self.transaction_service.create_transaction(db, input_data)
            
            logger.info(f"Workflow: Processed transaction for user {input_data.user_id}: {input_data.text}")
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Workflow: Error processing transaction for user {input_data.user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process transaction")

    async def search_transactions(self, db: AsyncSession, search_data: TransactionSearch) -> List[TransactionResponse]:
        """Process a natural language search query and return matching transactions"""
        try:
            if not await self.user_service.user_exists(db, search_data.user_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            results = await self.transaction_service.search_transactions(db, search_data)
            
            logger.info(f"Workflow: Processed search query for user {search_data.user_id}: {search_data.query}")
            return results

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Workflow: Error processing search query for user {search_data.user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search transactions")

    async def generate_financial_insights(self, db: AsyncSession, user_id: str, period: str = "this month") -> FinancialInsights:
        """Generate automated financial insights for a user"""
        try:
            if not await self.user_service.user_exists(db, user_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            insights = await self.analysis_service.get_financial_insights(db, user_id, period)
            
            logger.info(f"Workflow: Generated financial insights for user {user_id} for period {period}")
            return insights

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Workflow: Error generating financial insights for user {user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate financial insights")