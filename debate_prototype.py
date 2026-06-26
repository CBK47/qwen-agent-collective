def synthesize_reviews(pedant_review: str, arch_review: str, skeptic_review: str) -> str:
    """Synthesizes the reviews from Pedant, Architect, and Skeptic into a final commit message."""
    synthesizer_prompt = f"{PERSONAS['Synthesizer']}\n\nPedant: {pedant_review}\n\nArchitect: {arch_review}\n\nSkeptic: {skeptic_review}\n\nProduce a final Conventional Commit message."
    synthesis = chat(synthesizer_prompt)
    print(f"SYNTHESIZER: {synthesis}\n")
    return synthesis
