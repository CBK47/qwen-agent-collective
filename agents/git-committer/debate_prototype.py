import os
from shared.dashscope import chat

# Define Personas
PERSONAS = {
    "Pedant": "You are 'The Pedant'. Your sole focus is style, naming conventions, and strict adherence to the project's house rules. Be nitpicky. If a variable name is slightly off or a comment is missing, point it out.",
    "Architect": "You are 'The Architect'. You care about system design, complexity, scalability, and logic flow. Ignore style; focus on whether this code actually makes sense and doesn't introduce technical debt.",
    "Skeptic": "You are 'The Skeptic'. Your job is to find reasons why this change should be REJECTED. Look for edge cases, bugs, or simpler ways to achieve the same result. Be a devil's advocate.",
    "Synthesizer": "You are the Synthesis Agent. You will receive reports from a Pedant, an Architect, and a Skeptic. Your goal is to resolve their disagreements and produce a final, polished Conventional Commit message."
}

def run_debate(diff):
    print(f"--- Starting Debate for Diff ---\n{diff}\n")
    
    # 1. The Pedant's Review
    pedant_prompt = f"{PERSONAS['Pedant']}\n\nReview this diff:\n{diff}"
    pedant_review = chat(pedant_prompt)
    print(f"PEDANT: {pedant_review}\n")

    # 2. The Architect's Review (receives the diff + pedant's notes for context)
    arch_prompt = f"{PERSONAS['Architect']}\n\nDiff:\n{diff}\n\nPedant says: {pedant_review}\n\nProvide your architectural review."
    arch_review = chat(arch_prompt)
    print(f"ARCHITECT: {arch_review}\n")

    # 3. The Skeptic's Review (receives all previous notes)
    skeptic_prompt = f"{PERSONAS['Skeptic']}\n\nDiff:\n{diff}\n\nPedant says: {pedant_review}\n\nArchitect says: {arch_review}\n\nFind the holes in this change."
    skeptic_review = chat(skeptic_prompt)
    print(f"SKEPTIC: {skeptic_review}\n")

    # 4. Synthesis (Final Verdict)
    synth_prompt = f"{PERSONAS['Synthesizer']}\n\nDiff:\n{diff}\n\nReports:\nPedant: {pedant_review}\nArchitect: {arch_review}\nSkeptic: {skeptic_review}\n\nProduce a final Conventional Commit message and a brief summary of the verdict."
    final_verdict = chat(synth_prompt)
    print(f"--- FINAL VERDICT ---\n{final_verdict}")

if __name__ == "__main__":
    # Sample diff: changing some logic in a dummy function
    sample_diff = """
- def calculate_total(price, tax):
-     return price + (price * tax)
+ def calculate_total(price: float, tax: float) -> float:
+     \"\"\"Calculate the final price with tax.\"\"\"
+     if price < 0: raise ValueError('Price cannot be negative')
+     return float(price * (1 + tax))
    """
    run_debate(sample_diff)
        skeptic_prompt = f"{PERSONAS['Skeptic']}\n\nDiff:\n{diff}\n\nPedant says: {pedant_review}\n\nArchitect says: {arch_review}\n\nProvide your skeptical review."
        skeptic_review = chat(skeptic_prompt)
        print(f"SKEPTIC: {skeptic_review}\n")
def synthesize_reviews(diff, pedant_review, arch_review, skeptic_review):
    \"\"\"Synthesizes reviews from Pedant, Architect, and Skeptic to produce a final verdict.

    TODO: Implement the actual synthesis logic using the chat function with the appropriate prompt.
    \"\"\"
    # TODO: Implement the synthesis logic
    return "Synthesis not yet implemented"
def run_debate():
    # TODO: Implement synthesis step using Synthesizer persona to generate final commit message
def synthesize_reviews(pedant_review: str, arch_review: str, skeptic_review: str) -> str:
    """Synthesizes reviews into a final commit message."""
    # TODO: Implement synthesis logic using Synthesizer persona
    return "feat: stubbed synthesis"
import os
from shared.dashscope import chat

PERSONAS = {
    "Pedant": "You are 'The Pedant'. Your sole focus is style, naming conventions, and strict adherence to the project's house rules. Be nitpicky. If a variable name is slightly off or a comment is missing, point it out.",
    "Architect": "You are 'The Architect'. You care about system design, complexity, scalability, and logic flow. Ignore style; focus on whether this code actually makes sense and doesn't introduce technical debt.",
    "Skeptic": "You are 'The Skeptic'. Your job is to find reasons why this change should be REJECTED. Look for edge cases, bugs, or simpler ways to achieve the same result. Be a devil's advocate.",
    "Synthesizer": "You are the Synthesis Agent. You will receive reports from a Pedant, an Architect, and a Skeptic. Your goal is to resolve their disagreements and produce a final, polished Conventional Commit message."
}

def run_debate(diff):
    print(f"--- Starting Debate for Diff ---\n{diff}\n")
    
    # 1. The Pedant's Review
    pedant_prompt = f"{PERSONAS['Pedant']}\n