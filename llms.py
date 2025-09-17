from google import genai
import config
import os
from openai import OpenAI
from langchain.llms.base import LLM
from typing import Optional, List

class gemini:
    def __init__(self, model_name: str):
        self.available_models = ["gemini-1.5-flash" , "gemini-1.5-pro" , "gemini-2.0-flash" , "gemini-2.0-pro"]
        self.model = None
        if model_name in self.available_models:
            self.model_name = model_name      
        else:
            raise ValueError("Unsupported model name. Use 'gemini-1.5-flash'.")
        self.client = genai.Client()

    def generate_response(self, messages) -> str:
        response = self.client.models.generate_content(
            model=self.model_name, contents=messages[0]["content"]
        )
        return response.text
    
    def generate_response_with_params(self, prompt: str, temperature: float = 0.7, max_output_tokens: int = 256) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )

    def print_guide(self):
        print("To use the Gemini class, create an instance with the desired model name (e.g., 'gemini-1.5-flash').")
        print("Then, call the generate_response method with your prompt to get a response.")
        print("Example:")
        print("model = gemini('gemini-1.5-flash')")
        print("response = model.generate_response('Your prompt here')")
        print("print(response)")



class qwen:
    def __init__(self):
        pass
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=os.environ["HF_TOKEN"],)
        
    def generate_response(self, messages) -> str:
        completion = self.client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct:together",
            messages=messages,
        )
        return completion.choices[0].message.content
    
    def generate_response_with_params(self, prompt:str) -> str:
        completion = self.client.chat.completions.create(
            model="Qwen/Qwen2.5-7B-Instruct:together",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return completion.choices[0].message.content
    
    def print_guide(self):
        print("To use the Qwen class, create an instance.")
        print("Then, call the generate_response method with your prompt to get a response.")
        print("Example:")
        print("model = qwen()")
        print("response = model.generate_response('Your prompt here')")
        print("print(response)")

class CustomLLM(LLM):
    """Wraps Gemini or Qwen to work with LangChain."""
    
    model_type: str = "qwen"      # Default field for Pydantic
    model_name: str = "gemini-1.5-flash"
    model: object = None          # <-- Declare here so Pydantic allows it

    def __init__(self, model_type="qwen", model_name="gemini-1.5-flash", **kwargs):
        super().__init__(**kwargs)
        self.model_type = model_type
        self.model_name = model_name
        
        if model_type == "gemini":
            self.model = gemini(model_name)
        elif model_type == "qwen":
            self.model = qwen()
        else:
            raise ValueError("Unsupported model type. Use 'gemini' or 'qwen'.")

    @property
    def _llm_type(self) -> str:
        return "custom_llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.model.generate_response(messages)



