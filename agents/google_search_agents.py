import requests
import os
import llms


class GoogleSearchAgent:
    def __init__(self):
        self.API_KEY = os.getenv("GOOGLE_API_KEY")
        self.CX = os.getenv("CX")
        # self.llm = llms.gemini("gemini-2.0-flash")
        self.llm = llms.qwen()

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
            "num": 3  # top 3 results
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
                "link": item.get("link", "")
            })
        return results
    
    def format_results_for_llm(self,results):
        formatted = ""
        for i, item in enumerate(results, start=1):
            formatted += (
                f"[Result {i}]\n"
                f"Title: {item['title']}\n"
                f"Snippet: {item['snippet']}\n"
                f"URL: {item['link']}\n\n"
            )
        return formatted
    

    def answer_from_search_with_gemini(self, query):
        search_results = self.google_search_tool(query)
        context = self.format_results_for_llm(search_results)
        
        prompt = (
            f"You are a highly accurate assistant.\n"
            f"The user asked: \"{query}\"\n\n"
            f"Here are search results:\n"
            f"{context}\n\n"
            f"Analyze these results and provide a concise and factual answer.\n"
            f"If unsure, say \"I could not find enough information\"."
        )

        response = self.llm.generate_response(prompt)
        # response = self.llm.generate_response(
        #     {"contents": [{"parts": [{"text": prompt}]}]}
        # )
        
        # extract content depending on Gemini response format
        # answer = resp.text  # or whatever the field is
        # return answer
        return response




