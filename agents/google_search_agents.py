import requests
import os
import llms


class GoogleSearchAgent:
    def __init__(self):
        self.API_KEY = os.getenv("GOOGLE_API_KEY")
        self.CX = os.getenv("CX")
        # self.llm = llms.qwen()
        self.llm = llms.gemini("gemini-1.5-flash")

        # Debugging: mask the API key to see if it's loaded
        if not self.API_KEY or not self.CX:
            raise ValueError("API key or CX not loaded. Check environment variables!")
        # print(f"Loaded API Key: {self.API_KEY[:4]}...{self.API_KEY[-4:]}")
        # print(f"Loaded CX: {self.CX}")

    # @tool
    def google_search_tool(self, query: str) -> list:
        """Search Google and return top search results as a list of dictionaries."""
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": self.API_KEY,
            "cx": self.CX,
            "num": 6  # top 3 results
        }
        response = requests.get(url, params=params)
        data = response.json()

        # Handle case when there are no search results
        if "items" not in data:
            return []  # Return empty list, not a string

        # Extract only the useful data
        results = []
        for item in data["items"]:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                # "link": item.get("link", "")
            })
        return results
    
    def format_results_for_llm(self,results):
        formatted = ""
        for i, item in enumerate(results, start=1):
            formatted += (
                f"[Result {i}]\n"
                f"Title: {item['title']}\n"
                f"Snippet: {item['snippet']}\n"
                # f"URL: {item['link']}\n\n"
            )
        return formatted
    

    def answer_from_search_with_gemini(self, query:str)-> str:
        search_results = self.google_search_tool(query)
        context = self.format_results_for_llm(search_results)
        
        prompt = f"""
        You are a highly accurate assistant.

        The user asked: "{query}"

        Here are the search results:
        {context}

        Your task:
        1. Carefully analyze the snippets.
        2. Identify the snippet that directly answers the question.
        3. Provide a concise and factual answer based ONLY on the search results.
        4. If multiple results conflict, mention the uncertainty.
        5. If no snippet clearly answers the question, respond with: "I could not find enough information."

        Answer:
        """

        messages=[{"role": "user", "content": prompt}]
        # print(prompt)

        response = self.llm.generate_response(messages)
        return response




