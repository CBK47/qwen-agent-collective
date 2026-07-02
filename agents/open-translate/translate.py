"""open-translate — end-to-end localization workflow CLI.

Usage:
    python agents/open-translate/translate.py --in doc.md --target French
    python agents/open-translate/translate.py --in doc.md --target Spanish --out out.md
    python agents/open-translate/translate.py --in doc.md --target German --interactive

Workflow:
    1. Ingest document (md/txt) and segment by paragraph.
    2. Load glossary from brain shared.glossary via retrieve.
    3. Pre-translate: locate glossary terms in each segment.
    4. Translate each segment via DashScopeClient.chat (qwen-plus).
    5. Post-translate: enforce glossary terms (replace any misses).
    6. QA gate: back-translate each segment; compare with original via
       normalized overlap; mark pass / needs-review.
    7. HITL checkpoint: collect low-confidence / failed-QA segments;
       in batch mode just print them; in --interactive mode prompt user.
    8. Publish: assemble and write output.
    9. Print summary.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any

# Ensure repo root is importable when running the script directly.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from shared.brain import BrainClient
from shared.dashscope import DashScopeClient  # noqa: E402

CONFIDENCE_THRESHOLD = 0.75


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Segment:
    index: int
    source: str
    translation: str = ""
    confidence: float = 0.0
    qa_pass: bool = True
    flagged: bool = False
    glossary_terms_enforced: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Glossary / Translation Memory
# ---------------------------------------------------------------------------


def load_glossary(target_language: str) -> dict[str, str]:
    brain_client = BrainClient()
    glossary_data = brain_client.retrieve('shared.glossary')
    for lang, pairs in glossary_data.items():
        if lang.lower() == target_language.lower():
            return {k.lower(): v for k, v in pairs.items()}
    return {}


def find_glossary_terms(text: str, glossary: dict[str, str]) -> list[str]:
    """Return glossary source-terms found (case-insensitive) in *text*."""
    found = []
    lower = text.lower()
    for term in glossary:
        if term in lower:
            found.append(term)
    return found


def enforce_glossary(translation: str, segment_source: str, glossary: dict[str, str]) -> tuple[str, list[str]]:
    """Ensure that every glossary term present in the source appears correctly
    in the translation.  Returns (corrected_translation, [enforced_terms]).
    """
    enforced: list[str] = []
    lower_source = segment_source.lower()
    result = translation
    for term, required_translation in glossary.items():
        if term not in lower_source:
            continue
        # Check if the required translation is already present (case-insensitive).
        if required_translation.lower() not in result.lower():
            # Simple post-process: append the required term in brackets if the
            # model forgot it, then replace via a regex on the first plausible
            # occurrence.  Because we have no positional information from the
            # model output we do a best-effort inline swap: find the model's
            # rendering of the source term (transliterated or untranslated) and
            # replace it; if nothing found, append a correction note.
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(result):
                # Function replacement → required_translation is treated literally
                # (a plain string repl would interpret \1, \g<>, and backslashes).
                result = pattern.sub(lambda _m: required_translation, result, count=1)
            else:
                result = f"{result} [{required_translation}]"
            enforced.append(term)
    return result, enforced


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------


def segment_document(text: str) -> list[str]:
    """Split document into translatable segments (paragraph-level).

    Empty lines act as paragraph boundaries.  Each non-empty paragraph is one
    segment.  Very long paragraphs are left intact for MVP simplicity.
    """
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


# ---------------------------------------------------------------------------
# Translation + confidence
# ---------------------------------------------------------------------------


def _build_translate_prompt(segment: str, target_language: str, glossary: dict[str, str]) -> str:
    glossary_block = ""
    terms_in_segment = find_glossary_terms(segment, glossary)
    if terms_in_segment:
        pairs = "\n".join(f"  {t} → {glossary[t]}" for t in terms_in_segment)
        glossary_block = f"\nRequired glossary terms (use exactly as given):\n{pairs}\n"

    return (
        f"Translate the following text to {target_language}. "
        f"Return ONLY the translated text — no commentary, no labels, no extra lines.{glossary_block}\n\n"
        f"Source text:\n{segment}"
    )


def _build_confidence_prompt(source: str, translation: str, target_language: str) -> str:
    return (
        f"Rate the quality of this {target_language} translation on a scale from 0.0 to 1.0.\n"
        f"Return ONLY a decimal number between 0.0 and 1.0 — nothing else.\n\n"
        f"Original: {source}\n"
        f"Translation: {translation}"
    )


def _build_back_translate_prompt(translation: str, source_language: str, target_language: str) -> str:
    return (
        f"Back-translate the following {target_language} text to {source_language}. "
        f"Return ONLY the back-translated text — no commentary.\n\n"
        f"{translation}"
    )


def _build_qa_judge_prompt(original: str, back_translation: str) -> str:
    return (
        "Compare these two texts and decide if they convey the same meaning.\n"
        "Reply with ONLY 'PASS' or 'FAIL' — no other text.\n\n"
        f"Text A: {original}\n"
        f"Text B: {back_translation}"
    )


def _parse_confidence(raw: str) -> float:
    """Extract a float in [0,1] from model output; default 0.5 on parse failure."""
    match = re.search(r"([01]?\.\d+|\d+\.?\d*)", raw.strip())
    if match:
        try:
            val = float(match.group(1))
            return max(0.0, min(1.0, val))
        except ValueError:
            pass
    return 0.5


# ---------------------------------------------------------------------------
# Similarity (QA fallback when model judge is unavailable)
# ---------------------------------------------------------------------------


def _normalized_overlap(a: str, b: str) -> float:
    """Token overlap between two strings normalized by max length."""
    tokens_a = set(re.findall(r"\w+", a.lower()))
    tokens_b = set(re.findall(r"\w+", b.lower()))
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))


# ---------------------------------------------------------------------------
# Core translator
# ---------------------------------------------------------------------------


class OpenTranslateAgent:
    """Localization workflow agent.

    Args:
        client: a DashScopeClient (or compatible fake).  If None, one is
            constructed from the environment — requires DASHSCOPE_API_KEY.
        source_language: label for the source language (default "English").
        qa_overlap_threshold: minimum normalized-overlap score for QA pass
            when the LLM judge is used as a fallback (default 0.4).
    """

    def __init__(
        self,
        client: DashScopeClient | None = None,
        source_language: str = "English",
        qa_overlap_threshold: float = 0.4,
    ) -> None:
        self.client: DashScopeClient = client or DashScopeClient()
        self.source_language = source_language
        self.qa_overlap_threshold = qa_overlap_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def translate_document(
        self,
        text: str,
        target_language: str,
        glossary: dict[str, str] | None = None,
        *,
        interactive: bool = False,
    ) -> tuple[list[Segment], str]:
        """Translate the input text to the target language.

        Args:
            text: The source text to be translated.
            target_language: The language to translate into (e.g., "French", "Spanish").
            glossary: Optional dictionary of glossary terms (source term → translated term) for enforcement. If None, no glossary is used.
            interactive: If True, pause for human review of flagged segments during the HITL checkpoint.

        Returns:
            A tuple containing:
                - segments: List of Segment objects with translation results and metadata.
                - published_output: The final translated document as a string, assembled from segments.
        """
        if glossary is None:
            glossary = {}

        raw_segments = segment_document(text)
        segments: list[Segment] = []

        for idx, src in enumerate(raw_segments):
            seg = self._translate_segment(idx, src, target_language, glossary)
            seg = self._qa_segment(seg, target_language)
            seg.flagged = (seg.confidence < CONFIDENCE_THRESHOLD) or (not seg.qa_pass)
            segments.append(seg)

        if interactive:
            segments = self._hitl_checkpoint(segments)

        output = self._publish(segments)
        return segments, output

    # ------------------------------------------------------------------
    # Internal pipeline steps
    # ------------------------------------------------------------------

    def _translate_segment(
        self,
        idx: int,
        source: str,
        target_language: str,
        glossary: dict[str, str],
    ) -> Segment:
        seg = Segment(index=idx, source=source)

        # Step 3a: translate.
        translate_prompt = _build_translate_prompt(source, target_language, glossary)
        raw_translation = self.client.chat(translate_prompt, model=self.client.config.chat_model)

        # Step 3b: enforce glossary post-hoc.
        enforced_translation, enforced_terms = enforce_glossary(raw_translation, source, glossary)
        seg.translation = enforced_translation
        seg.glossary_terms_enforced = enforced_terms

        # Step 3c: ask model to self-rate confidence.
        conf_prompt = _build_confidence_prompt(source, enforced_translation, target_language)
        conf_raw = self.client.chat(conf_prompt, model=self.client.config.chat_model)
        seg.confidence = _parse_confidence(conf_raw)

        return seg

    def _qa_segment(self, seg: Segment, target_language: str) -> Segment:
        """Back-translate and LLM-judge; fall back to overlap if judge ambiguous."""
        bt_prompt = _build_back_translate_prompt(seg.translation, self.source_language, target_language)
        back_translation = self.client.chat(bt_prompt, model=self.client.config.chat_model)

        judge_prompt = _build_qa_judge_prompt(seg.source, back_translation)
        verdict = self.client.chat(judge_prompt, model=self.client.config.chat_model).strip().upper()

        if verdict.startswith("PASS"):
            seg.qa_pass = True
        elif verdict.startswith("FAIL"):
            seg.qa_pass = False
        else:
            # Ambiguous LLM reply — fall back to overlap heuristic.
            overlap = _normalized_overlap(seg.source, back_translation)
            seg.qa_pass = overlap >= self.qa_overlap_threshold

        return seg

    def _hitl_checkpoint(self, segments: list[Segment]) -> list[Segment]:
        """Interactive HITL: prompt user for each flagged segment.

        Only called when --interactive is set.  In batch mode, flagged segments
        are simply collected and printed in the summary.
        """
        for seg in segments:
            if not seg.flagged:
                continue
            reason = []
            if seg.confidence < CONFIDENCE_THRESHOLD:
                reason.append(f"conf={seg.confidence:.2f}")
            if not seg.qa_pass:
                reason.append("QA-FAIL")
            print(f"\n[REVIEW {','.join(reason)}]")
            print(f"  Source:   {seg.source}")
            print(f"  Proposed: {seg.translation}")
            answer = input("  Accept? [y/edit/skip] ").strip().lower()
            if answer == "y":
                seg.flagged = False  # approved — unflag
            elif answer == "edit":
                seg.translation = input("  Enter revised translation: ").strip()
                seg.flagged = False
            # skip → leave flagged
        return segments

    def _publish(self, segments: list[Segment]) -> str:
        """Assemble translated segments into the output document."""
        parts: list[str] = []
        for seg in segments:
            text = seg.translation
            if seg.flagged:
                reason = []
                if seg.confidence < CONFIDENCE_THRESHOLD:
                    reason.append(f"conf={seg.confidence:.2f}")
                if not seg.qa_pass:
                    reason.append("QA-FAIL")
                text = f"[REVIEW: {','.join(reason)}] {text}"
            parts.append(text)
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------


def print_summary(segments: list[Segment]) -> None:
    flagged = [s for s in segments if s.flagged]
    all_enforced = [t for s in segments for t in s.glossary_terms_enforced]
    total_enforced = len(set(all_enforced))

    print("\n--- open-translate summary ---")
    print(f"  Segments translated : {len(segments)}")
    print(f"  Glossary terms enforced : {total_enforced} unique term(s) across segments")
    print(f"  Flagged for review  : {len(flagged)}")

    if flagged:
        print("\nSegments flagged for human review:")
        for seg in flagged:
            reason = []
            if seg.confidence < CONFIDENCE_THRESHOLD:
                reason.append(f"conf={seg.confidence:.2f}")
            if not seg.qa_pass:
                reason.append("QA-FAIL")
            print(f"  [{seg.index}] ({','.join(reason)}) {seg.source[:60]!r}")

    # TODO: after human approval, ingest confirmed pairs into open-translate.private
    #       and propose new glossary terms to shared.glossary via memory_review_queue.
    print("------------------------------\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="open-translate: translate a document with glossary enforcement and QA gate"
    )
    parser.add_argument("--in", dest="input_path", required=True, help="Path to source document (.md or .txt)")
    parser.add_argument("--target", default="French", help="Target language (default: French)")
    parser.add_argument("--out", dest="output_path", default=None, help="Output path (default: stdout)")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Pause at HITL checkpoint to let user review flagged segments",
    )
    parser.add_argument(
        "--source-lang",
        default="English",
        help="Source language label (default: English)",
    )
    args = parser.parse_args(argv)

    # Load input.
    input_path = pathlib.Path(args.input_path)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1
    text = input_path.read_text(encoding="utf-8")

    # Load glossary.
    glossary = load_glossary(args.target)

    # Translate.
    agent = OpenTranslateAgent(source_language=args.source_lang)
    segments, output = agent.translate_document(
        text,
        args.target,
        glossary=glossary,
        interactive=args.interactive,
    )

    # Write output.
    if args.output_path:
        out_path = pathlib.Path(args.output_path)
        out_path.write_text(output, encoding="utf-8")
        print(f"Output written to {out_path}")
    else:
        print(output)

    print_summary(segments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
