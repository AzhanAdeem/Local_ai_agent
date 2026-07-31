"""
opponent_database.py - Persistent File-Based Opponent Memory System
Survives program restarts. Detects strategy shifts between matches.
"""
import json
import os
from typing import Dict, Any, List
from datetime import datetime


class OpponentDatabase:
    """Manages a JSON file system that stores every match replay and 
    detects when opponents change their strategy."""

    def __init__(self, base_dir: str = "opponent_database"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self._ensure_registry()

    # ── File I/O Helpers ──────────────────────────────────────
    def _save_json(self, path: str, data: dict):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_json(self, path: str) -> dict:
        if not os.path.exists(path):
            return {}
        with open(path, 'r') as f:
            return json.load(f)

    def _ensure_registry(self):
        path = os.path.join(self.base_dir, "opponent_registry.json")
        if not os.path.exists(path):
            self._save_json(path, {"opponents": [], "last_updated": ""})

    def _safe_name(self, name: str) -> str:
        """Sanitize opponent name for use as a folder name."""
        return "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()

    def _get_opponent_dir(self, opponent_name: str) -> str:
        opp_dir = os.path.join(self.base_dir, self._safe_name(opponent_name))
        os.makedirs(opp_dir, exist_ok=True)
        return opp_dir

    # ── Core: Save a Completed Match ──────────────────────────
    def save_match(self, opponent_name: str, match_history: List[Dict],
                   my_name: str = "Agent_5"):
        """Called at the end of every match. Saves round-by-round replay
        to disk and updates the opponent's permanent profile."""

        opp_dir = self._get_opponent_dir(opponent_name)
        profile_path = os.path.join(opp_dir, "profile.json")
        profile = self._load_json(profile_path)

        # Initialize profile if first time facing this opponent
        if not profile:
            profile = {
                "opponent_name": opponent_name,
                "matches_played": 0,
                "total_rounds": 0,
                "total_defections": 0,
                "round_1_defections": 0,
                "round_7_defections": 0,
                "liar_incidents": 0,
                "match_defect_rates": [],
                "strategy_phases": [],
                "current_strategy_label": "UNKNOWN",
                "last_updated": ""
            }

        match_num = profile["matches_played"] + 1

        # ── Compute match-level stats ──
        match_defects = sum(1 for r in match_history if r["opponent_move"] == "Defect")
        total_rounds = len(match_history)
        match_defect_rate = (match_defects / total_rounds * 100) if total_rounds else 0

        # ── Save full round-by-round replay ──
        match_data = {
            "match_number": match_num,
            "timestamp": datetime.now().isoformat(),
            "my_name": my_name,
            "opponent_name": opponent_name,
            "match_defect_rate": round(match_defect_rate, 1),
            "rounds": match_history
        }
        self._save_json(
            os.path.join(opp_dir, f"match_{match_num:03d}.json"), match_data
        )

        # ── Update aggregated profile ──
        profile["matches_played"] = match_num
        profile["total_rounds"] += total_rounds
        profile["total_defections"] += match_defects
        profile["match_defect_rates"].append(round(match_defect_rate, 1))
        profile["last_updated"] = datetime.now().isoformat()

        for r in match_history:
            if r.get("round") == 1 and r["opponent_move"] == "Defect":
                profile["round_1_defections"] += 1
            if r.get("round") == 7 and r["opponent_move"] == "Defect":
                profile["round_7_defections"] += 1
            msg_lower = r.get("opponent_msg", "").lower()
            if ("cooperat" in msg_lower or "trust" in msg_lower or "friend" in msg_lower) \
                    and r["opponent_move"] == "Defect":
                profile["liar_incidents"] += 1

        # ── STRATEGY DRIFT DETECTION ──
        rates = profile["match_defect_rates"]
        if len(rates) >= 2:
            historical_avg = sum(rates[:-1]) / len(rates[:-1])
            latest_rate = rates[-1]
            drift = abs(latest_rate - historical_avg)

            if drift > 25:  # 25 percentage-point threshold
                direction = "AGGRESSIVE" if latest_rate > historical_avg else "COOPERATIVE"
                profile["strategy_phases"].append({
                    "detected_at_match": match_num,
                    "previous_avg_defect_rate": round(historical_avg, 1),
                    "new_defect_rate": round(latest_rate, 1),
                    "drift_magnitude": round(drift, 1),
                    "shift_direction": direction
                })
                profile["current_strategy_label"] = f"SHIFTED_TO_{direction}"
            elif not profile["strategy_phases"]:
                profile["current_strategy_label"] = "CONSISTENT"

        self._save_json(profile_path, profile)

        # ── Update master registry ──
        reg_path = os.path.join(self.base_dir, "opponent_registry.json")
        registry = self._load_json(reg_path)
        if opponent_name not in registry.get("opponents", []):
            registry["opponents"].append(opponent_name)
        registry["last_updated"] = datetime.now().isoformat()
        self._save_json(reg_path, registry)

        print(f"  💾 Saved match {match_num} vs '{opponent_name}' to disk.")

    # ── Load Profile for Prompt Injection ─────────────────────
    def load_profile(self, opponent_name: str) -> Dict[str, Any]:
        opp_dir = self._get_opponent_dir(opponent_name)
        return self._load_json(os.path.join(opp_dir, "profile.json"))

    def load_recent_matches(self, opponent_name: str, n: int = 3) -> List[Dict]:
        """Load the last N match replays for deep analysis."""
        opp_dir = self._get_opponent_dir(opponent_name)
        profile = self.load_profile(opponent_name)
        if not profile:
            return []
        total = profile.get("matches_played", 0)
        matches = []
        for i in range(max(1, total - n + 1), total + 1):
            m = self._load_json(os.path.join(opp_dir, f"match_{i:03d}.json"))
            if m:
                matches.append(m)
        return matches

    def get_meta_profile_string(self, opponent_name: str) -> str:
        """Builds the text block injected into the LLM system prompt."""
        profile = self.load_profile(opponent_name)
        if not profile or profile.get("matches_played", 0) == 0:
            return "NO PRIOR BATTLES. Treat as unknown."

        m = profile["matches_played"]
        r1 = (profile["round_1_defections"] / m) * 100
        r7 = (profile["round_7_defections"] / m) * 100
        overall = (profile["total_defections"] / profile["total_rounds"]) * 100

        rates = profile.get("match_defect_rates", [])
        recent = rates[-3:] if len(rates) >= 3 else rates
        recent_avg = sum(recent) / len(recent) if recent else 0

        label = profile.get("current_strategy_label", "UNKNOWN")
        phases = profile.get("strategy_phases", [])

        drift_warning = ""
        if phases:
            last = phases[-1]
            drift_warning = (
                f" ⚠️ STRATEGY SHIFT at match {last['detected_at_match']}: "
                f"defect rate went {last['previous_avg_defect_rate']}% → "
                f"{last['new_defect_rate']}% ({last['shift_direction']}). "
                f"PRIORITIZE RECENT BEHAVIOR over old data!"
            )

        return (
            f"🧠 META-MEMORY ({m} past matches): "
            f"Overall Defect: {overall:.1f}% | "
            f"Recent Trend (last {len(recent)}): {recent_avg:.1f}% | "
            f"R1 Betrayal: {r1:.1f}% | R7 Betrayal: {r7:.1f}% | "
            f"Liar Incidents: {profile['liar_incidents']} | "
            f"Strategy: {label}.{drift_warning}"
        )

    def list_all_opponents(self) -> List[str]:
        reg = self._load_json(os.path.join(self.base_dir, "opponent_registry.json"))
        return reg.get("opponents", [])