"""
   RAFAY
arena_simulator.py - 1v1 Agent Tournament
"""
import os
import time
from typing import Dict, Tuple
from agent import TrustArenaAgent
from agent_v4 import Agent_4
from agent_v5 import Agent_5
from agent_v6 import Agent_6

# FIXED: Removed trailing spaces in keys to prevent KeyError
PAYOFFS = {
    ("Cooperate", "Cooperate"): (3, 3),
    ("Cooperate", "Defect"): (0, 5),
    ("Defect", "Cooperate"): (5, 0),
    ("Defect", "Defect"): (1, 1),
}

def run_match(agent_a, agent_b) -> Tuple[int, int]:
    score_a, score_b = 0, 0
    
    # Reset memory safely for both agents
    if hasattr(agent_a, 'memory'):
        agent_a.memory = type(agent_a.memory)()
    if hasattr(agent_b, 'memory'):
        agent_b.memory = type(agent_b.memory)()
        
    last_move_a, last_move_b = None, None
    msg_a, msg_b = "", ""
    
    for r in range(1, 8):
        time.sleep(1.2)  # Delay to prevent Rate Limits
        
        res_a = agent_a.process_turn(
            current_round=r, opponent_last_move=last_move_b, 
            my_last_move=last_move_a, opponent_last_msg=msg_b
        )
        move_a = res_a["decision"].strip()
        msg_a = res_a["message"]
        
        res_b = agent_b.process_turn(
            current_round=r, opponent_last_move=last_move_a, 
            my_last_move=last_move_b, opponent_last_msg=msg_a
        )
        move_b = res_b["decision"].strip()
        msg_b = res_b["message"]
        
        # Fallback if LLM returns something unexpected
        if move_a not in ["Cooperate", "Defect"]: move_a = "Defect"
        if move_b not in ["Cooperate", "Defect"]: move_b = "Defect"
            
        pts_a, pts_b = PAYOFFS[(move_a, move_b)]
        score_a += pts_a
        score_b += pts_b
        
        last_move_a, last_move_b = move_a, move_b
        print(f"  Round {r}: A={move_a:<10} | B={move_b:<10} | Scores: A={score_a}, B={score_b}")
        
    return score_a, score_b

def run_1v1_tournament():
    api_key = os.getenv("GROQ_API_KEY", "")
    
    agent1 = TrustArenaAgent(api_key=api_key)
    agent2 = Agent_4(api_key=api_key)
    
    agent1.name = "TrustArenaAgent (Llama-3.3)"
    agent2.name = "Agent_5 (Generous, Forgiving)"
    
    all_participants = [agent1, agent2]
    total_scores: Dict[str, int] = {p.name: 0 for p in all_participants}
    
    print("==================================================")
    print("🚀 1v1 AGENTS TOURNAMENT")
    print("==================================================")
    
    # Run 3 matches to see who dominates overall
    num_matches = 3
    for match_num in range(1, num_matches + 1):
        print(f"\n--- MATCH {match_num} ---")
        s1, s2 = run_match(agent1, agent2)
        total_scores[agent1.name] += s1
        total_scores[agent2.name] += s2
        print(f"⚔️ {agent1.name} ({s1} pts) vs {agent2.name} ({s2} pts)")
        
    print("\n==================================================")
    print("🏆 FINAL LEADERBOARD")
    print("==================================================")
    sorted_leaderboard = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (name, total_pts) in enumerate(sorted_leaderboard, start=1):
        crown = "🥇" if rank == 1 else "🥈" if rank == 2 else "  "
        print(f"{crown} Rank {rank}: {name:<35} | Total Points: {total_pts}")

# FIXED: Corrected __name__ == "__main__" syntax and indentation
if __name__ == "__main__":
    run_1v1_tournament()