from langchain_core.tools import tool
from datetime import datetime
import os, requests, pdfplumber

@tool
def date_tool() -> str:
    """Return today's date in YYYY-MM-DD format."""
    return datetime.today().strftime("%Y-%m-%d")

@tool
def calculator_tool(expression: str) -> str:
    """Evaluate a basic mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"

@tool
def google_search_tool(query: str) -> str:
    """Search Google and return top 3 results with title and snippet."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": os.getenv("GOOGLE_API_KEY"),
        "cx": os.getenv("CX"),
        "num": 3
    }
    try:
        data = requests.get(url, params=params).json()
        items = data.get("items", [])
        if not items:
            return "No results found."
        return "\n\n".join(
            [f"{i+1}. {it['title']}\n{it['snippet']}" for i, it in enumerate(items[:3])]
        )
    except Exception as e:
        return f"Error: {e}"

@tool
def pdf_parser_tool(file_path: str) -> str:
    """Extract text content from a PDF at the given path."""
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
        return "\n".join(pages) or "No text found."
    except Exception as e:
        return f"Error reading PDF: {e}"

@tool
def get_data_dir_files_tool() -> str:
    """List all file paths in the data directory."""
    data_dir = r"C:\Users\sachi\OneDrive\Desktop\PersonalFinanceManager\data"
    try:
        return "\n".join(os.path.join(data_dir, f) for f in os.listdir(data_dir))
    except Exception as e:
        return f"Error: {e}"

@tool
def local_llm_tool(prompt: str) -> str:
    """Send a prompt to the local LLM API and return its response."""
    try:
        resp = requests.post("http://localhost:8000/generate", json={"prompt": prompt, "max_tokens": 250})
        return resp.json().get("text", "No response.")
    except Exception as e:
        return f"Error calling local LLM: {e}"

tools = [date_tool, calculator_tool, google_search_tool, pdf_parser_tool, get_data_dir_files_tool, local_llm_tool]
