import ollama
import json

# ==========================================
# 1. THE MEMORY (The Notebook)
# ==========================================
# We start with an empty list. We will add what happens each round here.
game_history = []

# ==========================================
# 2. THE BRAIN (The Prompt)
# ==========================================
def get_decision(round_num, opponent_name, history):
    # Turn the history list into a readable text string for the LLM
    history_text = "No previous rounds."
    if history:
        history_text = "\n".join([
            f"Round {h['round']}: You chose {h['my_move']}, Opponent chose {h['opponent_move']}. They said: '{h.get('opponent_msg', '')}'"
            for h in history
        ])

    # This is the instruction we give to the LLM
    prompt = f"""You are playing a 7-round game called the Iterated Prisoner's Dilemma.
    SCORES: 
    - Both Cooperate: +3 points each
    - You Defect, They Cooperate: +5 for you, 0 for them
    - Both Defect: +1 point each
    - You Cooperate, They Defect: 0 for you, +6 for them
    
    Current Round: {round_num} of 7.
    Opponent Name: {opponent_name}
    Game History:
    {history_text}

    YOUR TASK:
    1. Decide if you will "COOPERATE" or "DEFECT" this round.
    2. Write a short message (max 100 characters) to the opponent.
    
    You MUST reply ONLY with a valid JSON object in this exact format:
    {{
        "reasoning": "One sentence on why you chose this",
        "message": "Your short message to the opponent",
        "decision": "COOPERATE" or "DEFECT"
    }}"""

    # ==========================================
    # 3. THE ACTION (Calling Ollama)
    # ==========================================
    try:
        # We ask Ollama to generate a response using the llama3.2 model
        response = ollama.chat(model='llama3.2', messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        # Get the raw text the LLM gave us
        raw_text = response['message']['content']
        print(f"\n--- Raw LLM Response ---\n{raw_text}\n----------------------")

        # Clean up the text in case the LLM adds markdown code blocks (like ```json ... ```)
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        # Convert the text into a Python dictionary we can use
        result = json.loads(raw_text)
        
        # Extract the decision and make sure it's valid and uppercase
        decision = result.get("decision", "DEFECT").strip().upper()
        if decision not in ["COOPERATE", "DEFECT"]:
            decision = "DEFECT" # Safety fallback
            
        message = result.get("message", "Let's play.")[:100] # Cut off at 100 chars
        
        return decision, message

    except Exception as e:
        # If the LLM crashes or gives bad JSON, we don't want the whole program to fail.
        # We fall back to a safe default.
        print(f"⚠️ Error reading LLM response: {e}")
        return "DEFECT", "System error, playing safely."


# ==========================================
# LET'S TEST IT! (Simulating a 3-round game)
# ==========================================
if __name__ == "__main__":
    opponent = "TestOpponent"
    
    for round_num in range(1, 4): # Simulating 3 rounds
        print(f"\n=== ROUND {round_num} ===")
        
        # 1. Get our agent's decision
        my_decision, my_message = get_decision(round_num, opponent, game_history)
        print(f"🤖 My Agent decided: {my_decision}")
        print(f"🤖 My Agent's message: '{my_message}'")
        
        # 2. Simulate the opponent's response (Let's pretend they always cooperate)
        opponent_decision = "COOPERATE" 
        opponent_msg = "I trust you!"
        
        # 3. Save this round to our memory (The Notebook)
        game_history.append({
            "round": round_num,
            "my_move": my_decision,
            "opponent_move": opponent_decision,
            "opponent_msg": opponent_msg
        })
        
        print(f"📝 History updated. Opponent played: {opponent_decision}")