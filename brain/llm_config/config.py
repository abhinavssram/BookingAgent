import os
from dotenv import load_dotenv
from anthropic import Anthropic
from brain.llm_config.constants import MODEL_NAME, GROQ_MODEL_NAME
from groq import Groq
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
class LLMConfig:
    def __init__(self, model_name: str = MODEL_NAME, api_key: str = ANTHROPIC_API_KEY, groq_model_name: str = GROQ_MODEL_NAME, groq_api_key: str = GROQ_API_KEY):
        self.model_name = model_name
        self.api_key = api_key
        self.groq_model_name = groq_model_name
        self.groq_api_key = groq_api_key
        self.client = Anthropic(api_key=self.api_key)
        self.groq_client = Groq(api_key=self.groq_api_key)

    def call_anthropic(self, prompt: str, max_tokens: int = 1024):
        response = self.client.messages.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.content[0].text
    def call_groq(self, prompt: str, max_tokens: int = 1024):
        response = self.groq_client.chat.completions.create(
            model=self.groq_model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content