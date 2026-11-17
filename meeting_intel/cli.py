"""Command-line interface:  meeting-intel process standup.mp3

Runs the same pipeline as the API, without starting a server.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

from . import __version__
from .export import to_markdown
from .metrics import match_items, recall_at_k, wer
from .schemas import Meeting
from .services import Services, get_services
from .utils import fmt_time


def _services() -> Services:
    return get_services()


def cmd_process(args: argparse.Namespace, svc: Services) -> int:
    src = Path(args.file)
    if not src.is_file():
        print(f"error: {src} not found", file=sys.stderr)
        return 2
    meeting_id = svc.store.new_id()
    filename = f"audio{src.suffix.lower()}"
    shutil.copyfile(src, svc.store.dir(meeting_id) / filename)
    svc.store.save(Meeting(id=meeting_id, filename=filename))

    meeting = svc.pipeline.process(meeting_id)
    if meeting.status != "done":
        print(f"error: processing failed: {meeting.error}", file=sys.stderr)
        return 1
    markdown = to_markdown(meeting, include_transcript=not args.no_transcript)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
        print(f"meeting {meeting_id} processed -> {args.output}")
    else:
        print(markdown)
        print(f"(meeting id: {meeting_id})", file=sys.stderr)
    return 0


def cmd_list(_: argparse.Namespace, svc: Services) -> int:
    for m in svc.store.list():
        title = m.analysis.title if m.analysis else m.filename
        print(f"{m.id}  {m.status:<10} {fmt_time(m.duration):>8}  {m.created_at[:16]}  {title}")
    return 0


def cmd_show(args: argparse.Namespace, svc: Services) -> int:
    try:
        print(to_markdown(svc.store.load(args.id), include_transcript=not args.no_transcript))
    except FileNotFoundError:
        print(f"error: meeting {args.id} not found", file=sys.stderr)
        return 1
    return 0


def cmd_search(args: argparse.Namespace, svc: Services) -> int:
    for h in svc.index.search(args.query, meeting_id=args.meeting, limit=args.limit):
        print(f"[{h.score:.2f}] {h.meeting_id} {fmt_time(h.start)}-{fmt_time(h.end)} ({', '.join(h.speakers)})")
        print(f"       {h.summary or h.text[:200]}")
    return 0


def cmd_delete(args: argparse.Namespace, svc: Services) -> int:
    svc.index.delete_meeting(args.id)
    svc.store.delete(args.id)
    print(f"deleted {args.id}")
    return 0


def cmd_wer(args: argparse.Namespace, _: Services | None = None) -> int:
    ref = Path(args.reference).read_text(encoding="utf-8")
    hyp = Path(args.hypothesis).read_text(encoding="utf-8")
    print(f"WER: {wer(ref, hyp):.2%}")
    return 0


def cmd_eval_search(args: argparse.Namespace, svc: Services) -> int:
    """questions file: [{"query": "...", "relevant": [{"meeting_id": "...", "chunk_id": 3}, ...]}, ...]"""
    cases = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    ranked, relevant = [], []
    for c in cases:
        hits = svc.index.search(c["query"], limit=args.k)
        ranked.append([(h.meeting_id, h.chunk_id) for h in hits])
        relevant.append({(r["meeting_id"], r["chunk_id"]) for r in c["relevant"]})
    print(f"Recall@{args.k}: {recall_at_k(ranked, relevant, args.k):.2%} over {len(cases)} queries")
    return 0


def cmd_eval_items(args: argparse.Namespace, _: Services | None = None) -> int:
    """Compare predicted vs gold action items. Both files are JSON lists of strings."""
    pred = json.loads(Path(args.predicted).read_text(encoding="utf-8"))
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    r = match_items(pred, gold)
    print(f"precision {r.precision:.2%}  recall {r.recall:.2%}  F1 {r.f1:.2%}")
    return 0


OFFLINE = {cmd_wer, cmd_eval_items}  # commands that must not load any model or service


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="meeting-intel", description="AI Meeting Intelligence")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("-v", "--verbose", action="store_true", help="log pipeline progress")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("process", help="transcribe, analyse and index a recording")
    s.add_argument("file")
    s.add_argument("-o", "--output", help="write the Markdown report to this file")
    s.add_argument("--no-transcript", action="store_true", help="omit the full transcript from the report")
    s.set_defaults(func=cmd_process)

    s = sub.add_parser("list", help="list processed meetings")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="print a meeting as Markdown")
    s.add_argument("id")
    s.add_argument("--no-transcript", action="store_true")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("search", help="semantic search across meetings")
    s.add_argument("query")
    s.add_argument("-m", "--meeting", help="restrict to one meeting id")
    s.add_argument("-n", "--limit", type=int, default=5)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("delete", help="delete a meeting and its vectors")
    s.add_argument("id")
    s.set_defaults(func=cmd_delete)

    s = sub.add_parser("wer", help="word error rate between a reference and a hypothesis transcript")
    s.add_argument("reference")
    s.add_argument("hypothesis")
    s.set_defaults(func=cmd_wer)

    s = sub.add_parser("eval-search", help="Recall@k of semantic search on a hand-written question set")
    s.add_argument("questions")
    s.add_argument("-k", type=int, default=3)
    s.set_defaults(func=cmd_eval_search)

    s = sub.add_parser("eval-items", help="precision/recall of extracted action items vs a gold list")
    s.add_argument("predicted")
    s.add_argument("gold")
    s.set_defaults(func=cmd_eval_items)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    svc = None if args.func in OFFLINE else _services()
    return args.func(args, svc)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
