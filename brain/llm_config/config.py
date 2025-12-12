import os
from dotenv import load_dotenv
from anthropic import Anthropic
from brain.llm_config.constants import MODEL_NAME, GROQ_MODEL_NAME # Assuming these are defined
from groq import Groq
# FIX: Use the correct ChatGroq class for LangChain integration
from langchain_groq import ChatGroq 
from langchain_core.language_models.chat_models import BaseChatModel



class LLMConfig:
    """
    Configuration class to initialize and manage LLM clients.
    Prioritizes Groq for agent operations if the key is available.
    """
    def __init__(
        self, 
        model_name: str = MODEL_NAME, 
        groq_model_name: str = GROQ_MODEL_NAME
    ):
        load_dotenv()

        # Use helper functions to load settings safely
        def get_env_var(name):
            value = os.getenv(name)
            if not value:
                print(f"WARNING: Environment variable {name} not found.")
            return value

        ANTHROPIC_API_KEY = get_env_var("ANTHROPIC_API_KEY") 
        GROQ_API_KEY = get_env_var("GROQ_API_KEY")
        self.model_name = model_name
        self.groq_model_name = groq_model_name
        self.llm: BaseChatModel = None # The primary model for the agent
        
        # 1. Initialize Groq (Preferred Agent Model)
        if GROQ_API_KEY:
            # Use LangChain's ChatGroq for agent compatibility
            self.llm = ChatGroq(
                model=self.groq_model_name, 
                temperature=0.0, # Agents prefer low temperature
                groq_api_key=GROQ_API_KEY
            )
            print(f"INFO: Primary LLM set to Groq ({self.groq_model_name}).")
        
        # 2. Initialize Anthropic (Fallback or secondary client)
        if ANTHROPIC_API_KEY:
            # Initialize the raw SDK client for direct calls
            self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
            print(f"INFO: Anthropic client initialized.")
        else:
            self.anthropic_client = None

        if not self.llm:
             raise EnvironmentError("No valid LLM client could be initialized. Please provide GROQ_API_KEY.")