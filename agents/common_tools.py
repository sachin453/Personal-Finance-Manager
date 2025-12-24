from langchain_core.tools import tool
from datetime import datetime
import os, requests, pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
def text_parser_tool(file_path: str) -> str:
    """Extract text content from a PDF or txt at the given path."""
    if str(file_path).lower().endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file: {e}"
    elif str(file_path).lower().endswith('.pdf'):
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
            return "\n".join(pages) or "No text found."
        except Exception as e:
            return f"Error reading PDF: {e}"
    else:
        return "Unsupported file type. Only .txt and .pdf are supported."
    


@tool
def get_data_dir_files_tool() -> str:
    """List all file paths in the data directory."""
    data_dir = r"C:\Users\sachi\OneDrive\Desktop\PersonalFinanceManager\data"
    try:
        return "\n".join(os.path.join(data_dir, f) for f in os.listdir(data_dir))
    except Exception as e:
        return f"Error: {e}"
    
@tool
def get_cache_dir_files_tool() -> str:
    """List all file paths in the cache directory."""
    cache_dir = r"C:\Users\sachi\OneDrive\Desktop\PersonalFinanceManager\cache"
    try:
        return "\n".join(os.path.join(cache_dir, f) for f in os.listdir(cache_dir))
    except Exception as e:
        return f"Error: {e}"
    
@tool
def remove_file_tool(file_path: str) -> str:
    """Remove the file at the given path."""
    try:
        os.remove(file_path)
        return f"File {file_path} removed."
    except Exception as e:
        return f"Error removing file: {e}"



@tool
def local_llm_tool(prompt: str) -> str:
    """Send a prompt to the local LLM API and return its response. Only 1000 tokens allowed.
    If this tool does not work, use dont use it.
    """
    try:
        resp = requests.post("http://localhost:8000/generate", json={"prompt": prompt, "max_tokens": 250} , timeout=30)
        return resp.json().get("text", "No response.")
    except Exception as e:
        return f"Error calling local LLM: {e}"
    
@tool
def save_text_to_txt_tool(text: str) -> str:
    """Save the provided text to a .txt file and return the path of file written."""
    cache_dir = r"C:\Users\sachi\OneDrive\Desktop\PersonalFinanceManager\cache"
    random_filename = f"output_{int(datetime.now().timestamp())}.txt"
    file_path = os.path.join(cache_dir, random_filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        return f"Text saved to {file_path}"
    except Exception as e:
        return f"Error saving text: {e}"
    
@tool
def split_txt_into_chunks_txts_tool(file_path: str) -> str:
    """Split a .txt file into chunks and save each chunk as a separate .txt file. Return paths of files written.
    Use it for large .txt files so that LLM can process them in parts. Each chunk is 1000 characters with 100 character overlap. 
    """
    cache_dir = r"C:\Users\sachi\OneDrive\Desktop\PersonalFinanceManager\cache"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        
        file_paths = []
        for i, chunk in enumerate(chunks):
            chunk_filename = f"chunk_{i+1}_{int(datetime.now().timestamp())}.txt"
            chunk_path = os.path.join(cache_dir, chunk_filename)
            with open(chunk_path, "w", encoding="utf-8") as cf:
                cf.write(chunk)
            file_paths.append(chunk_path)
        
        return "\n".join(file_paths) if file_paths else "No chunks created."
    except Exception as e:
        return f"Error splitting text: {e}"
    



    

tools = [date_tool, 
         calculator_tool, 
         google_search_tool, 
         text_parser_tool, 
         get_data_dir_files_tool, 
        #  local_llm_tool , 
         save_text_to_txt_tool , 
         get_cache_dir_files_tool,
         remove_file_tool,
         split_txt_into_chunks_txts_tool
         ]
