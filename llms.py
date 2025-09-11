from google import genai

class gemini:
    def __init__(self, model_name: str):
        self.available_models = ["gemini-1.5-flash" , "gemini-1.5-pro" , "gemini-2.0-flash" , "gemini-2.0-pro"]
        self.model = None
        if model_name in self.available_models:
            self.model_name = model_name      
        else:
            raise ValueError("Unsupported model name. Use 'gemini-1.5-flash'.")
        self.client = genai.Client()

    def generate_response(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
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