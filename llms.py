from google import genai
import config
import os
from openai import OpenAI
from langchain.llms.base import LLM
from typing import Optional, List

global_llm = None

def init_llm():
    """Initialize the LLM once and share it everywhere."""
    global global_llm
    if global_llm is None:
        print("Initializing shared LLM instance...")
        global_llm = gemini("gemini-1.5-flash")
    return global_llm


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
        elif model_type == "ondevicellm":
            self.model = OnDeviceLLM()
        else:
            raise ValueError("Unsupported model type. Use 'gemini' or 'qwen'.")

    @property
    def _llm_type(self) -> str:
        return "custom_llm"
    
    def _call(self, prompt: str, stop: Optional[list] = None, **kwargs) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self.model.generate_response(messages)
    


from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import BitsAndBytesConfig
import torch
class OnDeviceLLM():
    def __init__(self):
        self.model_name = "Qwen/Qwen2.5-3B-Instruct"
        self.quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_type=torch.bfloat16
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=self.quantization_config,
            # dtype=torch.int8,
            device_map="auto",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def generate_response(self, messages: str) -> str:
        torch.no_grad()
        messages = [
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
            {"role": "user", "content": messages[0]["content"]}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response
    
    def generate_response_with_params(self, prompt: str) -> str:
        torch.no_grad()
        messages = [
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response
    
    def print_guide(self):
        print("To use the OnDeviceLLM class, create an instance.")
        print("Then, call the generate_response method with your prompt to get a response.")
        print("Example:")
        print("model = OnDeviceLLM()")
        print("response = model.generate_response('Your prompt here')")
        print("print(response)")



