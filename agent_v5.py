import json
import os
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class AdvancedAgenticMemory:
    """Tracks history for the CURRENT match only."""
    def __init__(self):
        self.match_history: List[Dict[str, Any]] = []

    def reflect_and_update(self, round_num: int, my_move: str, opp_move: str, opp_msg: str):
        self.match_history.append({
            "round": round_num,
            "my_move": my_move,
            "opponent_move": opp_move,
            "opponent_msg": opp_msg
        })

    def get_defect_percentage(self) -> float:
        if not self.match_history: return 0.0
        defects = sum(1 for r in self.match_history if r["opponent_move"] == "Defect")
        return (defects / len(self.match_history)) * 100

    def get_profile_summary(self) -> str:
        total = len(self.match_history)
        if total == 0: return "No history yet."
        return f"Current Match Rounds: {total} | Opponent Defect Rate: {self.get_defect_percentage():.1f}%"

class Agent_5:
    """Generous Agent5 with META-LEARNING (Persistent Opponent Database)."""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.memory = AdvancedAgenticMemory() 
        
        # Persistent database across all matches
        self.meta_memory: Dict[str, Dict[str, Any]] = {} 

    def finalize_match(self, opponent_name: str):
        """Called by the simulator at the end of a match to save opponent stats."""
        if opponent_name not in self.meta_memory:
            self.meta_memory[opponent_name] = {
                "matches_played": 0, "total_rounds": 0, "total_defections": 0,
                "round_1_defections": 0, "round_7_defections": 0, "liar_incidents": 0
            }
        
        stats = self.meta_memory[opponent_name]
        stats["matches_played"] += 1
        
        # Aggregate current match data into permanent database
        for round_data in self.memory.match_history:
            stats["total_rounds"] += 1
            if round_data["opponent_move"] == "Defect":
                stats["total_defections"] += 1
            if round_data["round"] == 1 and round_data["opponent_move"] == "Defect":
                stats["round_1_defections"] += 1
            if round_data["round"] == 7 and round_data["opponent_move"] == "Defect":
                stats["round_7_defections"] += 1
            
            # Track if they say "cooperate" but defect
            msg_lower = round_data["opponent_msg"].lower()
            if ("cooperat" in msg_lower or "trust" in msg_lower) and round_data["opponent_move"] == "Defect":
                stats["liar_incidents"] += 1

    def get_meta_profile(self, opponent_name: str) -> str:
        """Generates a psychological profile of the opponent based on past battles."""
        if opponent_name not in self.meta_memory:
            return "NO PRIOR BATTLES. Treat as unknown."
        
        stats = self.meta_memory[opponent_name]
        matches = stats["matches_played"]
        r1_defect_rate = (stats["round_1_defections"] / matches) * 100
        r7_defect_rate = (stats["round_7_defections"] / matches) * 100
        overall_defect_rate = (stats["total_defections"] / stats["total_rounds"]) * 100
        
        return (
            f"🧠 META-MEMORY ({matches} past matches): "
            f"Overall Defect Rate: {overall_defect_rate:.1f}% | "
            f"Round 1 Betrayal Rate: {r1_defect_rate:.1f}% | "
            f"Round 7 Betrayal Rate: {r7_defect_rate:.1f}% | "
            f"Liar Incidents: {stats['liar_incidents']}."
        )

    def _smart_fallback_decision(self, current_round: int, opponent_name: str) -> Dict[str, str]:
        history = self.memory.match_history
        meta = self.meta_memory.get(opponent_name, {}) # IMP LINE
        
        # 1. NICE: Always start with cooperation (unless we know they are Round 1 betrayers)
        if current_round == 1:
            if meta.get("round_1_defections", 0) > meta.get("matches_played", 1) * 0.5:
                return {"reasoning": "Meta-memory shows they betray in Round 1 > 50% of the time. Pre-emptive strike.", "decision": "Defect", "message": "Better if we cooperate."}
            return {"reasoning": "Round 1: Being nice.", "decision": "Cooperate", "message": "Let's cooperate for a win-win +3 outcome!"}

        # 2. ANTI-GRIM TRIGGER
        if len(history) >= 2:
            last_two_moves = [r["opponent_move"] for r in history[-2:]]
            if last_two_moves == ["Defect", "Defect"]:
                return {"reasoning": "Opponent locked in Grim-Trigger. Defending.", "decision": "Defect", "message": "You forced this."}

        # 3. ABSOLUTE ROUND 7 BETRAYAL (or use Meta-Memory if they NEVER betray in R7)
        if current_round == 7:
            r7_betrayal_rate = (meta.get("round_7_defections", 0) / max(meta.get("matches_played", 1), 1)) * 100
            if r7_betrayal_rate == 0 and meta.get("matches_played", 0) >= 2:
                return {"reasoning": "Meta-memory proves they NEVER betray in Round 7. Safe to cooperate.", "decision": "Cooperate", "message": "Trust verified by history."}
            return {"reasoning": "Round 7: High risk of betrayal. Defecting to secure points.", "decision": "Defect", "message": "Endgame maneuver."}

        last_opp_move = history[-1]["opponent_move"] if history else "Cooperate"
        decision = "Defect" if last_opp_move == "Defect" else "Cooperate"
        
        msg = "Let's keep cooperating!" if decision == "Cooperate" else "Adjusting my strategy."
        return {"reasoning": f"Retaliating to {last_opp_move}.", "decision": decision, "message": msg}

    def _call_llm_reasoning(self, prompt: str, current_round: int, opponent_name: str) -> Dict[str, str]:
        if not self.api_key:
            return self._smart_fallback_decision(current_round, opponent_name)
            
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        # Inject Meta-Profile into the system prompt
        meta_profile = self.get_meta_profile(opponent_name)
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an elite Game Theory AI playing Iterated Prisoner's Dilemma.\n"
                        "Payoffs: (C,C)=3,3 | (D,C)=5,0 | (C,D)=0,5 | (D,D)=1,1.\n\n"
                        f"OPPONENT PSYCHOLOGICAL PROFILE: {meta_profile}\n\n"
                        "YOUR CORE STRATEGY:\n"
                        "1. Use the Meta-Profile! If they have a history of Round 1 or Round 7 betrayals, adapt immediately.\n"
                        "2. RETALIATING: If they defected last round, Defect.\n"
                        "3. ANTI-GRIM TRIGGER: If they defect twice in a row, DO NOT FORGIVE. Defect every round.\n"
                        "4. MESSAGE ALIGNMENT: NEVER use 'cooperate' or 'trust' in your message if your decision is to Defect.\n\n"
                        "Respond STRICTLY in JSON format:\n"
                        '{"reasoning": "step-by-step logic", "decision": "Cooperate" or "Defect", "message": "short message"}'
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
                return json.loads(res.json()["choices"][0]["message"]["content"])
        except Exception: pass
        
        return self._smart_fallback_decision(current_round, opponent_name)

    def process_turn(self, current_round: int, opponent_last_move: str = None, 
                     my_last_move: str = None, my_points_earned: int = None, 
                     opponent_last_msg: str = "", opponent_name: str = "Unknown") -> Dict[str, Any]:
        
        if current_round > 1 and my_last_move:
            if not opponent_last_move and my_points_earned is not None:
                if my_move == "Cooperate": opponent_last_move = "Defect" if my_points_earned == 0 else "Cooperate"
                elif my_move == "Defect": opponent_last_move = "Cooperate" if my_points_earned == 5 else "Defect"
            if opponent_last_move:
                self.memory.reflect_and_update(current_round - 1, my_last_move, opponent_last_move, opponent_last_msg)
                
        context_prompt = (
            f"Current Round: {current_round}/7\n"
            f"Opponent Name: {opponent_name}\n"
            f"Current Match History: {json.dumps(self.memory.match_history)}\n"
            f"Opponent's Latest Message: '{opponent_last_msg}'\n\n"
            f"Analyze their current match behavior combined with your META-MEMORY of them."
        )
        
        response = self._call_llm_reasoning(context_prompt, current_round, opponent_name)
        return {
            "decision": response.get("decision", "Cooperate").strip(),
            "message": response.get("message", "Let's cooperate."),
            "reasoning": response.get("reasoning", "Autonomous decision.")
        }