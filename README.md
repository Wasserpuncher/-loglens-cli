# loglens-cli

A compact Python CLI tool for **logfile analysis**. It detects log levels, aggregates the time window, counts sources, and shows the most frequent messages – perfect for quick log overviews directly in the terminal.

## Features

- Reads one or multiple log files – or directly from `stdin`.
- Detects log levels (INFO, WARN, ERROR, DEBUG, CRITICAL, UNKNOWN).
- Parses generic timestamps (`YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DDTHH:MM:SS`).
- Aggregates a global time window (first/last event).
- Counts optional sources such as `service=orders`, `app=api`, `module=auth`.
- Shows the top N most frequent messages (normalized message text).
- Output as human-readable text or machine-friendly JSON (`--format json`).
- Installable as a global CLI tool via the `loglens` command.

## Installation

Requirement: Python 3.9+

```bash
git clone https://github.com/<your-user>/loglens-cli.git
cd loglens-cli
pip install .
