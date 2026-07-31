"""
agent_v5.py - Agent5 with Persistent File-Based Meta-Learning
"""
import json
import os
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from opponent_database import OpponentDatabase  # <-- NEW IMPORT

load_dotenv()


class AdvancedAgenticMemory:
    """Tracks history for the CURRENT match only (in RAM)."""
    def __init__(self):  # FIXED: was "def init(self):"
        self.match_history: List[Dict[str, Any]] = []

    def reflect_and_update(self, round_num: int, my_move: str,
                           opp_move: str, opp_msg: str):
        self.match_history.append({
            "round": round_num,
            "my_move": my_move,
            "opponent_move": opp_move,
            "opponent_msg": opp_msg
        })

    def get_defect_percentage(self) -> float:
        if not self.match_history:
            return 0.0
        defects = sum(1 for r in self.match_history
                      if r["opponent_move"] == "Defect")
        return (defects / len(self.match_history)) * 100

    def get_profile_summary(self) -> str:
        total = len(self.match_history)
        if total == 0:
            return "No history yet."
        return (f"Current Match Rounds: {total} | "
                f"Opponent Defect Rate: {self.get_defect_percentage():.1f}%")


class Agent_6:
    """Agent5 with FILE-BASED Meta-Learning + Strategy Drift Detection."""

    def __init__(self, api_key: str = None):  # FIXED: was "def init"
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.memory = AdvancedAgenticMemory()
        self.name = "Agent_6"

        # 🧠 Persistent file-based database (survives restarts!)
        self.db = OpponentDatabase(base_dir="opponent_database")

    # ── Called by simulator at end of each match ──────────────
    def finalize_match(self, opponent_name: str):
        """Saves the entire match to disk and runs drift detection."""
        if self.memory.match_history:
            self.db.save_match(
                opponent_name=opponent_name,
                match_history=self.memory.match_history,
                my_name=self.name
            )

    # ── Fallback Logic (uses file-based meta-memory) ──────────
    def _smart_fallback_decision(self, current_round: int,
                                 opponent_name: str) -> Dict[str, str]:
        history = self.memory.match_history
        profile = self.db.load_profile(opponent_name) or {}

        # 1. ROUND 1: Use file history to detect Round-1 betrayers
        if current_round == 1:
            r1_def = profile.get("round_1_defections", 0)
            matches = profile.get("matches_played", 0)
            if matches >= 2 and (r1_def / matches) > 0.5:
                return {
                    "reasoning": "File memory: they betray Round 1 >50%.",
                    "decision": "Defect",
                    "message": "I remember your opening."
                }
            return {
                "reasoning": "Round 1: Being nice.",
                "decision": "Cooperate",
                "message": "Let's cooperate for a win-win!"
            }

        # 2. ANTI-GRIM TRIGGER
        if len(history) >= 2:
            last_two = [r["opponent_move"] for r in history[-2:]]
            if last_two == ["Defect", "Defect"]:
                return {
                    "reasoning": "Grim-Trigger detected. Locking defense.",
                    "decision": "Defect",
                    "message": "You forced this."
                }

        # 3. ROUND 7: Use file history for R7 betrayal rate
        if current_round == 7:
            r7_def = profile.get("round_7_defections", 0)
            matches = profile.get("matches_played", 0)
            r7_rate = (r7_def / matches * 100) if matches else 0
            if r7_rate == 0 and matches >= 2:
                return {
                    "reasoning": "File memory: they NEVER betray R7.",
                    "decision": "Cooperate",
                    "message": "Trust verified by history."
                }
            return {
                "reasoning": "Round 7: High betrayal risk.",
                "decision": "Defect",
                "message": "Endgame maneuver."
            }

        # 4. TIT-FOR-TAT
        last_opp = history[-1]["opponent_move"] if history else "Cooperate"
        decision = "Defect" if last_opp == "Defect" else "Cooperate"
        msg = "Let's keep cooperating!" if decision == "Cooperate" \
            else "Adjusting my strategy."
        return {
            "reasoning": f"Retaliating to {last_opp}.",
            "decision": decision,
            "message": msg
        }

    # ── LLM Call (injects file-based meta-profile) ────────────
    def _call_llm_reasoning(self, prompt: str, current_round: int,
                            opponent_name: str) -> Dict[str, str]:
        if not self.api_key:
            return self._smart_fallback_decision(current_round, opponent_name)

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 🧠 Load persistent profile from disk
        meta_profile = self.db.get_meta_profile_string(opponent_name)

        # Load recent match replays for extra context
        recent = self.db.load_recent_matches(opponent_name, n=2)
        recent_summary = ""
        if recent:
            recent_summary = "\nRECENT MATCH REPLAYS:\n"
            for m in recent:
                recent_summary += (
                    f"  Match {m['match_number']} "
                    f"(defect rate {m['match_defect_rate']}%): "
                    f"{[r['opponent_move'] for r in m['rounds']]}\n"
                )

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an elite Game Theory AI playing Iterated "
                        "Prisoner's Dilemma.\n"
                        "Payoffs: (C,C)=3,3 | (D,C)=5,0 | "
                        "(C,D)=0,5 | (D,D)=1,1.\n\n"
                        f"OPPONENT FILE PROFILE: {meta_profile}\n"
                        f"{recent_summary}\n"
                        "YOUR CORE STRATEGY:\n"
                        "1. If a STRATEGY SHIFT is detected, trust the "
                        "RECENT trend, not the historical average.\n"
                        "2. RETALIATING: Defect if they defected last round.\n"
                        "3. ANTI-GRIM: Two defections in a row = permanent "
                        "defect. Do NOT forgive.\n"
                        "4. MESSAGE ALIGNMENT: NEVER say 'cooperate' or "
                        "'trust' when your decision is Defect.\n\n"
                        "Respond STRICTLY in JSON:\n"
                        '{"reasoning":"...","decision":"Cooperate" or '
                        '"Defect","message":"..."}'
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
                return json.loads(
                    res.json()["choices"][0]["message"]["content"]
                )
        except Exception:
            pass
        return self._smart_fallback_decision(current_round, opponent_name)

    # ── Main Turn Processor ───────────────────────────────────
    def process_turn(self, current_round: int,
                     opponent_last_move: str = None,
                     my_last_move: str = None,
                     my_points_earned: int = None,
                     opponent_last_msg: str = "",
                     opponent_name: str = "Unknown") -> Dict[str, Any]:

        if current_round > 1 and my_last_move:
            if not opponent_last_move and my_points_earned is not None:
                if my_last_move == "Cooperate":  # FIXED: was "my_move"
                    opponent_last_move = (
                        "Defect" if my_points_earned == 0 else "Cooperate"
                    )
                elif my_last_move == "Defect":
                    opponent_last_move = (
                        "Cooperate" if my_points_earned == 5 else "Defect"
                    )
            if opponent_last_move:
                self.memory.reflect_and_update(
                    current_round - 1, my_last_move,
                    opponent_last_move, opponent_last_msg
                )

        context_prompt = (
            f"Current Round: {current_round}/7\n"
            f"Opponent: {opponent_name}\n"
            f"Current Match: {json.dumps(self.memory.match_history)}\n"
            f"Opponent's Latest Message: '{opponent_last_msg}'\n\n"
            f"Combine current match data with your FILE-BASED META-MEMORY."
        )

        response = self._call_llm_reasoning(
            context_prompt, current_round, opponent_name
        )
        return {
            "decision": response.get("decision", "Cooperate").strip(),
            "message": response.get("message", "Let's cooperate."),
            "reasoning": response.get("reasoning", "Autonomous.")
        }