# agents/decision_agent.py
import llms

class ExecutionAgent:
    def __init__(self):
        self.client = llms.gemini("gemini-2.0-flash")

    def make_decision(self, context):
        prompt = f"""
        You are an execution agent. Based on the following context, make a decision:
        {context}

        Provide a clear and concise action plan.
        """
        response = self.client.generate_response(prompt)
        return response.strip()
