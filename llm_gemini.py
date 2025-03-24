from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr
from .config import GEMINI_MODEL, GEMINI_API_KEY

# Initialize the model
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL,
                             api_key=SecretStr(GEMINI_API_KEY))
