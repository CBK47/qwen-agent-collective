"""Tests for the open-translate agent (agents/open-translate/translate.py).

Run with:
    python tests/test_open_translate.py

Uses importlib to load the module because the directory name contains a hyphen
and is therefore not a regular Python package.

The FakeClient injects canned responses without touching the network:
  - forward-pass prompts (containing "Translate the following") → canned translation
  - confidence prompts (containing "Rate the quality") → canned confidence score
  - back-translation prompts (containing "Back-translate") → canned back-translation
  - QA-judge prompts (containing "Compare these two texts") → canned PASS/FAIL

Three core assertions:
  1. A glossary term is enforced in the segment output even when the model
     "forgot" to include its required translation.
  2. A low-confidence / failed-QA segment is flagged for human review.
  3. The published output assembles all translated segments in order.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

# ---------------------------------------------------------------------------
# Module loader (hyphen in directory name prevents normal import)
# ---------------------------------------------------------------------------

_AGENT_FILE = pathlib.Path(__file__).resolve().parents[1] / "agents" / "open-translate" / "translate.py"

spec = importlib.util.spec_from_file_location("open_translate", _AGENT_FILE)
_mod = importlib.util.module_from_spec(spec)
# Register in sys.modules BEFORE exec so @dataclass can resolve the module.
sys.modules["open_translate"] = _mod
spec.loader.exec_module(_mod)

OpenTranslateAgent = _mod.OpenTranslateAgent
segment_document = _mod.segment_document
load_glossary = _mod.load_glossary
enforce_glossary = _mod.enforce_glossary
CONFIDENCE_THRESHOLD = _mod.CONFIDENCE_THRESHOLD


# ---------------------------------------------------------------------------
# Fake client
# ---------------------------------------------------------------------------

class FakeClient:
    """Minimal DashScopeClient replacement.

    Dispatches by detecting key phrases in the prompt:
      - "Translate the following" → canned forward translation
      - "Rate the quality"        → canned confidence score
      - "Back-translate"          → canned back-translation
      - "Compare these two texts" → canned QA verdict
    """

    def __init__(
        self,
        *,
        forward_reply: str = "Le logiciel open source est un agent de traduction.",
        confidence_reply: str = "0.85",
        back_translation_reply: str = "The open source software is a translation agent.",
        qa_verdict: str = "PASS",
        # Set to a low score / FAIL to trigger the HITL flag.
        low_confidence_segment_index: int | None = None,
        low_confidence_reply: str = "0.40",
        fail_qa_segment_index: int | None = None,
    ):
        self.forward_reply = forward_reply
        self.confidence_reply = confidence_reply
        self.back_translation_reply = back_translation_reply
        self.qa_verdict = qa_verdict
        self.low_confidence_segment_index = low_confidence_segment_index
        self.low_confidence_reply = low_confidence_reply
        self.fail_qa_segment_index = fail_qa_segment_index

        self._call_counter: dict[str, int] = {}  # phase → call count

        # Expose a minimal config so the agent can call client.config.chat_model.
        class _Config:
            chat_model = "qwen-plus"

        self.config = _Config()

    def chat(self, prompt: str, **kwargs) -> str:
        prompt_lower = prompt.lower()

        # Check "back-translate" BEFORE "translate the following" because
        # "Back-translate the following..." contains "translate the following"
        # as a substring — wrong phase would be assigned otherwise.
        if "back-translate" in prompt_lower:
            phase = "back_translate"
        elif "translate the following" in prompt_lower:
            phase = "translate"
        elif "rate the quality" in prompt_lower:
            phase = "confidence"
        elif "compare these two texts" in prompt_lower:
            phase = "qa_judge"
        else:
            return ""

        # Increment counter per phase to identify which segment we're on.
        self._call_counter[phase] = self._call_counter.get(phase, 0) + 1
        seg_idx = self._call_counter[phase] - 1  # 0-based

        if phase == "translate":
            return self.forward_reply

        if phase == "confidence":
            if self.low_confidence_segment_index is not None and seg_idx == self.low_confidence_segment_index:
                return self.low_confidence_reply
            return self.confidence_reply

        if phase == "back_translate":
            return self.back_translation_reply

        if phase == "qa_judge":
            if self.fail_qa_segment_index is not None and seg_idx == self.fail_qa_segment_index:
                return "FAIL"
            return self.qa_verdict

        return ""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGlossaryEnforcement(unittest.TestCase):
    """Assertion 1: glossary terms must appear in the output even if the model
    returns a translation that omits the required term."""

    def test_glossary_term_enforced_when_model_forgets(self):
        # The glossary requires "agent" → "agente" in Spanish.
        # The FakeClient returns a translation that deliberately omits "agente".
        fake = FakeClient(
            forward_reply="El software de fuente abierta es un asistente de traducción.",
            # ^ note: uses "asistente" not "agente" — simulating a glossary miss
            confidence_reply="0.88",
            back_translation_reply="The open source software is a translation assistant.",
            qa_verdict="PASS",
        )
        glossary = {"agent": "agente", "open source": "código abierto"}
        agent = OpenTranslateAgent(client=fake, source_language="English")
        source_text = "The open source agent does great work."
        segments, output = agent.translate_document(source_text, "Spanish", glossary=glossary)

        self.assertEqual(len(segments), 1)
        seg = segments[0]

        # "agente" must appear in the output (glossary enforcement).
        self.assertIn(
            "agente",
            seg.translation.lower(),
            msg=f"Glossary term 'agent' → 'agente' was not enforced in: {seg.translation!r}",
        )
        # At least one term should have been enforced.
        self.assertTrue(
            len(seg.glossary_terms_enforced) >= 1,
            msg=f"Expected at least 1 enforced term, got {seg.glossary_terms_enforced}",
        )
        # The output also assembles correctly.
        self.assertIn("agente", output.lower())


class TestHITLFlagging(unittest.TestCase):
    """Assertion 2: low-confidence or failed-QA segments are flagged for review."""

    def test_low_confidence_segment_is_flagged(self):
        # Two-paragraph doc; segment 0 gets low confidence.
        fake = FakeClient(
            forward_reply="Bonjour le monde.",
            confidence_reply="0.90",
            back_translation_reply="Hello the world.",
            qa_verdict="PASS",
            low_confidence_segment_index=0,  # first segment → low conf
            low_confidence_reply="0.40",
        )
        source_text = "Hello world.\n\nThis is a test sentence."
        agent = OpenTranslateAgent(client=fake, source_language="English")
        segments, output = agent.translate_document(source_text, "French", glossary={})

        flagged = [s for s in segments if s.flagged]
        self.assertTrue(
            len(flagged) >= 1,
            msg="Expected at least one segment flagged for review due to low confidence.",
        )
        # The flagged segment must have confidence below threshold.
        self.assertLess(
            flagged[0].confidence,
            CONFIDENCE_THRESHOLD,
            msg=f"Flagged segment confidence {flagged[0].confidence} should be < {CONFIDENCE_THRESHOLD}",
        )
        # The published output should contain a [REVIEW: ...] marker.
        self.assertIn("[REVIEW:", output, msg="Expected [REVIEW:] marker in published output for flagged segment.")

    def test_failed_qa_segment_is_flagged(self):
        # Single segment; QA returns FAIL.
        fake = FakeClient(
            forward_reply="Une traduction quelconque.",
            confidence_reply="0.88",   # confidence is fine…
            back_translation_reply="Something completely different.",
            qa_verdict="FAIL",         # …but QA fails
        )
        source_text = "Specific technical content that is hard to round-trip."
        agent = OpenTranslateAgent(client=fake, source_language="English")
        segments, output = agent.translate_document(source_text, "French", glossary={})

        self.assertEqual(len(segments), 1)
        self.assertFalse(segments[0].qa_pass, msg="Expected QA to be marked as failed.")
        self.assertTrue(segments[0].flagged, msg="Expected segment to be flagged when QA fails.")
        self.assertIn("[REVIEW:", output)


class TestPublishedOutput(unittest.TestCase):
    """Assertion 3: published output assembles all translated segments."""

    def test_all_segments_assembled_in_output(self):
        # Three-paragraph doc — each gets its own translation.
        translations = [
            "Premier paragraphe traduit.",
            "Deuxième paragraphe traduit.",
            "Troisième paragraphe traduit.",
        ]
        # Only count forward-translate calls so the index stays correct
        # regardless of how many confidence / back-translate / judge calls
        # the pipeline makes per segment.
        translate_call_counter = {"n": 0}

        class SequentialFake:
            """Returns different translations for each forward call."""

            class config:
                chat_model = "qwen-plus"

            def chat(self, prompt: str, **kwargs) -> str:
                p = prompt.lower()
                # Check back-translate BEFORE translate-the-following because
                # "Back-translate the following..." contains "translate the following"
                # as a substring.
                if "back-translate" in p:
                    return "Back translated text."
                if "translate the following" in p:
                    idx = translate_call_counter["n"] % len(translations)
                    translate_call_counter["n"] += 1
                    return translations[idx]
                if "rate the quality" in p:
                    return "0.90"
                if "compare these two texts" in p:
                    return "PASS"
                return ""

        source_text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        agent = OpenTranslateAgent(client=SequentialFake(), source_language="English")
        segments, output = agent.translate_document(source_text, "French", glossary={})

        self.assertEqual(len(segments), 3, msg=f"Expected 3 segments, got {len(segments)}")

        # Each canned translation must appear in the output.
        for t in translations:
            self.assertIn(t, output, msg=f"Translation {t!r} missing from assembled output.")

        # Segments appear in order.
        positions = [output.index(t) for t in translations]
        self.assertEqual(positions, sorted(positions), msg="Segments are not in order in the published output.")


class TestSegmentDocument(unittest.TestCase):
    """Unit tests for the segmentation helper."""

    def test_single_paragraph(self):
        segs = segment_document("Hello world.")
        self.assertEqual(segs, ["Hello world."])

    def test_two_paragraphs(self):
        segs = segment_document("Para one.\n\nPara two.")
        self.assertEqual(segs, ["Para one.", "Para two."])

    def test_blank_lines_ignored(self):
        segs = segment_document("\n\n\nHello.\n\n\nWorld.\n\n")
        self.assertEqual(segs, ["Hello.", "World."])


class TestEnforceGlossary(unittest.TestCase):
    """Unit tests for the post-process enforcement helper."""

    def test_no_enforcement_needed(self):
        result, enforced = enforce_glossary("glossaire complet", "glossary", {"glossary": "glossaire"})
        self.assertIn("glossaire", result)
        self.assertEqual(enforced, [])

    def test_term_replaced_when_forgotten(self):
        # Translation still has the English word "glossary" untranslated.
        result, enforced = enforce_glossary("a nice glossary", "glossary check", {"glossary": "glossaire"})
        self.assertIn("glossaire", result.lower())
        self.assertIn("glossary", enforced)

    def test_term_appended_when_no_source_word_in_translation(self):
        # Translation has neither "glossary" nor "glossaire" — bracket appended.
        result, enforced = enforce_glossary("une belle chose", "glossary check", {"glossary": "glossaire"})
        self.assertIn("glossaire", result.lower())
        self.assertIn("glossary", enforced)


class TestLoadGlossary(unittest.TestCase):
    """Smoke test: glossary.json loads without error for known languages."""

    def test_french_glossary_loads(self):
        g = load_glossary("French")
        self.assertIsInstance(g, dict)
        self.assertIn("glossary", g, msg="Expected 'glossary' term in French glossary")
        self.assertEqual(g["glossary"], "glossaire")

    def test_unknown_language_returns_empty(self):
        g = load_glossary("Klingon")
        self.assertEqual(g, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
