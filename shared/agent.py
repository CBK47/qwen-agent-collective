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
        ...

    def write(self, spec: AgentSpec, task: AgentTask, result: AgentResult) -> None:
        ...


class NullMemoryStore:
    """Memory adapter for agents before the real brain client exists."""

    def read(self, spec: AgentSpec, task: AgentTask) -> MemoryBundle:
        return MemoryBundle()

    def write(self, spec: AgentSpec, task: AgentTask, result: AgentResult) -> None:
        return None


class BaseAgent:
    """Template method implementation of the collective agent lifecycle."""

    def __init__(
        self,
        spec: AgentSpec,
        *,
        ai: DashScopeClient | None = None,
        memory: MemoryStore | None = None,
    ):
        self.spec = spec
        self.ai = ai or DashScopeClient()
        self.memory = memory or NullMemoryStore()

    def run(self, instruction: str, **metadata: Any) -> AgentResult:
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
        return self.memory.read(self.spec, task)

    def write_project_memory(self, task: AgentTask, result: AgentResult) -> None:
        self.memory.write(self.spec, task, result)

    def generate(
        self,
        task: AgentTask,
        memory: MemoryBundle,
        *,
        previous_output: str,
        previous_validation: ValidationResult,
    ) -> str:
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
        """Override in concrete agents to run tests, lint, schema checks, etc."""
        return ValidationResult(ok=bool(output.strip()), output="non-empty output")
