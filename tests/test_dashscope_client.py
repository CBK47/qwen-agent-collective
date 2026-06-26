from types import SimpleNamespace
import unittest

from shared.dashscope import DashScopeClient, DashScopeConfig, DashScopeError


class FakeChatCompletions:
    def __init__(self, failures=0):
        self.failures = failures
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("temporary outage")
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="ok"),
                    delta=SimpleNamespace(content="ok"),
                )
            ]
        )


class FakeEmbeddings:
    def create(self, **kwargs):
        values = kwargs["input"]
        if isinstance(values, str):
            data = [SimpleNamespace(embedding=[0.1, 0.2])]
        else:
            data = [SimpleNamespace(embedding=[float(i)]) for i, _ in enumerate(values)]
        return SimpleNamespace(data=data)


class FakeModels:
    def list(self, **kwargs):
        return SimpleNamespace(data=[SimpleNamespace(id="qwen-plus")])


class FakeOpenAI:
    def __init__(self, chat_failures=0):
        self.chat = SimpleNamespace(completions=FakeChatCompletions(chat_failures))
        self.embeddings = FakeEmbeddings()
        self.models = FakeModels()


class DashScopeClientTests(unittest.TestCase):
    def config(self, **overrides):
        values = dict(
            api_key="sk-test",
            max_retries=0,
            backoff_base_seconds=0,
            timeout_seconds=1,
        )
        values.update(overrides)
        return DashScopeConfig(**values)

    def test_missing_api_key_diagnostic_is_clear(self):
        client = DashScopeClient(config=self.config(api_key=None), openai_client=FakeOpenAI())
        report = client.diagnose(network=False)
        self.assertFalse(report["ok"])
        self.assertEqual(report["checks"][0]["name"], "api_key_present")

    def test_chat_retries_then_returns_content(self):
        fake = FakeOpenAI(chat_failures=1)
        client = DashScopeClient(
            config=self.config(max_retries=1),
            openai_client=fake,
        )
        self.assertEqual(client.chat("hello"), "ok")
        self.assertEqual(fake.chat.completions.calls, 2)

    def test_chat_raises_friendly_error_after_retries(self):
        client = DashScopeClient(
            config=self.config(max_retries=1),
            openai_client=FakeOpenAI(chat_failures=2),
        )
        with self.assertRaises(DashScopeError) as caught:
            client.chat("hello")
        self.assertIn("temporary outage", str(caught.exception))

    def test_embed_supports_single_and_batch_inputs(self):
        client = DashScopeClient(config=self.config(), openai_client=FakeOpenAI())
        self.assertEqual(client.embed("one"), [0.1, 0.2])
        self.assertEqual(client.embed(["one", "two"]), [[0.0], [1.0]])


if __name__ == "__main__":
    unittest.main()
