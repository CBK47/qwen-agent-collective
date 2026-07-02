"""Reusable agent loop primitives.

This is deliberately small: agents can subclass `BaseAgent` and provide their
domain-specific generation, review, validation, and memory hooks without
forking the Qwen client or inventing a new execution loop each time.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from shared.dashscope import DashScopeClient

LOGGER = logging.getLogger("qwen_collective.agent")


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    name: str
    role: str
    model: str | None = None
    max_iterations: int = 2
    temperature: float | None = None
    max_tokens: int | None = None


@dataclass(frozen=True)
class AgentTask:
    instruction: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryBundle:
    facts: Sequence[str] = ()
    conventions: Sequence[str] = ()
    working_notes: Sequence[str] = ()

    def as_prompt_context(self) -> str:
        """Converts the memory bundle into a formatted string for use as prompt context.

        Returns:
            str: A formatted string containing project memory, conventions, and working notes, or "No prior memory supplied." if empty.
        """
        sections = [
            ("Project memory", self.facts),
            ("Project conventions", self.conventions),
            ("Working notes", self.working_notes),
        ]
        parts = []
        for title, values in sections:
            if values:
                parts.append(f"## {title}\n" + "\n".join(f"- {item}" for item in values))
        return "\n\n".join(parts) if parts else "No prior memory supplied."


@dataclass(frozen=True)
class ReviewResult:
    ok: bool
    notes: str = ""


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    command: str | None = None
    output: str = ""


@dataclass(frozen=True)
class AgentResult:
    ok: bool
    output: str
    review: ReviewResult
    validation: ValidationResult
    iterations: int
    session_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


class MemoryStore(Protocol):
    def read(self, spec: AgentSpec, task: AgentTask) -> MemoryBundle:
        """Reads the memory for the given agent spec and task.

        Args:
            spec (AgentSpec): The agent specification.
            task (AgentTask): The task for which to read memory.

        Returns:
            MemoryBundle: The memory bundle containing the relevant context.
        """
        ...

    def write(self, spec: AgentSpec, task: AgentTask, result: AgentResult) -> None:
        """Writes the result to the memory store.

        Args:
            spec (AgentSpec): The agent specification.
            task (AgentTask): The task associated with the result.
            result (AgentResult): The result to store.
        """
        ...


class NullMemoryStore:
    """Memory adapter for agents before the real brain client exists."""

    def read(self, spec: AgentSpec, task: AgentTask) -> MemoryBundle:
        """Reads the memory for the given agent spec and task, returning an empty MemoryBundle.

        Args:
            spec (AgentSpec): The agent specification.
            task (AgentTask): The task for which to read memory.

        Returns:
            MemoryBundle: An empty MemoryBundle instance.
        """
        return MemoryBundle()

    def write(self, spec: AgentSpec, task: AgentTask, result: AgentResult) -> None:
        """Writes the result to the memory store (no-op for NullMemoryStore).

        Args:
            spec (AgentSpec): The agent specification.
            task (AgentTask): The task associated with the result.
            result (AgentResult): The result to store.
        """
        return None


class BrainMemoryStore:
    """File-based memory store using /home/cbk/shared_drive/brain."""

    def __init__(self, base_path: str = "/home/cbk/shared_drive/brain"):
        self.base_path = base_path

    def _get_file_path(self, namespace: str) -> str:
        return f"{self.base_path}/{namespace}.txt"

    def read(self, spec: AgentSpec, task: AgentTask) -> MemoryBundle:
        """Reads project memory from the file-based storage.

        Args:
            spec (AgentSpec): The agent specification.
            task (AgentTask): The task for which to read memory.

        Returns:
            MemoryBundle: A bundle containing facts, conventions, and working notes from the memory store.
        """
        import shared.namespaces as ns
        import os
        bundle = MemoryBundle()
        facts, conventions, notes = [], [], []

        private_ns = getattr(ns, f"{spec.agent_id.upper()}_PRIVATE", None)
        if private_ns:
            path = self._get_file_path(private_ns)
            if os.path.exists(path):
                with open(path, "r") as f:
                    notes.append(f.read())

        if spec.agent_id == "git-committer" or "shared" in spec.role.lower():
            path = self._get_file_path(ns.SHARED_CODE_CONVENTIONS)
            if os.path.exists(path):
                with open(path, "r") as f:
                    conventions.append(f.read())

        return MemoryBundle(facts=facts, conventions=tuple(conventions), working_notes=tuple(notes))

    def write(self, spec: AgentSpec, task: AgentTask, result: AgentResult) -> None:
        """Writes the result to the file-based memory store.

        Args:
            spec (AgentSpec): The agent specification.
            task (AgentTask): The task associated with the result.
            result (AgentResult): The result to store.
        """
        import shared.namespaces as ns
        import os
        private_ns = getattr(ns, f"{spec.agent_id.upper()}_PRIVATE", None)
        if not private_ns:
            return
        path = self._get_file_path(private_ns)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(f"\n--- Session {result.session_id} ---\n{result.output}\n")


class BaseAgent:
    """Template method implementation of the collective agent lifecycle."""

    def __init__(
        self,
        spec: AgentSpec,
        *,
        ai: DashScopeClient | None = None,
        memory: MemoryStore | None = None,
    ):
        """Initialize the BaseAgent instance.

        Args:
            spec (AgentSpec): Agent specification containing configuration details.
            ai (DashScopeClient | None, optional): Optional AI client; defaults to a new DashScopeClient if not provided.
            memory (MemoryStore | None, optional): Optional memory store; defaults to NullMemoryStore if not provided.
        """
        self.spec = spec
        self.ai = ai or DashScopeClient()
        self.memory = memory or NullMemoryStore()

    def run(self, instruction: str, **metadata: Mapping[str, Any]) -> AgentResult:
        """Executes the agent's workflow by reading initial memory context, then iteratively generating, reviewing, and validating responses until both pass or max iterations are reached.

        This method processes the instruction by repeatedly generating a response, reviewing it, and validating it. If both review and validation pass, the process terminates early. Otherwise, it retries up to the specified maximum iterations.

        Args:
            instruction (str): The task instruction for the agent to process. This is the main input that the agent will work on.
            metadata (Mapping[str, Any]): Additional keyword arguments for the task, which is stored in the AgentTask and used across all steps of the agent's workflow.

        Returns:
            AgentResult: The outcome of the agent's execution, containing:
                - ok (bool): True if both review and validation passed; otherwise False.
                - output (str): The final generated output string.
                - review (ReviewResult): The result of the self-review step, including whether it passed and any notes.
                - validation (ValidationResult): The result of the validation step, including whether it passed and any details.
                - iterations (int): The number of iterations performed (up to spec.max_iterations).
                - session_id (str): A unique identifier for the task session.
                - metadata (Mapping[str, Any]): Additional metadata including the original task metadata and 'elapsed_ms' (total execution time in milliseconds).
        """
        task = AgentTask(instruction=instruction, metadata=metadata)
        started = time.monotonic()
        memory = self.read_project_context(task)
        output = ""
        review = ReviewResult(ok=False, notes="not reviewed")
        validation = ValidationResult(ok=False, output="not validated")

        for iteration in range(1, self.spec.max_iterations + 1):
            output = self.generate(task, memory, previous_output=output, previous_validation=validation)
            review = self.self_review(task, output, memory)
            validation = self.validate(task, output)
            if review.ok and validation.ok:
                result = AgentResult(
                    ok=True,
                    output=output,
                    review=review,
                    validation=validation,
                    iterations=iteration,
                    session_id=task.session_id,
                    metadata={"elapsed_ms": round((time.monotonic() - started) * 1000, 2)},
                )
                self.write_project_memory(task, result)
                return result
            LOGGER.info(
                "agent_iteration_retry",
                extra={
                    "agent_id": self.spec.agent_id,
                    "session_id": task.session_id,
                    "iteration": iteration,
                    "review_ok": review.ok,
                    "validation_ok": validation.ok,
                },
            )

        result = AgentResult(
            ok=False,
            output=output,
            review=review,
            validation=validation,
            iterations=self.spec.max_iterations,
            session_id=task.session_id,
            metadata={"elapsed_ms": round((time.monotonic() - started) * 1000, 2)},
        )
        self.write_project_memory(task, result)
        return result

    def read_project_context(self, task: AgentTask) -> MemoryBundle:
        """Read the project context from the memory store for the given task.

        Args:
            task (AgentTask): The task for which to read the memory context.

        Returns:
            MemoryBundle: The memory bundle containing the project context for the task.
        """
        return self.memory.read(self.spec, task)

    def write_project_memory(self, task: AgentTask, result: AgentResult) -> None:
        """Write the result to the project memory store.

        Args:
            task (AgentTask): The task associated with the result.
            result (AgentResult): The result to store in memory.

        Returns:
            None
        """
        self.memory.write(self.spec, task, result)

    def generate(
        self,
        task: AgentTask,
        memory: MemoryBundle,
        *,
        previous_output: str,
        previous_validation: ValidationResult,
    ) -> str:
        """Generate a response based on the task and memory context.

        Args:
            task (AgentTask): The task to process.
            memory (MemoryBundle): Current memory context for the agent.
            previous_output (str): The output from the previous generation step (if any).
            previous_validation (ValidationResult): The result of the previous validation step.

        Returns:
            str: The generated output string.
        """
        repair_context = ""
        if previous_output or previous_validation.output:
            repair_context = (
                "\n\nPrevious attempt failed validation. Revise it.\n"
                f"Validation output:\n{previous_validation.output}"
            )
        prompt = (
            f"You are {self.spec.name}, {self.spec.role}.\n\n"
            f"{memory.as_prompt_context()}\n\n"
            f"Task:\n{task.instruction}"
            f"{repair_context}"
        )
        return self.ai.chat(
            prompt,
            model=self.spec.model,
            temperature=self.spec.temperature,
            max_tokens=self.spec.max_tokens,
            metadata={
                "agent_id": self.spec.agent_id,
                "session_id": task.session_id,
                "phase": "generate",
                **dict(task.metadata),
            },
        )

    def self_review(self, task: AgentTask, output: str, memory: MemoryBundle) -> ReviewResult:
        """Review the generated output for correctness and quality.

        Args:
            task (AgentTask): The task being processed.
            output (str): The generated output to review.
            memory (MemoryBundle): Current memory context for the agent.

        Returns:
            ReviewResult: indicating whether the output is acceptable and any review notes.
        """
        prompt = (
            f"You are reviewing output from {self.spec.name}.\n"
            "Return exactly one line starting with PASS: or FAIL:, followed by a short reason.\n\n"
            f"Task:\n{task.instruction}\n\n"
            f"Context:\n{memory.as_prompt_context()}\n\n"
            f"Output:\n{output}"
        )
        text = self.ai.chat(
            prompt,
            model=self.spec.model,
            temperature=0,
            max_tokens=200,
            metadata={
                "agent_id": self.spec.agent_id,
                "session_id": task.session_id,
                "phase": "self_review",
            },
        ).strip()
        return ReviewResult(ok=text.upper().startswith("PASS:"), notes=text)

    def validate(self, task: AgentTask, output: str) -> ValidationResult:
        """Validate the generated output against specific criteria.

        This method should be overridden by concrete agent implementations to perform validation checks.

        Args:
            task (AgentTask): The task being processed.
            output (str): The generated output to validate.

        Returns:
            ValidationResult: indicating whether the output is valid and any associated details.
        """
        return ValidationResult(ok=bool(output.strip()), output="non-empty output")
