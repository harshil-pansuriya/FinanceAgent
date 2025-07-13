from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional
import json
import re
from config.setting import Config
from config.logger import logger
from prompts.prompt import TRANSACTION_PARSE_PROMPT,TRANSACTION_CATEGORIZATION_PROMPT, SEARCH_PARSE_PROMPT
from services.user_service import UserService
from schemas.transaction import TransactionParsed

class TransactionParserAgent:
    def __init__(self):
        self.crewai_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=Config.gemini_api_key,
            temperature=0.3
        )

        self.crewai_llm.model = "gemini/gemini-1.5-flash"
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=Config.gemini_api_key,
            temperature=0.3
        )
        # CrewAI agent for transaction parsing and categorization
        self.transaction_agent = Agent(
            role="Transaction Parser and Categorizer",
            goal="Extract amount, merchant, date, and category from natural language transaction input",
            backstory="Expert at parsing and categorizing financial transactions using user-specific preferences",
            llm=self.crewai_llm,
            verbose=False,
            allow_delegation=True,  
            max_retry_limit=1 
        )

        # Initialize Crew
        self.crew = Crew(
            agents=[self.transaction_agent],
            tasks=[],
            verbose=False,
        )

        # Transaction and categorization prompt
        self.transaction_prompt = PromptTemplate(
            input_variables=["input_text", "current_date", "categories"],
            template=TRANSACTION_PARSE_PROMPT + TRANSACTION_CATEGORIZATION_PROMPT
        )

        # Search query prompt
        self.search_prompt = PromptTemplate(
            input_variables=["query", "current_date"],
            template=SEARCH_PARSE_PROMPT
        )

        self.transaction_parser = PydanticOutputParser(pydantic_object=TransactionParsed)

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
            task = Task(
                description=self.transaction_prompt.format(
                    input_text=input_text,
                    current_date=current_date,
                    categories=", ".join(categories)
                ),
                agent=self.transaction_agent,
                expected_output="Valid JSON with amount (decimal), merchant (string or null), transaction_date (YYYY-MM-DD), category (string)"
            )
            self.crew.tasks = [task]
            result = await self.crew.kickoff_async()

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
            logger.info(f"Parsed and categorized transaction for user {user_id}: {input_text} → {category}")
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
            # Ensure start_date ≤ end_date
            if cleaned.get("start_date") and cleaned["end_date"] and cleaned["start_date"] > cleaned["end_date"]:
                cleaned["start_date"], cleaned["end_date"] = cleaned["end_date"], cleaned["start_date"]

        # Convert amounts to float
        if cleaned.get("min_amount"):
            cleaned["min_amount"] = float(cleaned["min_amount"])
        if cleaned.get("max_amount"):
            cleaned["max_amount"] = float(cleaned["max_amount"])
            # Ensure min_amount ≤ max_amount
            if cleaned.get("min_amount") and cleaned["max_amount"] and cleaned["min_amount"] > cleaned["max_amount"]:
                cleaned["min_amount"], cleaned["max_amount"] = cleaned["max_amount"], cleaned["min_amount"]

        return cleaned