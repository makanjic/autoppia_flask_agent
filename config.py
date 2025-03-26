# take from autoppia_iwa

import os
from pathlib import Path

from distutils.util import strtobool
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ============================
# LLM CONFIGURATION
# ============================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # Can be "gemini" or "openai"
LLM_THRESHOLD = 100
LLM_CONTEXT_WINDOW = int(os.getenv("LLM_CONTEXT_WINDOW", 10000))

LOCAL_MODEL_ENDPOINT = os.getenv("LOCAL_MODEL_ENDPOINT", "http://127.0.0.1:6000/generate")
LOCAL_PARALLEL_MODEL_ENDPOINT = os.getenv("LOCAL_PARALLEL_MODEL_ENDPOINT", "http://127.0.0.1:6000/generate_parallel")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-32k-0613")
OPENAI_MAX_TOKENS = int(os.getenv("LLM_CONTEXT_WINDOW", 2000))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.8))

# Genmini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# PlayWright Configuration
BROWSER_HEADLESS = bool(strtobool(os.getenv("BROWSER_HEADLESS", "false")))

# Validate critical environment variables
if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is set to 'openai'.")
if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is set to 'gemini'.")    

# ============================
# Agent Configurations
# ============================
AGENT_NAME = os.getenv("AGENT_NAME")

# ============================
# MongoDB Configurations
# ============================
MONGO_DB_URL = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "autoppia_web_agent")