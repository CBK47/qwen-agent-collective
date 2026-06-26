import re
from typing import Any, Mapping
from shared.agent import BaseAgent, AgentSpec, AgentTask, MemoryBundle, ValidationResult, ReviewResult, AgentResult
from shared.dashscope import DashScopeClient

class GitCommitterAgent(BaseAgent):
    """
    Productionizes the git-committer debate prototype into a structured agent.
    Implements the 'Triangular Debate Loop' (Pedant -> Architect -> Skeptic -> Synthesis).
    """

    PERSONAS = {
        "Pedant": "You are 'The Pedant'. Your sole focus is style, naming conventions, and strict adherence to the project's house rules. Be nitpicky. If a variable name is slightly off or a comment is missing, point it out.",
        "Architect": "You are 'The Architect'. You care about system design, complexity, scalability, and logic flow. Ignore style; focus on whether this code actually makes sense and doesn't introduce technical debt.",
        "Skeptic": "You are 'The Skeptic'. Your job is to find reasons why this change should be REJECTED. Look for edge cases, bugs, or simpler ways to achieve the same result. Be a devil's advocate.",
        "Synthesizer": "You are the Synthesis Agent. You will receive reports from a Pedant, an Architect, and a Skeptic. Your goal is to resolve their disagreements and produce a final, polished Conventional Commit message."
    }

    def generate(
        self, 
        task: AgentTask, 
        memory: MemoryBundle, 
        *, 
        previous_output: str, 
        previous_validation: ValidationResult
    ) -> str:
        # We assume the task.instruction contains the git diff
        diff = task.instruction
        context = memory.as_prompt_context()
        
        # Handle iteration context
        repair_context = ""
        if previous_output or previous_validation.output:
            repair_context = f"\n\nPrevious attempt failed validation:\n{previous_validation.output}\nRevise the result."

        print(f"--- Starting Triangular Debate for Session {task.session_id} ---")

        # 1. The Pedant's Review
        pedant_prompt = (
            f"{self.PERSONAS['Pedant']}\n\n"
            f"Context:\n{context}\n\n"
            f"Review this diff:\n{diff}"
        )
        pedant_review = self.ai.chat(pedant_prompt, temperature=0)
        print(f"[PEDANT]: {pedant_review}")

        # 2. The Architect's Review
        arch_prompt = (
            f"{self.PERSONAS['Architect']}\n\n"
            f"Context:\n{context}\n\n"
            f"Diff:\n{diff}\n\n"
            f"Pedant says: {pedant_review}\n\n"
            f"Provide your architectural review."
        )
        arch_review = self.ai.chat(arch_prompt, temperature=0)
        print(f"[ARCHITECT]: {arch_review}")

        # 3. The Skeptic's Review
        skeptic_prompt = (
            f"{self.PERSONAS['Skeptic']}\n\n"
            f"Context:\n{context}\n\n"
            f"Diff:\n{diff}\n\n"
            f"Pedant says: {pedant_review}\n\n"
            f"Architect says: {arch_review}\n\n"
            f"Find the holes in this change."
        )
        skeptic_review = self.ai.chat(skeptic_prompt, temperature=0)
        print(f"[SKEPTIC]: {skeptic_review}")

        # 4. Synthesis (Final Verdict)
        synth_prompt = (
            f"{self.PERSONAS['Synthesizer']}\n\n"
            f"Context:\n{context}\n\n"
            f"Diff:\n{diff}\n\n"
            f"Reports:\nPedant: {pedant_review}\nArchitect: {arch_review}\nSkeptic: {skeptic_review}\n\n"
            f"Produce a final Conventional Commit message and a brief summary of the verdict."
            f"{repair_context}"
        )
        final_verdict = self.ai.chat(synth_prompt, temperature=0)
        print(f"[SYNTHESIS]: {final_verdict}")

        return final_verdict

    def validate(self, task: AgentTask, output: str) -> ValidationResult:
        # Basic check for Conventional Commit format
        # Pattern: <type>[optional scope]: <description>
        pattern = r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(\w+\))?:\s.+$"
        
        # We look for the commit message line in the synthesis output 
        # since Synthesis usually returns a summary + the message.
        lines = output.split('\n')
        found_valid_commit = False
        for line in lines:
            if re.match(pattern, line.strip()):
                found_valid_commit = True
                break
        
        if found_valid_commit:
            return ValidationResult(ok=True, output="Conventional Commit pattern match found.")
        else:
            return ValidationResult(
                ok=False, 
                output="No valid Conventional Commit message found. Expected format: 'feat: add something' or 'fix(ui): fix bug'"
            )

if __name__ == "__main__":
    # Simple test run
    spec = AgentSpec(
        agent_id="git-committer", 
        name="Git Committer", 
        role=" commit message synthesizer",
        model=None # uses default from DashScopeClient
    )
    
    # Mocking memory store for a quick test
    from shared.agent import NullMemoryStore
    agent = GitCommitterAgent(spec=spec, memory=NullMemoryStore())
    
    sample_diff = """- def add(a, b): return a + b
+ def add(a: int, b: int) -> int:
+     \"\"\"Adds two integers.\"\"\"
+     return a + b"""
    
    result = agent.run(sample_diff)
    print(f"\nFINAL RESULT:\n{result.output}")
def generate(
    self, 
    task: AgentTask, 
    memory: MemoryBundle, 
    *, 
    previous_output: str, 
    previous_validation: ValidationResult
) -> str:
    diff = task.instruction
    context = memory.as_prompt_context()
    # TODO: Implement debate loop by calling run_debate and returning synthesized commit message.
