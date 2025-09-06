# prompts/prompt.py
TRANSACTION_PARSE_PROMPT = """
            Parse this transaction input: "{input_text}"

            Extract and return ONLY valid JSON:
            {{
                "amount": decimal_number,
                "merchant": "store_name_or_null",
                "transaction_date": "YYYY-MM-DD"
            }}

            Rules:
            - Use today's date ({current_date}) if no date is mentioned.
            - Set merchant to null if not mentioned.
            - Amount must be a positive number.
            - Handle varied phrasings (e.g., "300 dollars", "300 bucks", "300$").

            Examples:
            - "bought groceries of 300$ today from walmart" → {{"amount": 300.00, "merchant": "walmart", "transaction_date": "{current_date}"}}
            - "spent 50 bucks on coffee yesterday" → {{"amount": 50.00, "merchant": null, "transaction_date": "YYYY-MM-DD"}} (day before {current_date})
            - "paid 100$ for bills on July 5th 2025" → {{"amount": 100.00, "merchant": null, "transaction_date": "2025-07-05"}}
            - "bought dinner for 75.50 at Chipotle" → {{"amount": 75.50, "merchant": "Chipotle", "transaction_date": "{current_date}"}}

            Output:
            """
            
            
TRANSACTION_CATEGORIZATION_PROMPT = """
            Additionally, categorize the transaction based on the provided details and user-defined categories. Include the category in the JSON output.

            User-Defined Categories: {categories}

            Rules for Categorization:
            - Match the transaction to one of the user-defined categories based on merchant and description.
            - Use keywords in the description or merchant (e.g., "groceries", "dinner", "Starbucks" → "Food"; "electricity", "bill" → "Bills").
            - If no clear match, use "Other".
            - Include the category in the JSON output.

            Examples:
            - Input: "bought groceries of 300$ today from walmart", Categories: ["Food", "Transportation", "Entertainment", "Shopping", "Bills"]
              → {{"amount": 300.00, "merchant": "walmart", "transaction_date": "{current_date}", "category": "Food"}}
            - Input: "spent 50 bucks on coffee yesterday", Categories: ["Food", "Transportation", "Entertainment", "Shopping", "Bills"]
              → {{"amount": 50.00, "merchant": null, "transaction_date": "YYYY-MM-DD", "category": "Food"}} (day before {current_date})
            - Input: "paid 100$ for bills on July 5th 2025", Categories: ["Food", "Transportation", "Entertainment", "Shopping", "Bills"]
              → {{"amount": 100.00, "merchant": null, "transaction_date": "2025-07-05", "category": "Bills"}}
            - Input: "took a ride to downtown for 25$", Categories: ["Food", "Travel", "Leisure"]
              → {{"amount": 25.00, "merchant": null, "transaction_date": "{current_date}", "category": "Travel"}}

            Output:
            """            

SEARCH_PARSE_PROMPT = """
            Parse this search query: "{query}"

            Extract filters and return ONLY valid JSON with applicable fields:
            {{
                "category": "category_name",
                "date": "YYYY-MM-DD",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD",
                "min_amount": number,
                "max_amount": number
            }}

            Rules:
            - Today is {current_date}.
            - Map keywords to categories (e.g., "grocery", "dinner", "coffee" → "Food"; "electricity", "bill" → "Bills").
            - For single dates, use "date"; for ranges, use "start_date" and "end_date".
            - Ensure start_date ≤ end_date.
            - Handle relative dates (e.g., "this week", "last month").
            - Only include fields that apply.
            - Do not include "merchant" in the output.

            Examples:
            - "show me grocery expenses" → {{"category": "Food"}}
            - "transactions above 100$" → {{"min_amount": 100.0}}
            - "expenses of 11,12,13th July" → {{"start_date": "2025-07-11", "end_date": "2025-07-13"}}
            - "transactions around July 15th" → {{"start_date": "2025-07-14", "end_date": "2025-07-16"}}
            - "show my expensive dining last month" → {{"category": "Food", "start_date": "2025-06-01", "end_date": "2025-06-30", "min_amount": 50.0}}
            - "all food transactions" → {{"category": "Food"}}
            - "Starbucks transactions this month" → {{"category": "Food", "start_date": "2025-07-01", "end_date": "{current_date}"}}

            Output:
            """



RECOMMENDATION_PROMPT = """
            Generate personalized financial recommendations for user {user_id} based on their spending analysis, savings goal progress, budget comparison, and top merchants. Return ONLY a JSON array of recommendations, each with text, category, and priority ("high", "medium", "low").

            Input Data:
            - Spending Analysis: {spending_analysis}
            - Monthly Trend: {monthly_trend}
            - Goal Progress: {goal_progress}
            - Budget Comparison: {budget_comparison}
            - Top Merchants: {top_merchants}

            Rules:
            - Provide 2-5 recommendations.
            - Include budget alerts for overspending (priority: high).
            - Suggest specific actions to reduce spending in high-spend categories or merchants.
            - Offer goal achievement timeline predictions if progress is low.
            - Use category names from spending analysis.
            - Format each recommendation as: {{"text": "string", "category": "string", "priority": "high|medium|low"}}

            Examples:
            - High food spending, frequent Starbucks visits:
              [
                {{"text": "Reduce coffee spending by $30/month by brewing at home", "category": "Food", "priority": "high"}},
                {{"text": "Limit dining out to twice a week to save $50/month", "category": "Food", "priority": "medium"}}
              ]
            - Overspending, slow goal progress:
              [
                {{"text": "Spending exceeds 80% of income; cut discretionary spending by 20%", "category": "General", "priority": "high"}},
                {{"text": "Increase savings by $100/month to meet goal in 6 months", "category": "Savings", "priority": "medium"}}
              ]

            Output:
            """