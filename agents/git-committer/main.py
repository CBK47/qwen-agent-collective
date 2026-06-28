import re
from typing import Any, Mapping
from shared.agent import BaseAgent, AgentSpec, AgentTask, MemoryBundle, ValidationResult, ReviewResult, AgentResult, NullMemoryStore
from shared.dashscope import DashScopeClient
import os
from flask import Flask, request
from shared.code_conventions import get_code_conventions

class GitCommitterAgent(BaseAgent):
    """
    Productionizes the git-committer debate prototype into a structured agent.
    Implements the 'Multi-Role Negotiation Loop' for collaborative review.
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
        
        # Retrieve code conventions from shared module
        code_conventions = get_code_conventions()
        
        # Handle iteration context
        repair_context = ""
        if previous_output or previous_validation.output:
            repair_context = f"\n\nPrevious attempt failed validation:\n{previous_validation.output}\nRevise the result."

        print(f"--- Starting Multi-Role Negotiation Loop for Session {task.session_id} ---")

        current_pedant = None
        current_arch = None
        current_skeptic = None

        for round in range(3):
            # Pedant's turn
            pedant_prompt = f"{self.PERSONAS['Pedant']}\n\nContext:\n{context}\n\nCode Conventions:\n{code_conventions}\n\nDiff:\n{diff}\n\n"
            if current_arch is not None:
                pedant_prompt += f"Architect's previous review: {current_arch}\n"
            if current_skeptic is not None:
                pedant_prompt += f"Skeptic's previous review: {current_skeptic}\n"
            pedant_prompt += "\nProvide your review."
            current_pedant = self.ai.chat(pedant_prompt, temperature=0)
            print(f"[PEDANT ROUND {round+1}]: {current_pedant}")

            # Architect's turn
            arch_prompt = f"{self.PERSONAS['Architect']}\n\nContext:\n{context}\n\nCode Conventions:\n{code_conventions}\n\nDiff:\n{diff}\n\n"
            if current_pedant is not None:
                arch_prompt += f"Pedant's review: {current_pedant}\n"
            if current_skeptic is not None:
                arch_prompt += f"Skeptic's review: {current_skeptic}\n"
            arch_prompt += "\nProvide your review."
            current_arch = self.ai.chat(arch_prompt, temperature=0)
            print(f"[ARCHITECT ROUND {round+1}]: {current_arch}")

            # Skeptic's turn
            skeptic_prompt = f"{self.PERSONAS['Skeptic']}\n\nContext:\n{context}\n\nCode Conventions:\n{code_conventions}\n\nDiff:\n{diff}\n\n"
            if current_pedant is not None:
                skeptic_prompt += f"Pedant's review: {current_pedant}\n"
            if current_arch is not None:
                skeptic_prompt += f"Architect's review: {current_arch}\n"
            skeptic_prompt += "\nFind the holes in this change."
            current_skeptic = self.ai.chat(skeptic_prompt, temperature=0)
            print(f"[SKEPTIC ROUND {round+1}]: {current_skeptic}")

        # 4. Synthesis (Final Verdict)
        synth_prompt = (
            f"{self.PERSONAS['Synthesizer']}\n\n"
            f"Context:\n{context}\n\n"
            f"Code Conventions:\n{code_conventions}\n\n"
            f"Diff:\n{diff}\n\n"
            f"Reports:\nPedant: {current_pedant}\nArchitect: {current_arch}\nSkeptic: {current_skeptic}\n\n"
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

app = Flask(__name__)

spec = AgentSpec(
    agent_id="git-committer", 
    name="Git Committer", 
    role=" commit message synthesizer",
    model=None,
    api_key=os.getenv("DASHSCOPE_API_KEY")
)
    
agent = GitCommitterAgent(spec=spec, memory=NullMemoryStore())

@app.route('/')
def home():
    return """
    <form action="/submit" method="post">
        <textarea name="diff" rows="10" cols="50"></textarea>
        <input type="submit" value="Submit">
    </form>
    """

@app.route('/submit', methods=['POST'])
def submit():
    diff = request.form['diff']
    result = agent.run(diff)
    return f"<pre>{result.output}</pre>"

if __name__ == "__main__":
    app.run(debug=True)
