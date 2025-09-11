import config
import llms

from agents import ingestion_agent
from agents import categorization_agent
from agents import forecast_agent
from agents import decision_agent

# main.py
from agents.ingestion_agent import IngestionAgent
from agents.categorization_agent import CategorizationAgent
from agents.forecast_agent import ForecastAgent
from agents.decision_agent import DecisionAgent

# 1. Load data
ingestion = IngestionAgent("data/sample_transactions.csv")
transactions = ingestion.load_transactions()

# 2. Categorize transactions
cat_agent = CategorizationAgent()
transactions['category'] = transactions.apply(
    lambda row: cat_agent.classify_transaction(row['description'], row['amount']), axis=1
)

# 3. Forecast expenses
forecast_agent = ForecastAgent()
forecast_agent.train(transactions)
forecast = forecast_agent.predict_future(30)

# 4. Decision making
decision_agent = DecisionAgent()
plan = decision_agent.suggest_actions(
    current_balance=2500,
    forecast_expenses=forecast['yhat'].iloc[-1],
    savings_goal=500
)

print("Suggested Plan:\n", plan)
