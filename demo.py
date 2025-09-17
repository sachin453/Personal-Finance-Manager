import os
import config
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

completion = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct:together",
    messages=[
        {
            "role": "user",
            "content": "Can you write a short paragraph on Quantum Physics?"
        }
    ],
)

print(completion.choices[0].message)