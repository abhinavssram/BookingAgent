from llm_config.config import LLMConfig

def main():
    llm_config = LLMConfig()
    response = llm_config.call_anthropic("Hello, how are you?")
    print(response)


if __name__ == "__main__":
    main()
