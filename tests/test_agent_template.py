import unittest

from shared.agent import AgentSpec, BaseAgent, MemoryBundle


class FakeAI:
    def __init__(self):
        self.calls = []

    def chat(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        if kwargs["metadata"]["phase"] == "self_review":
            return "PASS: output satisfies the task"
        return "generated work"


class RecordingMemory:
    def __init__(self):
        self.writes = []

    def read(self, spec, task):
        return MemoryBundle(
            facts=("architecture memory",),
            conventions=("use shared.dashscope",),
        )

    def write(self, spec, task, result):
        self.writes.append((spec.agent_id, task.session_id, result.ok))


class AgentTemplateTests(unittest.TestCase):
    def test_agent_runs_memory_generate_review_validate_write(self):
        ai = FakeAI()
        memory = RecordingMemory()
        agent = BaseAgent(
            AgentSpec(agent_id="test", name="test-agent", role="tester"),
            ai=ai,
            memory=memory,
        )

        result = agent.run("do useful work")

        self.assertTrue(result.ok)
        self.assertEqual(result.output, "generated work")
        self.assertEqual(result.iterations, 1)
        self.assertEqual(len(ai.calls), 2)
        self.assertEqual(memory.writes, [("test", result.session_id, True)])


if __name__ == "__main__":
    unittest.main()
