"""
agent.py - Master Tournament Winning Engine
Anti-Preemption & Optimal Backward Induction Patched
"""

import json
import requests
from typing import Dict, Any
from config import GROQ_API_KEY, PRIMARY_MODEL, LLM_TIMEOUT
from detector import OpponentTracker
from strategy import GameStrategy

class TrustArenaAgent:
    def __init__(self, api_key: str = None, name: str = "OUR_PRIMARY_AGENT"):
        self.name = name
        self.api_key = api_key or GROQ_API_KEY
        self.tracker = OpponentTracker()
        self.fallback_strategy = GameStrategy(self.tracker)

    def process_turn(
        self, 
        current_round: int, 
        opponent_last_move: str = None, 
        my_last_move: str = None, 
        opponent_last_msg: str = ""
    ) -> Dict[str, Any]:
        
        if current_round > 1:
            self.tracker.update_history(
                my_move=my_last_move, 
                opponent_move=opponent_last_move, 
                message=opponent_last_msg
            )

        classification = self.tracker.classify_opponent()

        # HARD RULE 1: Final Round Betrayal
        if current_round == 7:
            return {
                "decision": "Defect",
                "message": "Final round, GG!",
                "reasoning": "Round 7 backward induction betrayal.",
                "classification": classification
            }

        # HARD RULE 2: Immediate Retaliation against Defection
        if self.tracker.opponent_history and self.tracker.opponent_history[-1] == "Defect":
            return {
                "decision": "Defect",
                "message": "Defecting in self-defense.",
                "reasoning": "Retaliating to opponent defection.",
                "classification": classification
            }

        # HARD RULE 3: Anti-Nofil Pre-emption (Strike on Round 5 before they do!)
        if current_round == 5:
            return {
                "decision": "Defect",
                "message": "Securing endgame positioning.",
                "reasoning": "Pre-emptive strike against smart endgame agents.",
                "classification": classification
            }

        # Rounds 1-4 & 6: Maintain Cooperation
        return {
            "decision": "Cooperate",
            "message": "Let's keep building trust!",
            "reasoning": "Sustaining mutual cooperation for long-term score.",
            "classification": classification
        }