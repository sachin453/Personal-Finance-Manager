import llms

class CategorizationAgent:
    def __init__(self):
        self.client = llms.gemini("gemini-2.0-flash")

    def classify_transaction(self, description, amount):
        prompt = f"""
        Classify this transaction into one of these categories:
        [Groceries, Rent, Utilities, Entertainment, Income, Miscellaneous]

        Transaction: '{description} - ${abs(amount)}'
        """
        response = self.client.generate_response(prompt)
        return response.strip()
