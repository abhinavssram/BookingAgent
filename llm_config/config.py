import os
from dotenv import load_dotenv
from anthropic import Anthropic
from llm_config.constants import MODEL_NAME
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class LLMConfig:
    def __init__(self, model_name: str = MODEL_NAME, api_key: str = ANTHROPIC_API_KEY):
        self.model_name = model_name
        self.api_key = api_key
        client = Anthropic(api_key=self.api_key)
        self.client = client
    def get_model_name(self):
        return self.model_name

    def get_api_key(self):
        return self.api_key

    def call_anthropic(self, prompt: str, max_tokens: int = 1024):
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text