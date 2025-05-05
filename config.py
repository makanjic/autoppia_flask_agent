# take from autoppia_iwa

import os
from pathlib import Path

from distutils.util import strtobool
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# DEMO WEB PORT
# ============================
# This is the port where the demo web server will run.
# You can change this to any available port on your machine.
# The default is 8000.
# ============================
DEMO_WEBS_STARTING_PORT=int(os.getenv("DEMO_WEBS_STARTING_PORT", 8000))

# ============================
# LLM CONFIGURATION
# ============================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # Can be "gemini" or "openai", "perplexity"
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

# Perplexity Configuration
PPLX_API_KEY = os.getenv("PPLX_API_KEY")
PPLX_MODEL = os.getenv("PPLX_MODEL", "lama-3.1-sonar-small-128k-online")
PPLX_TEMPERATURE = float(os.getenv("PPLX_TEMPERATURE", 0))

# PlayWright Configuration
BROWSER_HEADLESS = bool(strtobool(os.getenv("BROWSER_HEADLESS", "false")))

# Validate critical environment variables
if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is set to 'openai'.")
if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is set to 'gemini'.")    
if LLM_PROVIDER == "perplexity" and not PPLX_API_KEY:
    raise ValueError("PPLX_API_KEY is required when LLM_PROVIDER is set to 'perplexity'.")

# ============================
# Agent Configurations
# ============================
AGENT_NAME = os.getenv("AGENT_NAME")

# ============================
# MongoDB Configurations
# ============================
MONGO_DB_URL = os.getenv("MONGO_DB_URL", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "autoppia_web_agent")