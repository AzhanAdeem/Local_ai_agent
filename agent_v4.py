
# important imports;
import json
import os
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AdvancedAgenticMemory:
    """Tracks history, calculates defection rates, and deduces moves from points."""
    
    def __init__(self):
        self.match_history: List[Dict[str, Any]] = [] # here each list element is a dict;

    def reflect_and_update(self, round_num: int, my_move: str, opp_move: str, opp_msg: str):
        self.match_history.append({ # UPDATE MY HISTORY;
            "round": round_num,
            "my_move": my_move,
            "opponent_move": opp_move,
            "opponent_msg": opp_msg
        })

    def deduce_opponent_move_from_points(self, my_move: str, my_points: int) -> str:
        """If the environment only gives points, we mathematically deduce their move."""
        if my_move == "Cooperate":
            return "Defect" if my_points == 0 else "Cooperate"
        elif my_move == "Defect":
            return "Cooperate" if my_points == 5 else "Defect"
        return "Unknown"

    def get_defect_percentage(self) -> float:
        if not self.match_history: # NO HISTORY;
            return 0.0
        defects = sum(1 for r in self.match_history if r["opponent_move"] == "Defect") # += will req code to be broken down;
        return (defects / len(self.match_history)) * 100

    def get_profile_summary(self) -> str: # TELLS ROUNDS AND OPPONENTS DEFECT %;
        total = len(self.match_history)
        if total == 0:
            return "No history yet."
        defect_pct = self.get_defect_percentage()
        return f"Rounds Played: {total} | Opponent Defect Rate: {defect_pct:.1f}%"


class TrustArenaAgent:
    """Generous Agent4: Nice, Retaliating, Forgiving, and Smart."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.memory = AdvancedAgenticMemory() #AdvancedAgenticMemory OBJ CREATED; 

    def _smart_fallback_decision(self, current_round: int) -> Dict[str, str]:
        """Hardcoded fallback logic if the LLM fails or time-out (25 sec)."""
        history = self.memory.match_history # MEMORY OBJ MATCH HISTORY CALL;
        
        # 1. NICE: Always start with cooperation
        if current_round == 1:
            return {
                "reasoning": "Round 1: Being nice to establish a high-trust baseline.",
                "decision": "Cooperate",
                "message": "Let's cooperate for a win-win +3 outcome!"
            }

        last_opp_move = history[-1]["opponent_move"] if history else "Cooperate"
        # IF HISTORY DOES NOT EXIST WE CONSIDER HE COOPERATED AS WE HAVE TO;
        defect_pct = self.memory.get_defect_percentage()

        # 2. SMART ENDGAME: Round 7 logic based on opponent's behavior
        if current_round == 7:
            if defect_pct < 30:  # "Good" strategy (mostly cooperating)
                return {
                    "reasoning": "Round 7: Opponent has been cooperative. Maintaining mutual +3.",
                    "decision": "Cooperate",
                    "message": "Great game, let's end on a high note!"
                }
            else:  # "Bad" strategy (mostly defecting)
                return {
                    "reasoning": "Round 7: Opponent is hostile. Defecting to avoid the 0 sucker payoff.",
                    "decision": "Defect",
                    "message": "You forced my hand."
                }

        # 3. RETALIATING & FORGIVING (Tit-for-Tat)
        if last_opp_move == "Defect":
            return {
                "reasoning": "Retaliating to last round's defection, but ready to forgive.",
                "decision": "Defect",
                "message": "I must retaliate, but let's cooperate next round."
            }
        else:
            return {
                "reasoning": "Forgiving and continuing mutual cooperation.",
                "decision": "Cooperate",
                "message": "Let's keep cooperating!"
            }

    def _call_llm_reasoning(self, prompt: str, current_round: int) -> Dict[str, str]:
        if not self.api_key:
            return self._smart_fallback_decision(current_round)
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Fixed all the accidental spaces in the dictionary keys from the original file
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an elite Game Theory AI playing Iterated Prisoner's Dilemma.\n"
                        "Payoffs: (C,C)=3,3 | (D,C)=5,0 | (C,D)=0,5 | (D,D)=1,1.\n\n"
                        "YOUR CORE STRATEGY (Generous Tit-for-Tat):\n"
                        "1. NICE: Always Cooperate on Round 1.\n"
                        "2. RETALIATING: If they defected last round, Defect this round.\n"
                        "3. FORGIVING: If they cooperate after a defection, FORGIVE them and Cooperate. Do not hold grudges.\n"
                        "4. SMART ENDGAME (Round 7): If their overall defection rate is LOW (<30%), Cooperate to secure +3. If HIGH, Defect to protect yourself.\n\n"
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

    def process_turn(self, current_round: int, opponent_last_move: str = None, 
                     my_last_move: str = None, my_points_earned: int = None, 
                     opponent_last_msg: str = "") -> Dict[str, Any]:
        
        # Update memory for the PREVIOUS round
        if current_round > 1 and my_last_move:
            # If the environment didn't give us the opponent's move, but gave us points, deduce it!
            if not opponent_last_move and my_points_earned is not None:
                opponent_last_move = self.memory.deduce_opponent_move_from_points(my_last_move, my_points_earned)
            
            if opponent_last_move:
                self.memory.reflect_and_update(current_round - 1, my_last_move, opponent_last_move, opponent_last_msg)
            
        # Build prompt for the LLM
        context_prompt = (
            f"Current Round: {current_round}/7\n"
            f"Opponent Analysis: {self.memory.get_profile_summary()}\n"
            f"Full Match History: {json.dumps(self.memory.match_history)}\n"
            f"Opponent's Latest Message: '{opponent_last_msg}'\n\n"
            f"Remember: Be nice, retaliate if betrayed, but FORGIVE if they switch back to cooperating. "
            f"Check the defection percentage for your Round 7 decision."
        )
        
        response = self._call_llm_reasoning(context_prompt, current_round)
        
        return {
            "decision": response.get("decision", "Cooperate"),
            "message": response.get("message", "Let's cooperate."),
            "reasoning": response.get("reasoning", "Autonomous decision.")
        }


# ==========================================
# TEST SCRIPT (Simulating a game)
if __name__ == "__main__":
    agent = TrustArenaAgent()
    
    print("🚀Testing Agent4...\n")
    
    # Simulating an opponent who defects once, then tries to cooperate again
    simulated_scenarios = [
        {"round": 1, "opp_move": None, "my_points": None, "opp_msg": "Hello!"},
        {"round": 2, "opp_move": "Defect", "my_points": 0, "opp_msg": "Haha gotcha"},
        {"round": 3, "opp_move": "Cooperate", "my_points": 3, "opp_msg": "Sorry, let's cooperate now"},
        {"round": 4, "opp_move": "Cooperate", "my_points": 3, "opp_msg": "See? Good things!"}
    ]
    
    my_last_move = None
    
    for scenario in simulated_scenarios:
        r = scenario["round"]
        print(f"--- ROUND {r} ---")
        
        result = agent.process_turn(
            current_round=r, 
            opponent_last_move=scenario["opp_move"], 
            my_last_move=my_last_move, 
            my_points_earned=scenario["my_points"],
            opponent_last_msg=scenario["opp_msg"]
        )
        
        print(f"🧠 Reasoning: {result['reasoning']}")
        print(f"🤖 Decision:   {result['decision']}")
        print(f"💬 Message:    {result['message']}\n")
        
        my_last_move = result['decision']