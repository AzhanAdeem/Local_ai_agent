"""
RAFAY
detector.py - Precise Opponent Profiling Engine
"""

from typing import List

class OpponentTracker:
    def __init__(self):
        self.opponent_history: List[str] = []
        self.my_history: List[str] = []
        self.messages: List[str] = []

    def update_history(self, my_move: str, opponent_move: str, message: str = ""):
        if my_move:
            self.my_history.append(my_move)
        if opponent_move:
            self.opponent_history.append(opponent_move)
        if message:
            self.messages.append(message)

    @property
    def total_rounds(self) -> int:
        return len(self.opponent_history)

    def classify_opponent(self) -> str:
        rounds = self.total_rounds
        if rounds == 0:
            return "UNKNOWN"

        # 1. Check PREDATOR: Always defects
        if all(move == "Defect" for move in self.opponent_history):
            return "PREDATOR"

        # 2. Check PACIFIST: Cooperated even AFTER we defected!
        for i in range(1, rounds):
            if self.my_history[i - 1] == "Defect" and self.opponent_history[i] == "Cooperate":
                return "PACIFIST"

        # 3. Check MIRROR: Copies our (N-1) move exactly
        if rounds >= 2:
            is_mirror = True
            for i in range(1, rounds):
                if self.opponent_history[i] != self.my_history[i - 1]:
                    is_mirror = False
                    break
            if is_mirror:
                return "MIRROR"

        return "DYNAMIC"