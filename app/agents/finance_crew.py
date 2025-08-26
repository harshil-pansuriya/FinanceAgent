from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional, List
import json
import re
from config.setting import Config
from config.logger import logger
from prompts.prompt import TRANSACTION_PARSE_PROMPT, TRANSACTION_CATEGORIZATION_PROMPT, SEARCH_PARSE_PROMPT, RECOMMENDATION_PROMPT
from services.user_service import UserService
from schemas.transaction import TransactionParsed
from schemas.analysis import Recommendation, SpendingAnalysis

class FinanceCrew:
    def __init__(self):
        # LLM Configuration
        self.crewai_llm = ChatGroq(
            model="groq/llama-3.3-70b-versatile",  # Fixed model name
            api_key=Config.groq_api_key,
            temperature=0.1,
        )

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",  # Fixed model name
            api_key=Config.groq_api_key,
            temperature=0.1,
        )

        # Transaction Parser Agent
        self.transaction_agent = Agent(
            role="Transaction Parser",
            goal="Extract amount, merchant and date from natural language transaction input",
            backstory="Expert at parsing financial transactions using user-specific preferences",
            llm=self.crewai_llm,
            verbose=False,
            allow_delegation=True,  
            max_retry_limit=2 
        )

        self.categorizer_agent = Agent(
            role="Transaction Categorizer",
            goal="Categorize transactions based on parsed data and user-defined categories",
            backstory="You are an expert in financial categorization. You analyze transaction details and merchant information to assign appropriate spending categories based on user preferences and spending patterns.",
            llm=self.crewai_llm,
            verbose=False,
            max_retry_limit=2
        )
        # Recommendation Agent
        self.recommendation_agent = Agent(
            role="Financial Recomemendation Specialist",
            goal="Generate personalized financial recommendations based on spending analysis and user goals",
            backstory="You are a certified financial advisor specializing in personalized recommendations. You analyze spending patterns and generate actionable advice to help users optimize their finances.",
            llm=self.crewai_llm,
            verbose=False
        )

        # Prompts
        self.transaction_prompt = PromptTemplate(
            input_variables=["input_text", "current_date"],
            template=TRANSACTION_PARSE_PROMPT 
        )

        self.transaction_categorization_prompt = PromptTemplate(
            input_variables=["input_text", "current_date", "categories", "parsed_data"],
            template=TRANSACTION_CATEGORIZATION_PROMPT
        )
        
        self.search_prompt = PromptTemplate(
            input_variables=["query", "current_date"],
            template=SEARCH_PARSE_PROMPT
        )

        self.recommendation_prompt = PromptTemplate(
            input_variables=["user_id", "spending_analysis", "monthly_trend", "goal_progress", "budget_comparison", "top_merchants"],
            template=RECOMMENDATION_PROMPT
        )

    async def parse_transaction(self, input_text: str, user_id: str, db: AsyncSession) -> Optional[TransactionParsed]:
        """Parse and categorize natural language transaction input using CrewAI"""
        try:
            # Fetch user preferences
            user_prefs = await UserService().get_user_preferences(db, user_id)
            categories = (
                user_prefs.preferences.get("default_categories", ["Food", "Transportation", "Entertainment", "Shopping", "Bills"])
                if user_prefs
                else ["Food", "Transportation", "Entertainment", "Shopping", "Bills"]
            )

            # Create task
            current_date = date.today().isoformat()
            parse_task = Task(
                description=self.transaction_prompt.format(
                    input_text=input_text,
                    current_date=current_date,
                ),
                agent=self.transaction_agent,
                expected_output="Valid JSON with amount (decimal), merchant (string or null), transaction_date (YYYY-MM-DD), category (string)"
            )
            
            categorize_task = Task(
                description=self.transaction_categorization_prompt.format(
                    input_text=input_text,
                    current_date=current_date,
                    categories=categories,
                    parsed_data=parse_task.output
                ),
                agent=self.transaction_agent,
                expected_output="Complete JSON with amount, merchant, transaction_date, and category",
                context=[parse_task]  # Sequential dependency
            )
            crew = Crew(
                agents=[self.transaction_agent, self.categorizer_agent],
                tasks=[parse_task, categorize_task],
                process=Process.sequential,
                verbose=False
            )
            result = await crew.kickoff_async()

            json_data = self._extract_json(str(result))
            if not json_data:
                return None

            category = json_data.get("category", "Other")
            if category not in categories:
                logger.warning(f"Invalid category '{category}' for transaction: {input_text}. Defaulting to 'Other'.")
                category = "Other"

            parsed = TransactionParsed(
                amount=Decimal(str(json_data.get('amount', 0))),
                merchant=json_data.get('merchant') if json_data.get('merchant') != 'null' else None,
                transaction_date=datetime.strptime(json_data.get('transaction_date', current_date), '%Y-%m-%d').date(),
                category=category
            )
            logger.info(f"Parsed and categorized transaction for user {user_id}: {input_text} -> {category}")
            return parsed

        except Exception as e:
            logger.error(f"Error parsing transaction input '{input_text}' for user {user_id}: {e}")
            return None

    async def parse_search_query(self, query: str) -> Dict:
        """Parse natural language search query into filters using LLM"""
        try:
            current_date = date.today().isoformat()
            prompt = self.search_prompt.format(query=query, current_date=current_date)
            response = await self.llm.ainvoke(prompt)
            json_data = self._extract_json(str(response.content))
            if not json_data:
                return {}

            cleaned = self._clean_filters(json_data)
            logger.info(f"Parsed search query: {query}")
            return cleaned

        except Exception as e:
            logger.error(f"Error parsing search query '{query}': {e}")
            return {}

    async def generate_recommendations(self,
        user_id: str,
        spending_analysis: SpendingAnalysis,
        monthly_trend: str,
        goal_progress: Dict,
        budget_comparison: Dict, 
        top_merchants: List[Dict],
        db: AsyncSession = None) -> List[Recommendation]:
        """Generate financial recommendations"""
        try:
            spending_analysis_json = json.dumps(spending_analysis.dict(), default=str)
            goal_progress_json = json.dumps(goal_progress, default=str)
            budget_comparison_json = json.dumps(budget_comparison, default=str)
            top_merchants_json = json.dumps(top_merchants, default=str)

            recommendation_task = Task(
                description=self.recommendation_prompt.format(
                    user_id=user_id,
                    spending_analysis=spending_analysis_json,
                    monthly_trend=monthly_trend,
                    goal_progress=goal_progress_json,
                    budget_comparison=budget_comparison_json,
                    top_merchants=top_merchants_json
                ),
                agent=self.recommendation_agent,
                expected_output="JSON array of recommendations with text, category, and priority"
            )

            crew = Crew(
                agents=[self.recommendation_agent],
                tasks=[recommendation_task],
                process=Process.sequential,
                verbose=False
            )
            result = await crew.kickoff_async()

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

    def _extract_json(self, text: str) -> Optional[Dict]:
        try:
            json_match = re.search(r'\{[^{}]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            return None
        except json.JSONDecodeError:
            return None

    def _clean_filters(self, filters: Dict) -> Dict:
        valid_keys = {"category", "date", "start_date", "end_date", "min_amount", "max_amount"}
        cleaned = {k: v for k, v in filters.items() if k in valid_keys}

        # Convert and validate dates
        if cleaned.get("date"):
            cleaned["date"] = date.fromisoformat(cleaned["date"])
        if cleaned.get("start_date"):
            cleaned["start_date"] = date.fromisoformat(cleaned["start_date"])
        if cleaned.get("end_date"):
            cleaned["end_date"] = date.fromisoformat(cleaned["end_date"])
            if cleaned.get("start_date") and cleaned["end_date"] and cleaned["start_date"] > cleaned["end_date"]:
                cleaned["start_date"], cleaned["end_date"] = cleaned["end_date"], cleaned["start_date"]

        # Convert amounts to float
        if cleaned.get("min_amount"):
            cleaned["min_amount"] = float(cleaned["min_amount"])
        if cleaned.get("max_amount"):
            cleaned["max_amount"] = float(cleaned["max_amount"])
            if cleaned.get("min_amount") and cleaned["max_amount"] and cleaned["min_amount"] > cleaned["max_amount"]:
                cleaned["min_amount"], cleaned["max_amount"] = cleaned["max_amount"], cleaned["min_amount"]

        return cleaned