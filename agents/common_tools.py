from langchain_core.tools import tool
from datetime import datetime
import os , requests

@tool
def date_tool(query: str) -> str:
    '''Return the current date in YYYY-MM-DD format.'''
    today = datetime.today()
    return today.strftime("%Y-%m-%d")


@tool
def calculator_tool(expression: str) -> str:
    '''Evaluate a mathematical expression and return the result.'''
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"
    

@tool
def google_search_tool(query: str) -> str:
        '''Use Google search to find the information related to current or future events.
        :param query: The search query string.
        :return: A string containing the titles and snippets of the top 3 search results.
        '''
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": os.getenv("GOOGLE_API_KEY"),
            "cx": os.getenv("CX"),
            "num": 3
        }
        response = requests.get(url, params=params)
        data = response.json()

        if "items" not in data:
            return "No google search results found."

        results = ""
        for item in data["items"]:
            results += f"Title: {item.get('title', '')}\nSnippet: {item.get('snippet', '')}\n\n"
        return results.strip()
    

tools = [date_tool, calculator_tool , google_search_tool]