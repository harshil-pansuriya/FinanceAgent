from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.analysis import Recommendation, SpendingAnalysis
from config.setting import Config
from config.logger import logger
from prompts.prompt import RECOMMENDATION_PROMPT
from fastapi import HTTPException, status
from typing import List, Dict
import json
import re

class AnalysisAgent:
    def __init__(self):
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=Config.GEMINI_API_KEY,
                temperature=0.3  
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize AI model")

        self.agent = Agent(
            role="Financial Analyst",
            goal="Generate personalized financial recommendations based on spending analysis and user goals",
            backstory="Expert in financial analysis, skilled at identifying spending patterns and providing actionable budget optimization advice",
            llm=self.llm,
            verbose=False
        )
        self.crew = Crew(
            agents=[self.agent],
            tasks=[],
            verbose=False
        )

        self.recommendation_prompt = PromptTemplate(
            input_variables=["user_id", "spending_analysis", "monthly_trend", "goal_progress", "budget_comparison", "top_merchants"],
            template=RECOMMENDATION_PROMPT
        )

    async def generate_recommendations(
        self,
        user_id: str,
        spending_analysis: SpendingAnalysis,
        monthly_trend: str,
        goal_progress: Dict,
        budget_comparison: Dict,
        top_merchants: List[Dict],
        db: AsyncSession = None  
    ) -> List[Recommendation]:
        """Generate financial recommendations using CrewAI"""
        try:
            spending_analysis_json = json.dumps(spending_analysis.dict(), default=str)
            goal_progress_json = json.dumps(goal_progress, default=str)
            budget_comparison_json = json.dumps(budget_comparison, default=str)
            top_merchants_json = json.dumps(top_merchants, default=str)

            task = Task(
                description=self.recommendation_prompt.format(
                    user_id=user_id,
                    spending_analysis=spending_analysis_json,
                    monthly_trend=monthly_trend,
                    goal_progress=goal_progress_json,
                    budget_comparison=budget_comparison_json,
                    top_merchants=top_merchants_json
                ),
                agent=self.agent,
                expected_output="JSON array of recommendations with text, category, and priority"
            )

            self.crew.tasks = [task]
            result = await self.crew.kickoff_async()

            try:
                
                result_str = str(result)
                json_match = re.search(r'\[\s*\{.*\}\s*\]', result_str, re.DOTALL)
                if json_match:
                    result_str = json_match.group()
                
                recommendations = json.loads(result_str)
                if not isinstance(recommendations, list):
                    raise ValueError("Expected a list of recommendations")
                
                validated = [
                    Recommendation(
                        text=r["text"],
                        category=r["category"],
                        priority=r["priority"]
                    )
                    for r in recommendations
                    if isinstance(r, dict) and "text" in r and "category" in r and "priority" in r
                ]
                logger.info(f"Generated {len(validated)} recommendations for user {user_id}")
                return validated
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Invalid recommendation format for user {user_id}: {e}")
                return []

        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {e}")
            return []