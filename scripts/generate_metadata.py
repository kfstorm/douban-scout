#!/usr/bin/env python3
import json
import sqlite3
import os
import re
import sys
from collections import Counter
from typing import Set, List, Tuple


def tokenize_metadata(s: str) -> List[str]:
    if not s:
        return []
    # Split by major delimiters
    segments = re.split(r"[/|\\,，、]", s)
    cleaned = []
    for t in segments:
        # Aggressively strip leading/trailing noise including punctuation
        # Using a loop to handle multiple nested or sequential characters
        # Note: We use a set of characters to strip from both ends
        strip_chars = "()（）[]【】:;\"' "
        while True:
            new_t = t.strip(strip_chars)
            if new_t == t:
                break
            t = new_t

        if t:
            # Handle mixed language like "Canada 加拿大"
            # Split into sequences of Chinese characters vs non-Chinese characters
            parts = re.findall(r"[\u4e00-\u9fff]+|[^\u4e00-\u9fff]+", t)
            for p in parts:
                p = p.strip(strip_chars)
                if p:
                    cleaned.append(p)
    return cleaned


def generate_metadata(source_db_path: str, output_path: str):
    if not os.path.exists(source_db_path):
        print(f"Error: Source database not found at {source_db_path}")
        sys.exit(1)

    # Separate counters for better control
    structured_genres_counter = Counter()
    structured_regions_counter = Counter()
    unstructured_regions_counter = Counter()

    conn = sqlite3.connect(source_db_path)
    cursor = conn.cursor()

    print(f"Analyzing source database: {source_db_path}...")

    # Pass 1: Collect structured data
    cursor.execute("SELECT raw_data FROM item WHERE type IN ('movie', 'tv')")
    raw_rows = cursor.fetchall()

    for (raw_data,) in raw_rows:
        if not raw_data:
            continue
        try:
            data = json.loads(raw_data)
            detail = data.get("detail", {})
            if not isinstance(detail, dict):
                continue

            # 1. Structured Genres
            raw_genres = detail.get("genres", []) + detail.get("types", [])
            for g in raw_genres:
                if isinstance(g, str):
                    for t in tokenize_metadata(g):
                        if not t.isdigit() and len(t) >= 2:
                            structured_genres_counter[t] += 1

            # 2. Structured Regions
            raw_regions = detail.get("countries", []) + detail.get("regions", [])
            for r in raw_regions:
                if isinstance(r, str):
                    for t in tokenize_metadata(r):
                        if t.isdigit() or re.match(r"^[^\w\s]+$", t):
                            continue
                        if t.isascii() and len(t) < 2:
                            continue
                        structured_regions_counter[t] += 1
        except:
            continue

    # Known genres for degraded parsing
    known_genres = set(structured_genres_counter.keys())

    # Pass 2: Analyze subtitles and tags
    for (raw_data,) in raw_rows:
        if not raw_data:
            continue
        try:
            data = json.loads(raw_data)
            detail = data.get("detail", {})
            if not isinstance(detail, dict):
                continue

            # 3. Subtitles (Discovery)
            subtitles = [detail.get("card_subtitle"), detail.get("subtitle")]
            for subtitle in subtitles:
                if not isinstance(subtitle, str):
                    continue

                parts = [p.strip() for p in subtitle.split("/")]
                if not parts:
                    continue

                # Identify region parts based on year and genres
                # Standard: Year / Regions / Genres / ...
                region_parts = []
                start_idx = 0

                # Skip year if present
                if re.match(r"^\d{4}$", parts[0]):
                    start_idx = 1

                # Find the first part that contains a known genre
                genre_idx = -1
                for i in range(start_idx, len(parts)):
                    tokens = tokenize_metadata(parts[i])
                    if any(t in known_genres for t in tokens):
                        genre_idx = i
                        break

                if genre_idx != -1:
                    # Everything between year and genres is likely regions
                    region_parts = parts[start_idx:genre_idx]
                elif len(parts) > start_idx:
                    # Fallback: if no genre found, assume parts[start_idx] is region if it's not too long
                    p = parts[start_idx]
                    if len(p) < 30:
                        region_parts = [p]

                for p in region_parts:
                    for t in tokenize_metadata(p):
                        if t.isdigit() or re.match(r"^[^\w\s]+$", t):
                            continue
                        if t.isascii() and len(t) < 2:
                            continue

                        if t in structured_regions_counter:
                            structured_regions_counter[t] += 1
                        else:
                            unstructured_regions_counter[t] += 1

            # 4. Tags (often contain regions/genres)
            tags = detail.get("tags", [])
            for tag in tags:
                tag_name = tag.get("name") if isinstance(tag, dict) else tag
                if not isinstance(tag_name, str):
                    continue
                for t in tokenize_metadata(tag_name):
                    if t.isdigit() or re.match(r"^[^\w\s]+$", t):
                        continue
                    if t in structured_genres_counter:
                        structured_genres_counter[t] += 1
                    elif t in structured_regions_counter:
                        structured_regions_counter[t] += 1
        except:
            continue

    conn.close()

    # Final lists sorted alphabetically
    final_genres = sorted(
        [g for g, count in structured_genres_counter.items() if count >= 1]
    )

    # Subtitle discovery threshold
    discovered_regions = [
        r for r, count in unstructured_regions_counter.items() if count >= 5
    ]
    total_regions_counter = structured_regions_counter.copy()
    for r in discovered_regions:
        total_regions_counter[r] += unstructured_regions_counter[r]

    final_regions = sorted(
        [r for r, count in total_regions_counter.items() if count >= 1]
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Generated file. Do not edit manually.\n")
        f.write("# Generated from: " + os.path.basename(source_db_path) + "\n\n")

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
    if len(sys.argv) < 2:
        print("Usage: python3 generate_metadata.py <path_to_source_db>")
        sys.exit(1)

    source_db = sys.argv[1]
    # Detect project root to construct output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_file = os.path.join(project_root, "backend/app/metadata_constants.py")

    generate_metadata(source_db, output_file)
