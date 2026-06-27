import os
from shared.dashscope import chat
from review import conventions

def review_single_role(role: str, context: str) -> str:
    persona = conventions.get(role)
    if persona is None:
        raise ValueError(f"Role '{role}' not found in conventions")
    prompt = f"{persona}\n\n{context}"
    return chat(prompt)

def synthesize_reviews(diff: str, pedant_review: str, arch_review: str, skeptic_review: str) -> str:
    """Synthesizes reviews from Pedant, Architect, and Skeptic into a final Conventional Commit message.

    Args:
        diff: The code diff being reviewed.
        pedant_review: Review from the Pedant persona.
        arch_review: Review from the Architect persona.
        skeptic_review: Review from the Skeptic persona.

    Returns:
        A string containing the final commit message and summary.
    """
    synth_prompt = f"{conventions['Synthesizer']}\n\nDiff:\n{diff}\n\nReports:\nPedant: {pedant_review}\nArchitect: {arch_review}\nSkeptic: {skeptic_review}\n\nProduce a final Conventional Commit message and a brief summary of the verdict."
    return chat(synth_prompt)

def run_debate(diff: str) -> None:
    """Runs a debate between multiple personas to review a code diff.

    Args:
        diff: The code diff to be reviewed.
    """
    parsed_diff = conventions.parse_diff(diff)
    print(f"--- Starting Debate for Diff ---\n{parsed_diff}\n")
    
    # 1. The Pedant's Review
    pedant_context = f"Review this diff:\n{parsed_diff}"
    pedant_review = review_single_role("Pedant", pedant_context)
    print(f"PEDANT: {pedant_review}\n")

    # 2. The Architect's Review (receives the diff + pedant's notes for context)
    arch_context = f"Diff:\n{parsed_diff}\n\nPedant says: {pedant_review}\n\nProvide your architectural review."
    arch_review = review_single_role("Architect", arch_context)
    print(f"ARCHITECT: {arch_review}\n")

    # 3. The Skeptic's Review (receives all previous notes)
    skeptic_context = f"Diff:\n{parsed_diff}\n\nPedant says: {pedant_review}\n\nArchitect says: {arch_review}\n\nFind the holes in this change."
    skeptic_review = review_single_role("Skeptic", skeptic_context)
    print(f"SKEPTIC: {skeptic_review}\n")

    # 4. Synthesis (Final Verdict)
    final_verdict = synthesize_reviews(parsed_diff, pedant_review, arch_review, skeptic_review)
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
