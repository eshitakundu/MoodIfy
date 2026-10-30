"""Score mood readers on the labelled cases.

    python evals/run_eval.py                      # offline lexicon reader
    OPENROUTER_API_KEY=... python evals/run_eval.py --llm   # also score the LLM reader

Exits non-zero if the lexicon reader drops below --min-accuracy, so CI catches
regressions in the offline fallback.
"""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from moodify.reader import LexiconReader, LLMReader  # noqa: E402

CASES = Path(__file__).with_name("mood_cases.jsonl")
INDIRECT = Path(__file__).with_name("mood_cases_indirect.jsonl")


def score(reader, cases):
    hits, misses, sources = 0, [], Counter()
    for case in cases:
        reading = reader.read(case["text"])
        if inspect.isawaitable(reading):
            reading = asyncio.run(reading)
        sources[reading.source] += 1
        if reading.mood == case["mood"]:
            hits += 1
        else:
            misses.append((case["text"], case["mood"], reading.mood))
    return hits, misses, sources


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true")
    parser.add_argument("--min-accuracy", type=float, default=0.85)
    args = parser.parse_args()
    readers = [("lexicon", LexiconReader())] + ([("llm", LLMReader())] if args.llm else [])
    lexicon_accuracy = 0.0
    for case_file, label in [(CASES, "direct"), (INDIRECT, "indirect")]:
        cases = [json.loads(line) for line in case_file.read_text(encoding="utf-8").splitlines() if line]
        print(f"\n{label} phrasing ({len(cases)} cases, {case_file.name})")
        for name, reader in readers:
            hits, misses, sources = score(reader, cases)
            accuracy = hits / len(cases)
            if (name, label) == ("lexicon", "direct"):
                lexicon_accuracy = accuracy
            print(f"  {name}: {hits}/{len(cases)} = {accuracy:.0%}  answered by {dict(sources)}")
            for text, expected, got in misses:
                print(f"    miss: {text!r} expected {expected}, got {got}")
    # Only the direct set gates CI: the indirect set exists to show where keywords fail.
    return 0 if lexicon_accuracy >= args.min_accuracy else 1


if __name__ == "__main__":
    raise SystemExit(main())
