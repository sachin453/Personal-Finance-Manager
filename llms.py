from google import genai
import os , requests
from openai import OpenAI
from langchain.llms.base import LLM
from typing import Optional, List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain.chat_models import init_chat_model
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


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
        )
        return response.text

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
        self.model = "deepseek-ai/DeepSeek-R1:fireworks-ai"
        # self.model="Qwen/Qwen2.5-7B-Instruct:together"
        
    def generate_response(self, messages) -> str:
        completion = self.client.chat.completions.create(
            model = self.model,
            messages=messages,
        )
        return completion.choices[0].message.content
    
    def generate_response_with_params(self, prompt:str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
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
    
    model_type: str = "qwen"
    model_name: str = "gemini-1.5-flash"
    model: object = None          # <-- Declare here so Pydantic allows it

    def __init__(self, model_type="gemini", model_name="gemini-1.5-flash", **kwargs):
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
    
    def _call(self, prompt: str, stop: Optional[list] = None, **kwargs) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.model.generate_response(messages)
    


class MyCustomChatModel(BaseChatModel):
    """
    A custom chat model that interfaces with a local HTTP endpoint.
    It demonstrates how to correctly handle input messages and format output.
    """
    
    # 1. Define custom parameters using Field for Pydantic (better for LangChain integration)
    my_custom_param: str = Field(default="default_value", description="A custom string parameter.")
    
    # 2. Add required attributes (like client) if needed, or in this case, the API URL
    api_url: str = Field(default="http://localhost:8000/generate", description="The URL of the local generation API.")
    max_tokens: int = Field(default=250, description="The maximum number of tokens to generate.")


    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[object] = None,
        **kwargs,
    ) -> ChatResult:
        """
        The core logic for generating a response from the model.
        It must return a ChatResult object.
        """
        
        # --- Input Processing ---
        # 3. Extract the prompt from the messages list. 
        #    A simple approach is to get the content of the *last* HumanMessage.
        #    A more complex model would process all messages to form a conversation history.
        
        # Find the last message that is from a human/user
        prompt_message = next(
            (m for m in reversed(messages) if isinstance(m, HumanMessage)), 
            messages[-1] # Fallback to the very last message if no HumanMessage is found
        )
        prompt = prompt_message.content
        
        # --- API Call ---
        data = {
            "prompt": prompt, # 4. Use the actual prompt from the user input
            "max_tokens": self.max_tokens, # Use the model's configured parameter
            # Add any other required parameters here, like 'stop' sequences
        }

        try:
            # 5. Add a timeout for robustness and use the configured URL
            response = requests.post(self.api_url, json=data, timeout=30)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            # Assuming your local API returns a JSON like: {"text": "The answer is 'chota'."}
            api_response_data = response.json()
            
            # 6. Get the generated text content. Adjust the key ('text') based on your actual API response structure.
            response_content = api_response_data.get("text", "Error: No 'text' field in API response.")
            
        except requests.exceptions.RequestException as e:
            # Handle potential connection errors, timeouts, etc.
            print(f"Error calling local API: {e}")
            response_content = f"API Error (using {self.api_url}): Could not connect or failed. Details: {e}"

        
        # --- Output Formatting (Required by BaseChatModel) ---
        # 7. Create the AIMessage object with the generated content
        ai_message = AIMessage(content=response_content)
        
        # 8. Wrap the AIMessage in a ChatGeneration object
        generation = ChatGeneration(message=ai_message)
        
        # 9. Return the required ChatResult object
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "my_custom_chat_model"

    # 10. (Optional but recommended) Implement the required `_get_generation_info` method 
    #     to pass through information like token usage or log probs.
    def _get_generation_info(self, **kwargs) -> dict:
        """Get any model-specific information that should be included in the generation."""
        # This example just returns the custom parameter for logging/debugging
        return {"custom_param_used": self.my_custom_param}





