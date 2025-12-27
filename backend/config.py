"""Configuration for the LLM Council."""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "z-ai/glm-4.5-air:free",             # Strong all-rounder, coding + reasoning
    "kwaipilot/kat-coder-pro:free",     # Heavy-duty coding specialist
    "amazon/nova-2-lite-v1:free",       # Fast generalist, everyday tasks
    "google/gemma-3-27b-it:free",       # Lightweight reasoning + light coding
    "tngtech/deepseek-r1t-chimera:free",  # Efficient instruction-following, general + coding
    "qwen/qwen3-coder:free", # Coding-focused, multilingual, structured output
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "tngtech/deepseek-r1t2-chimera:free"

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Data directory for conversation storage
DATA_DIR = "data/conversations"
USERS_FILE = "data/users.json"
