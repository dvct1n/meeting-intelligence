#!/usr/bin/env python3
"""Run the repository's metrics on hand-written synthetic fixtures.

This is an offline demonstration only. It does not invoke Whisper, pyannote,
any LLM provider, an embedding model, or Qdrant, and must not be presented as
measured model performance.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from meeting_intel.metrics import match_items, recall_at_k, wer  # noqa: E402

FIXTURES = ROOT / "examples" / "synthetic_evaluation"


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read valid JSON from {path}: {exc}") from exc


def evaluate() -> dict[str, Any]:
    reference = (FIXTURES / "asr_reference.txt").read_text(encoding="utf-8")
    hypothesis = (FIXTURES / "asr_hypothesis.txt").read_text(encoding="utf-8")
    asr_wer = wer(reference, hypothesis)

    predicted = read_json(FIXTURES / "action_items_predicted.json")
    gold = read_json(FIXTURES / "action_items_gold.json")
    if not isinstance(predicted, list) or not isinstance(gold, list):
        raise SystemExit("Action-item fixtures must both be JSON lists.")
    action_scores = match_items(predicted, gold)

    cases = read_json(FIXTURES / "retrieval_rankings.json")
    if not isinstance(cases, list) or not cases:
        raise SystemExit("Retrieval fixture must be a non-empty JSON list.")

    ranked: list[list[tuple[str, int]]] = []
    relevant: list[set[tuple[str, int]]] = []
    for index, case in enumerate(cases, start=1):
        try:
            ranked.append([
                (str(item["meeting_id"]), int(item["chunk_id"]))
                for item in case["ranked"]
            ])
            relevant.append({
                (str(item["meeting_id"]), int(item["chunk_id"]))
                for item in case["relevant"]
            })
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"Invalid retrieval fixture at case {index}: {exc}") from exc

    recall = {f"recall_at_{k}": recall_at_k(ranked, relevant, k=k) for k in (1, 3, 5)}
    return {
        "status": "SYNTHETIC DEMO ONLY — NOT MEASURED MODEL PERFORMANCE",
        "source": "hand-written fixtures in examples/synthetic_evaluation/",
        "sample_counts": {
            "transcript_pairs": 1,
            "action_item_sets": 1,
            "search_queries": len(cases),
        },
        "metrics": {
            "wer": asr_wer,
            "action_item_precision": action_scores.precision,
            "action_item_recall": action_scores.recall,
            "action_item_f1": action_scores.f1,
            **recall,
        },
        "not_measured": [
            "DER: requires real or carefully simulated speaker-turn annotations and a diarization hypothesis",
            "RTF: requires timing an actual audio-processing run on specified hardware",
            "end-to-end quality: requires running the actual ASR, diarization, LLM, embedding, and retrieval pipeline",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-json",
        type=Path,
        help="Optionally write the synthetic demonstration results to this path.",
    )
    args = parser.parse_args()

    result = evaluate()
    metrics = result["metrics"]
    print("SYNTHETIC EVALUATION DEMO — NOT REAL MODEL EVALUATION")
    print(f"Fixtures: {result['source']}")
    print("\nMetric demonstration")
    print(f"  WER (one toy transcript pair): {metrics['wer']:.2%}")
    print(
        "  Action-item P / R / F1 (one toy set): "
        f"{metrics['action_item_precision']:.2%} / "
        f"{metrics['action_item_recall']:.2%} / "
        f"{metrics['action_item_f1']:.2%}"
    )
    for k in (1, 3, 5):
        print(f"  Recall@{k} ({result['sample_counts']['search_queries']} toy queries): {metrics[f'recall_at_{k}']:.2%}")
    print("\nNot measured: DER, RTF, and end-to-end performance.")
    print("Do not report these synthetic values as results from Whisper, pyannote, an LLM, or Qdrant.")

    if args.write_json:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote synthetic demonstration JSON to: {args.write_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
