"""
arena_simulator.py - 5 Multi-Model Agents Tournament
"""

import os
import time
from typing import Dict, Tuple
from agent import TrustArenaAgent
#from opponents import get_5_multimodel_opponents
from agent_v4 import Agent_4;

PAYOFFS = {
    ("Cooperate", "Cooperate"): (3, 3),
    ("Cooperate", "Defect"): (0, 5),
    ("Defect", "Cooperate"): (5, 0),
    ("Defect", "Defect"): (1, 1),
}

def run_match(agent_a, agent_b) -> Tuple[int, int]:
    score_a, score_b = 0, 0
    
    if hasattr(agent_a, 'memory'):
        agent_a.memory = type(agent_a.memory)()
    if hasattr(agent_b, 'reset_memory'):
        agent_b.reset_memory()

    last_move_a, last_move_b = None, None
    msg_a, msg_b = "", ""

    for r in range(1, 8):
        time.sleep(1.2)  # Delay to prevent Rate Limits

        res_a = agent_a.process_turn(
            current_round=r,
            opponent_last_move=last_move_b,
            my_last_move=last_move_a,
            opponent_last_msg=msg_b
        )
        move_a, msg_a = res_a["decision"], res_a["message"]

        res_b = agent_b.process_turn(
            current_round=r,
            opponent_last_move=last_move_a,
            my_last_move=last_move_b,
            opponent_last_msg=msg_a
        )
        move_b, msg_b = res_b["decision"], res_b["message"]

        pts_a, pts_b = PAYOFFS[(move_a, move_b)]
        score_a += pts_a
        score_b += pts_b

        last_move_a, last_move_b = move_a, move_b

    return score_a, score_b

def run_5_agent_tournament():
    api_key = os.getenv("GROQ_API_KEY", "")
    primary_agent = TrustArenaAgent(api_key=api_key)
    competitors = get_5_multimodel_opponents(api_key=api_key)

    all_participants = [primary_agent] + competitors
    primary_agent.name = "OUR_PRIMARY_AGENT (Llama-3.3-70b)"

    total_scores: Dict[str, int] = {p.name: 0 for p in all_participants}

    print("==================================================")
    print("🚀 5 MULTI-MODEL AGENTS TOURNAMENT")
    print("==================================================")

    for i in range(len(all_participants)):
        for j in range(i + 1, len(all_participants)):
            p1 = all_participants[i]
            p2 = all_participants[j]

            s1, s2 = run_match(p1, p2)
            total_scores[p1.name] += s1
            total_scores[p2.name] += s2

            print(f"⚔️ {p1.name:<32} ({s1:<2} pts) vs {p2.name:<25} ({s2:<2} pts)")

    print("\n==================================================")
    print("🏆 5 MULTI-MODEL LEADERBOARD")
    print("==================================================")
    
    sorted_leaderboard = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    
    for rank, (name, total_pts) in enumerate(sorted_leaderboard, start=1):
        crown = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        print(f"{crown} Rank {rank}: {name:<35} | Total Points: {total_pts}")

if __name__ == "__main__":
    run_5_agent_tournament()