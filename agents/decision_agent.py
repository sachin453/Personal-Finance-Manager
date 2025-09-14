# agents/decision_agent.py
import llms

class DecisionAgent:
    def __init__(self):
        self.client = llms.gemini("gemini-2.0-flash")

    def suggest_actions(self, current_balance, forecast_expenses, savings_goal):
        prompt = f"""
        You are a financial planning assistant.
        Current balance: ${current_balance}
        Forecasted total expenses: ${forecast_expenses}
        Savings goal: ${savings_goal}

        Suggest a clear plan to meet the goal less than 50 words. It should be compact and in points.
        """
        response = self.client.generate_response(prompt)
        return response.strip()
