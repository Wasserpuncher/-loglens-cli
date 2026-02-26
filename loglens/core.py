from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional, TextIO, Dict, List


@dataclass
class LogStats:
    total_lines: int
    level_counts: Dict[str, int]
    first_timestamp: Optional[datetime]
    last_timestamp: Optional[datetime]
    top_messages: List[tuple]
    source_counts: Dict[str, int]


LOGLEVEL_PATTERN = re.compile(r"\b(INFO|WARN|WARNING|ERROR|DEBUG|CRITICAL)\b")
TIMESTAMP_PATTERNS = [
    # 2025-02-26 12:34:56
    re.compile(r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"),
    # 2025-02-26T12:34:56
    re.compile(r"(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"),
]
SOURCE_PATTERN = re.compile(r"\b(?:service|app|src|module)=(?P<source>[A-Za-z0-9_\-\.]+)")


def parse_timestamp(line: str) -> Optional[datetime]:
    for pattern in TIMESTAMP_PATTERNS:
        match = pattern.search(line)
        if match:
            ts_str = match.group("ts")
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(ts_str, fmt)
                except ValueError:
                    continue
    return None


def detect_level(line: str) -> str:
    match = LOGLEVEL_PATTERN.search(line)
    if not match:
        return "UNKNOWN"
    level = match.group(1)
    if level == "WARNING":
        return "WARN"
    return level


def detect_source(line: str) -> Optional[str]:
    match = SOURCE_PATTERN.search(line)
    if match:
        return match.group("source")
    return None


def normalize_message(line: str) -> str:
    """
    Versucht, die eigentliche Meldung zu extrahieren:
    Entfernt Datum/Zeit, Level und bekannte Prefixes.
    """
    # Entferne Timestamp
    tmp = line
    for pattern in TIMESTAMP_PATTERNS:
        tmp = pattern.sub("", tmp)

    # Entferne Level
    tmp = LOGLEVEL_PATTERN.sub("", tmp)

    # Entferne source=…
    tmp = SOURCE_PATTERN.sub("", tmp)

    # Whitespace säubern
    tmp = re.sub(r"\s+", " ", tmp).strip()
    return tmp or "<empty>"


def analyze_stream(stream: Iterable[str]) -> LogStats:
    total_lines = 0
    level_counts: Counter = Counter()
    message_counter: Counter = Counter()
    source_counts: Counter = Counter()
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None

    for line in stream:
        line = line.rstrip("\n")
        if not line:
            continue

        total_lines += 1

        # Level
        level = detect_level(line)
        level_counts[level] += 1

        # Timestamp
        ts = parse_timestamp(line)
        if ts:
            if not first_ts or ts < first_ts:
                first_ts = ts
            if not last_ts or ts > last_ts:
                last_ts = ts

        # Source
        src = detect_source(line)
        if src:
            source_counts[src] += 1

        # Message
        msg = normalize_message(line)
        message_counter[msg] += 1

    top_messages = message_counter.most_common(5)

    return LogStats(
        total_lines=total_lines,
        level_counts=dict(level_counts),
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        top_messages=top_messages,
        source_counts=dict(source_counts),
    )


def analyze_files(paths: Optional[list[str]] = None) -> LogStats:
    if not paths:
        # stdin
        return analyze_stream(sys.stdin)

    combined_stats: Optional[LogStats] = None

    for path in paths:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            stats = analyze_stream(f)

        if combined_stats is None:
            combined_stats = stats
        else:
            combined_stats = merge_stats(combined_stats, stats)

    assert combined_stats is not None
    return combined_stats


def merge_stats(a: LogStats, b: LogStats) -> LogStats:
    level_counts = defaultdict(int, a.level_counts)
    for k, v in b.level_counts.items():
        level_counts[k] += v

    source_counts = defaultdict(int, a.source_counts)
    for k, v in b.source_counts.items():
        source_counts[k] += v

    message_counter = Counter(dict(a.top_messages))
    message_counter.update(dict(b.top_messages))
    top_messages = message_counter.most_common(5)

    first_ts = a.first_timestamp
    if b.first_timestamp and (not first_ts or b.first_timestamp < first_ts):
        first_ts = b.first_timestamp

    last_ts = a.last_timestamp
    if b.last_timestamp and (not last_ts or b.last_timestamp > last_ts):
        last_ts = b.last_timestamp

    return LogStats(
        total_lines=a.total_lines + b.total_lines,
        level_counts=dict(level_counts),
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        top_messages=top_messages,
        source_counts=dict(source_counts),
    )
