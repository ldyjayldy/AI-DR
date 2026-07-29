# -*- coding: utf-8 -*-
"""
Usage:
  - As module : from deduplicator import deduplicate
  - Standalone: python deduplicator.py

Dependencies:
  - Can be run independently (no dependencies on other project modules)
  - If imported as a module and utils functionality is required, ensure
    utils.py exists in the same directory.
"""

import re
import os
import sys


# ==================== Configurable Paths (Standalone Mode) ====================
DEFAULT_INPUT  = "merged_wos_format.txt"
DEFAULT_OUTPUT = "dedup_wos_format.txt"


# ==================== Utility Functions ====================

def normalize_text(text):
    """
    Text normalization:
      1. Strip leading/trailing whitespace
      2. Collapse consecutive spaces to a single space
      3. Convert to lowercase
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip()).lower()


def extract_first_author_surname(author_field):
    """
    Extract the first author's surname:
      Extract the first author's surname as the portion before the first comma,
      then convert to lowercase and trim.
    Examples: 'Smith, J; Johnson, A' → 'smith'
              'Wang, L.'             → 'wang'
    """
    if not author_field:
        return ""
    first_author = author_field.split(";")[0].strip()
    surname = first_author.split(",")[0].strip()
    return surname.lower()


def get_field_value(block, tag):
    """
    Extract the full content of a specified field (e.g., 'DI', 'TI', 'PY')
    from a single WOS record block. Supports continuation lines (starting
    with a space).
    """
    lines = block.split("\n")
    values = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(tag + " "):
            val = line[len(tag) + 1:]
            i += 1
            while i < len(lines) and lines[i].startswith(" "):
                val += " " + lines[i].strip()
                i += 1
            values.append(val)
        else:
            i += 1
    return "; ".join(values) if values else ""


def split_wos_blocks(content):
    """Split WOS-formatted text into a list of record blocks by 'PT ' lines."""
    blocks = re.split(r"(?=^PT )", content, flags=re.MULTILINE)
    return [b.strip() for b in blocks if b.strip()]


def write_blocks(blocks, filepath, separator="\n\n"):
    """Write a list of record blocks back to a file."""
    with open(filepath, "w", encoding="utf-8") as f:
        for block in blocks:
            f.write(block.strip())
            f.write(separator)


def read_blocks(filepath):
    """Read a WOS-format file and return a list of record blocks."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return split_wos_blocks(content)


def log(msg, level="INFO"):
    """Unified logging output."""
    prefix = {"INFO": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(level, "•")
    print(f"{prefix} {msg}")


# ==================== Stratified Key Generation ====================

def generate_dedup_key(block):
    """
    Generate a deduplication key using a 4-tier stratified strategy.

    Returns:
      ('doi',                   str)              → Level 1
      ('title_year',            (str, str))      → Level 2
      ('title_journal_author',  (str, str, str)) → Level 3
      None                                         → Level 4
    """

    # ===== Level 1: DOI-based =====
    # (1) Extract DOI → remove URL prefixes → lowercase → strip whitespace
    doi = get_field_value(block, "DI")
    if doi:
        # Lowercase first to handle uppercase variants (e.g., HTTPS://DOI.ORG/)
        doi_lower = doi.strip().lower()
        doi_clean = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi_lower)
        doi_clean = normalize_text(doi_clean)
        if doi_clean:
            return ("doi", doi_clean)

    # Common field extraction
    title   = get_field_value(block, "TI")
    year    = get_field_value(block, "PY")
    journal = get_field_value(block, "SO")
    authors = get_field_value(block, "AU")

    title_norm   = normalize_text(title)
    year_clean   = year.strip()
    journal_norm = normalize_text(journal)
    author_surname = extract_first_author_surname(authors)

    # ===== Level 2: Title + Year =====
    # (2) Title (normalized) + Year (stripped) → composite key
    if title_norm and year_clean:
        return ("title_year", (title_norm, year_clean))

    # ===== Level 3: Title + Journal + First Author =====
    # (3) Title + Journal + First Author surname → composite key
    if title_norm and journal_norm and author_surname and not year_clean:
        return ("title_journal_author",
                (title_norm, journal_norm, author_surname))

    # ===== Level 4: Unable to generate key =====
    # (4) Retain without comparison to ensure data integrity
    if not title_norm:
        log("Record lacks both DOI and valid title; retained without deduplication (Level 4)", "WARN")
    elif not journal_norm:
        log(f"Record missing journal title (Title: {title_norm[:40]}…); cannot generate L3 key, retained", "WARN")
    elif not author_surname:
        log(f"Record missing author info (Title: {title_norm[:40]}…); cannot generate L3 key, retained", "WARN")

    return None


# ==================== Core Deduplication Function ====================

def deduplicate(input_path=None, output_path=None):
    """
    Perform stratified precise deduplication on a WOS-format file.

    Args:
      input_path  : Path to input WOS-format .txt file
      output_path : Path to output WOS-format .txt file

    Returns:
      (kept_count, duplicate_count, no_key_count)
    """
    input_path  = input_path  or DEFAULT_INPUT
    output_path = output_path or DEFAULT_OUTPUT

    if not os.path.exists(input_path):
        log(f"Input file not found: {input_path}", "ERROR")
        return 0, 0, 0

    blocks = read_blocks(input_path)
    log(f"Parsed {len(blocks)} raw records")

    seen = {}
    unique_blocks = []
    duplicate_count = 0
    no_key_count = 0
    level_stats = {"doi": 0, "title_year": 0, "title_journal_author": 0}

    for block in blocks:
        key = generate_dedup_key(block)

        if key is None:
            # Level 4: No key, retain without comparison
            no_key_count += 1
            unique_blocks.append(block)

        elif key in seen:
            # Key collision → duplicate
            duplicate_count += 1

        else:
            # New key → retain
            seen[key] = True
            unique_blocks.append(block)
            if key[0] in level_stats:
                level_stats[key[0]] += 1

    # Write output
    write_blocks(unique_blocks, output_path)

    # Summary logging
    log("-" * 55)
    log("Deduplication Complete (Stratified Precise Matching Strategy)")
    log(f"  Level 1 — DOI                    : {level_stats['doi']} records kept")
    log(f"  Level 2 — Title + Year           : {level_stats['title_year']} records kept")
    log(f"  Level 3 — Title + Journal + Auth.: {level_stats['title_journal_author']} records kept")
    log(f"  Level 4 — No valid key (retained): {no_key_count} records")
    log(f"  {'-'*40}")
    log(f"  Duplicates removed: {duplicate_count}")
    log(f"  Final records kept: {len(unique_blocks)}")
    log(f"  Output file       : {output_path}")

    return len(unique_blocks), duplicate_count, no_key_count


# ==================== Standalone Execution ====================

if __name__ == "__main__":
    # CLI usage: python deduplicator.py [input] [output]
    input_arg  = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    output_arg = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT
    deduplicate(input_arg, output_arg)