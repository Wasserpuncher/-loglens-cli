from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .core import analyze_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loglens",
        description="Kompakte Zusammenfassung von Logfiles (Level, Top-Fehler, Zeitfenster).",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Pfad(e) zu Logfiles. Wenn leer, wird von stdin gelesen.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Ausgabeformat (text oder json, Standard: text).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Anzahl der Top-Fehlermeldungen (Standard: 5).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="loglens 0.1.0",
    )
    return parser


def format_text(stats, top_n: int) -> str:
    lines = []
    lines.append("=== Loglens Zusammenfassung ===")
    lines.append(f"Gesamtzeilen: {stats.total_lines}")

    if stats.first_timestamp and stats.last_timestamp:
        lines.append(
            f"Zeitfenster: {stats.first_timestamp.isoformat()}  ->  {stats.last_timestamp.isoformat()}"
        )

    lines.append("")
    lines.append("Level-Zählung:")
    for level, count in sorted(stats.level_counts.items()):
        lines.append(f"  {level:8}: {count}")

    if stats.source_counts:
        lines.append("")
        lines.append("Quellen (source=...):")
        for src, count in sorted(stats.source_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {src:20}: {count}")

    lines.append("")
    lines.append(f"Top {top_n} Meldungen:")
    for msg, count in stats.top_messages[:top_n]:
        lines.append(f"  ({count}x) {msg}")

    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    stats = analyze_files(args.files)

    if args.format == "json":
        # Dataclasses in dict konvertieren, Timestamps in ISO-Strings
        data = asdict(stats)
        if stats.first_timestamp:
            data["first_timestamp"] = stats.first_timestamp.isoformat()
        if stats.last_timestamp:
            data["last_timestamp"] = stats.last_timestamp.isoformat()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(format_text(stats, args.top))


if __name__ == "__main__":
    main()
