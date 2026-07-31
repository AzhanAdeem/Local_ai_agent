"""
 RAFAY
config.py - Centralized System Settings & Game Constants
"""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

PRIMARY_MODEL = "llama-3.3-70b-versatile"
LLM_TIMEOUT = 5  # Rulebook allows 25s total turn time

PAYOFFS = {
    ("Cooperate", "Cooperate"): (3, 3),
    ("Cooperate", "Defect"): (0, 6),
    ("Defect", "Cooperate"): (5, 0),
    ("Defect", "Defect"): (1, 1),
}