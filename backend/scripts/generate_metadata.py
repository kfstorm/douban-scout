#!/usr/bin/env python3
"""Script to generate metadata constants from Douban backup database."""

import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def tokenize_metadata(s: str) -> list[str]:
    """Split metadata string into individual tokens."""
    if not s:
        return []
    # Split by major delimiters
    segments = re.split(r"[/|\\,，、]", s)
    cleaned = []
    for segment in segments:
        stripped_segment = segment.strip()
        if not stripped_segment:
            continue

        # If segment contains Chinese characters, split by space to catch "美国 法国"
        # otherwise keep as is
        if re.search(r"[\u4e00-\u9fff]", stripped_segment):
            parts = re.split(r"\s+", stripped_segment)
            for part in parts:
                stripped_part = part.strip()
                if stripped_part:
                    cleaned.append(stripped_part)
        else:
            cleaned.append(stripped_segment)
    return cleaned


def is_chinese_or_punct(s: str) -> bool:
    """Check if string contains only Chinese characters or punctuation (no English letters)."""
    # Reject if contains any English letters
    if re.search(r"[a-zA-Z]", s):
        return False
    # Must contain at least one Chinese character
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def _extract_structured_data(
    detail: dict[str, Any],
    structured_genres_counter: Counter[str],
    structured_regions_counter: Counter[str],
) -> None:
    """Extract genres and regions from structured fields."""
    # 1. Structured Genres
    raw_genres = detail.get("genres", []) + detail.get("types", [])
    for g in raw_genres:
        if isinstance(g, str):
            for t in tokenize_metadata(g):
                if is_chinese_or_punct(t):
                    structured_genres_counter[t] += 1

    # 2. Structured Regions
    raw_regions = detail.get("countries", []) + detail.get("regions", [])
    for r in raw_regions:
        if isinstance(r, str):
            for t in tokenize_metadata(r):
                if t.isdigit() or re.match(r"^[^\w\s]+$", t):
                    continue
                if not is_chinese_or_punct(t):
                    continue
                structured_regions_counter[t] += 1


def _analyze_subtitles(
    detail: dict[str, Any],
    known_genres: set[str],
    structured_regions_counter: Counter[str],
    unstructured_regions_counter: Counter[str],
) -> None:
    """Analyze subtitles to discover additional regions."""
    subtitles = [detail.get("card_subtitle"), detail.get("subtitle")]
    for subtitle in subtitles:
        if not isinstance(subtitle, str):
            continue

        parts = [p.strip() for p in subtitle.split("/")]
        if not parts:
            continue

        region_parts = _identify_region_parts(parts, known_genres)

        for p in region_parts:
            for t in tokenize_metadata(p):
                if not is_chinese_or_punct(t):
                    continue

                if t in structured_regions_counter:
                    structured_regions_counter[t] += 1
                else:
                    unstructured_regions_counter[t] += 1


def _identify_region_parts(parts: list[str], known_genres: set[str]) -> list[str]:
    """Identify which parts of a subtitle string likely contain regions."""
    start_idx = 1 if re.match(r"^\d{4}$", parts[0]) else 0

    genre_idx = -1
    for i in range(start_idx, len(parts)):
        tokens = tokenize_metadata(parts[i])
        if any(t in known_genres for t in tokens):
            genre_idx = i
            break

    if genre_idx != -1:
        return parts[start_idx:genre_idx]

    if len(parts) > start_idx:
        p = parts[start_idx]
        max_region_len = 30
        if len(p) < max_region_len:
            return [p]

    return []


def generate_metadata(source_db_path: str, output_path: str) -> None:
    """Analyze database and generate metadata_constants.py."""
    if not Path(source_db_path).exists():
        print(f"Error: Source database not found at {source_db_path}")
        sys.exit(1)

    structured_genres_counter: Counter[str] = Counter()
    structured_regions_counter: Counter[str] = Counter()
    unstructured_regions_counter: Counter[str] = Counter()

    conn = sqlite3.connect(source_db_path)
    cursor = conn.cursor()
    print(f"Analyzing source database: {source_db_path}...")

    cursor.execute("SELECT raw_data FROM item WHERE type IN ('movie', 'tv')")
    raw_rows = cursor.fetchall()

    # Pass 1: Structured data
    for (raw_data,) in raw_rows:
        if not raw_data:
            continue
        try:
            data = json.loads(raw_data)
            detail = data.get("detail")
            if isinstance(detail, dict):
                _extract_structured_data(
                    detail, structured_genres_counter, structured_regions_counter
                )
        except Exception:
            continue

    known_genres = set(structured_genres_counter.keys())

    # Pass 2: Subtitles
    for (raw_data,) in raw_rows:
        if not raw_data:
            continue
        try:
            data = json.loads(raw_data)
            detail = data.get("detail")
            if isinstance(detail, dict):
                _analyze_subtitles(
                    detail, known_genres, structured_regions_counter, unstructured_regions_counter
                )
        except Exception:
            continue

    conn.close()
    _write_constants(
        output_path,
        source_db_path,
        structured_genres_counter,
        structured_regions_counter,
        unstructured_regions_counter,
    )


def _write_constants(
    output_path: str,
    source_db_path: str,
    genres_counter: Counter[str],
    regions_counter: Counter[str],
    unstructured_regions_counter: Counter[str],
) -> None:
    """Write the generated constants to a Python file."""
    final_genres = sorted([g for g, count in genres_counter.items() if count >= 1])

    min_discovery_count = 5
    discovered_regions = [
        r for r, count in unstructured_regions_counter.items() if count >= min_discovery_count
    ]
    total_regions_counter = regions_counter.copy()
    for r in discovered_regions:
        total_regions_counter[r] += unstructured_regions_counter[r]

    final_regions = sorted([r for r, count in total_regions_counter.items() if count >= 1])

    with Path(output_path).open("w", encoding="utf-8") as f:
        f.write("# Generated file. Do not edit manually.\n")
        f.write("# Generated by: backend/scripts/generate_metadata.py\n")
        f.write("# Generated from: " + Path(source_db_path).name + "\n\n")

        f.write("VALID_GENRES = [\n")
        for g in final_genres:
            f.write(f'    "{g}",\n')
        f.write("]\n\n")

        f.write("VALID_REGIONS = [\n")
        for r in final_regions:
            f.write(f'    "{r}",\n')
        f.write("]\n")

    print(f"Successfully generated metadata constants at {output_path}")
    print(f"Extracted {len(final_genres)} genres and {len(final_regions)} regions.")


if __name__ == "__main__":
    min_args = 2
    if len(sys.argv) < min_args:
        print("Usage: python3 backend/scripts/generate_metadata.py <path_to_source_db>")
        sys.exit(1)

    source_db = sys.argv[1]
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    output_file = project_root / "backend/app/metadata_constants.py"

    generate_metadata(source_db, str(output_file))
