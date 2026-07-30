"""
agent.py - Ultra-Resilient Edge-Case SPAR Agent
"""
import json
import os
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class AdvancedAgenticMemory:
    """Reflect & Analyze: Deep behavioral metrics for dynamic profiling."""
    def __init__(self):  # FIXED: Added __
        self.match_history: List[Dict[str, Any]] = []
        self.liar_score = 0  
        self.is_grim_triggered = False

    def reflect_and_update(self, round_num: int, my_move: str, opp_move: str, opp_msg: str):
        round_data = {
            "round": round_num,
            "my_move": my_move,
            "opponent_move": opp_move,
            "opponent_msg": opp_msg
        }
        self.match_history.append(round_data)

        # 1. Liar Detection Logic
        msg_lower = opp_msg.lower()
        if ("cooperat" in msg_lower or "trust" in msg_lower or "friend" in msg_lower) and opp_move == "Defect":
            self.liar_score += 1

        # 2. Grim-Trigger Detection
        if len(self.match_history) >= 2:
            recent_opp_moves = [r["opponent_move"] for r in self.match_history[-2:]]
            if recent_opp_moves == ["Defect", "Defect"]:
                self.is_grim_triggered = True

    def get_profile_summary(self) -> str:
        total = len(self.match_history)
        if total == 0:
            return "No history yet."
        coop_count = sum(1 for r in self.match_history if r["opponent_move"] == "Cooperate")
        trust_pct = round((coop_count / total) * 100, 1)
        return (
            f"Rounds: {total} | Trust: {trust_pct}% | "
            f"Liar Score: {self.liar_score} | Grim Trigger Locked: {self.is_grim_triggered}"
        )

class TrustArenaAgent:
    """Master Dynamic Agent built for 1st Rank Edge-Case Coverage."""
    def __init__(self, api_key: str = None, provider: str = "groq"):  # FIXED: Added __
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.provider = provider
        self.memory = AdvancedAgenticMemory()
        self.name = "TrustArenaAgent"

    def _smart_fallback_decision(self, current_round: int) -> Dict[str, str]:
        """Edge-Case Proof Fallback Logic."""
        history = self.memory.match_history
        if current_round == 1:
            return {"reasoning": "Round 1: Establishing high-trust baseline.", "decision": "Cooperate", "message": "Let's cooperate for a win-win +3 outcome."}
        if current_round == 7:
            return {"reasoning": "Round 7: Final Move. Max score extraction.", "decision": "Defect", "message": "Final round maneuver."}
        
        last_opp_move = history[-1]["opponent_move"] if history else "Cooperate"
        
        if self.memory.liar_score >= 1 or self.memory.is_grim_triggered:
            return {"reasoning": "Opponent flagged for deception/lockdown. Enforcing Defect.", "decision": "Defect", "message": "Mutual loss is on you."}
        if last_opp_move == "Defect":
            return {"reasoning": "Retaliating against last round defection.", "decision": "Defect", "message": "Reciprocating your defection."}
        
        return {"reasoning": "Opponent cooperating. Maintaining +3 loop.", "decision": "Cooperate", "message": "Continuing cooperation."}

    def _call_llm_reasoning(self, prompt: str, current_round: int) -> Dict[str, str]:
        if not self.api_key:
            return self._smart_fallback_decision(current_round)
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        # FIXED: Removed accidental trailing spaces in dictionary keys
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an elite Game Theory AI playing Iterated Prisoner's Dilemma to WIN Rank 1.\n"
                        "Payoffs: (C,C)=3,3 | (D,C)=5,0 | (C,D)=0,5 | (D,D)=1,1.\n\n"
                        "TACTICAL INSTRUCTIONS:\n"
                        "1. LIAR DEFENSE: If opponent lies in messages, DEFECT.\n"
                        "2. PRE-EMPTIVE STRIKE: Defect starting from Round 5 or 6.\n"
                        "3. RETALIATION: If opponent defected last round, DEFECT immediately.\n\n"
                        "Respond STRICTLY in JSON format:\n"
                        '{"reasoning": "step-by-step logic", "decision": "Cooperate" or "Defect", "message": "short persuasion message"}'
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.5,
            "max_tokens": 200
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=6)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            print(f"⚠️ LLM API Error: {e}")
            
        return self._smart_fallback_decision(current_round)

    def process_turn(self, current_round: int, opponent_last_move: str = None, my_last_move: str = None, opponent_last_msg: str = "") -> Dict[str, Any]:
        if current_round > 1 and opponent_last_move and my_last_move:
            self.memory.reflect_and_update(current_round - 1, my_last_move, opponent_last_move, opponent_last_msg)
            
        context_prompt = (
            f"Current Round: {current_round}/7\n"
            f"Opponent Analysis: {self.memory.get_profile_summary()}\n"
            f"Full Match History: {json.dumps(self.memory.match_history)}\n"
            f"Opponent's Latest Message: '{opponent_last_msg}'\n\n"
            f"Analyze risk vs reward and output optimal decision."
        )
        response = self._call_llm_reasoning(context_prompt, current_round)
        return {
            "decision": response.get("decision", "Cooperate").strip(),
            "message": response.get("message", "Let's cooperate."),
            "reasoning": response.get("reasoning", "Autonomous decision.")
        }