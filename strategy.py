"""
RAFAY
strategy.py - Dynamic Probing & Game-Theory Heuristics
"""

from detector import OpponentTracker

class GameStrategy:
    def __init__(self, tracker: OpponentTracker):
        self.tracker = tracker

    def decide_move(self, current_round: int) -> str:
        classification = self.tracker.classify_opponent()

        # Rule 1: Exploit PACIFIST completely (+5 points/round)
        if classification == "PACIFIST":
            return "Defect"

        # Rule 2: Absolute defense against PREDATOR
        if classification == "PREDATOR":
            return "Defect"

        # Rule 3: Backward Induction - Round 7 Betrayal
        if current_round == 7:
            return "Defect"

        # Rule 4: Baseline Trust Establishment
        if current_round == 1:
            return "Cooperate"

        # Rule 5: Round 3 Probing (To detect and exploit Pacifist)
        if current_round == 3:
            return "Defect"

        # Rule 6: Recovery after Round 3 probe if opponent retaliated (MIRROR recovery)
        if current_round == 4 and self.tracker.opponent_history[-1] == "Defect":
            return "Cooperate"

        # Rule 7: Tit-For-Tat Retaliation for general turns
        if self.tracker.opponent_history and self.tracker.opponent_history[-1] == "Defect":
            return "Defect"

        return "Cooperate"