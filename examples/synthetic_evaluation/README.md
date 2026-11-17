# Synthetic evaluation fixtures

**All files in this directory are hand-written synthetic examples.** They do not contain real meeting recordings, real users' information, or outputs produced by Whisper, pyannote, an LLM, or Qdrant.

| File | Purpose |
|---|---|
| `asr_reference.txt` | Toy reference transcript for demonstrating WER |
| `asr_hypothesis.txt` | Hand-written toy hypothesis with a few deliberate differences |
| `action_items_gold.json` | Toy ground-truth action-item list |
| `action_items_predicted.json` | Toy predicted list, including one miss and one false positive |
| `retrieval_rankings.json` | Hand-crafted retrieval rankings used only to exercise Recall@k calculation |
| `results.demo.json` | Generated output from the script; synthetic demonstration only |

Run `python scripts/run_synthetic_evaluation.py` from the repository root. Add `--write-json examples/synthetic_evaluation/results.demo.json` to regenerate the checked-in output file. The script uses the project's metric functions but **does not run any ML model or query the vector database**. Its output is a demonstration of metric calculations, not a benchmark of system quality.
