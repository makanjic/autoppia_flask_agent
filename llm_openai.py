from langchain_openai import ChatOpenAI
from .config import OPENAI_MODEL, OPENAI_API_KEY, OPENAI_MAX_TOKENS, OPENAI_TEMPERATURE

# Initialize the model
llm = ChatOpenAI(model=OPENAI_MODEL,
                 api_key=OPENAI_API_KEY,
                 temperature=OPENAI_TEMPERATURE,
                 max_tokens=OPENAI_MAX_TOKENS)
