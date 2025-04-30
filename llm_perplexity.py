from langchain_community.chat_models import ChatPerplexity
from config import PPLX_MODEL, PPLX_API_KEY, PPLX_TEMPERATURE

# Initialize the model
llm = ChatPerplexity(model=PPLX_MODEL,
                 api_key=PPLX_API_KEY,
                 temperature=PPLX_TEMPERATURE)
