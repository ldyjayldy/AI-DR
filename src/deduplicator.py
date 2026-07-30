# -*- coding: utf-8 -*-
"""
Deduplicator — Stratified Precise Matching Strategy
===================================================

Usage:
  - As module : from deduplicator import deduplicate
  - Standalone: python deduplicator.py [input] [output]

Deduplication Rules (aligned with methodological description):
  Level 1 — DOI-based:
      Standardize DOI → remove URL prefixes → lowercase → strip whitespace.
      Identical DOIs   → duplicates; retain the first occurrence.

  Level 2 — Composite key (Title + Year + First Author):
      Title  : lowercase, collapse spaces, REMOVE punctuation.
      Year   : strip surrounding whitespace.
      Author : first surname before the first comma, lowercase.
      Identical composite key → candidate duplicates.

  Level 3 — Secondary Journal Verification:
      Within each candidate group, compare normalized journal names.
      Exact match  → auto-dedup, keep the EARLIEST recorded entry.
      Mismatch     → preserve BOTH records, flag for manual inspection.

  Level 4 — Incomplete metadata:
      Records lacking DOI / valid title / valid year cannot generate a key.
      They are RETAINED and EXCLUDED from deduplication (conservative strategy).

Dependencies:
  - Pure standard library (re, os, sys, string).
  - No external packages required.
"""

import re
import os
import sys
import string


# ==================== Configurable Paths (Standalone Mode) ====================
DEFAULT_INPUT       = "merged_wos_format.txt"
DEFAULT_OUTPUT      = "dedup_wos_format.txt"
DEFAULT_FLAGGED_OUT = "flagged_for_manual_inspection.txt"


# ==================== Utility Functions ====================

def normalize_text(text):
    """
    Basic text normalization:
      1. Strip leading/trailing whitespace
      2. Collapse consecutive spaces to a single space
      3. Convert to lowercase
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip()).lower()


def normalize_title(text):
    """
    Title normalization (enhanced per methodology):
      1. Strip leading/trailing whitespace
      2. Collapse consecutive spaces to a single space
      3. Convert to lowercase
      4. Remove ALL punctuation characters
    """
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip()).lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_journal(text):
    """
    Journal name normalization for exact-match comparison:
      1. Strip / collapse spaces / lowercase
      2. Remove punctuation
    """
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text.strip()).lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_first_author_surname(author_field):
    """
    Extract the first author's surname:
      Take the substring before the first comma, lowercase, trimmed.
    Examples:
      'Smith, J; Johnson, A' → 'smith'
      'Wang, L.'             → 'wang'
    """
    if not author_field:
        return ""
    first_author = author_field.split(";")[0].strip()
    surname = first_author.split(",")[0].strip()
    return surname.lower()


def extract_year(block):
    """Extract publication year as int, or None if invalid/missing."""
    year_str = get_field_value(block, "PY")
    try:
        return int(year_str.strip()) if year_str else None
    except ValueError:
        return None


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
    Generate a deduplication key using the stratified strategy.

    Returns:
      ('doi',             str)             → Level 1
      ('composite',       (str,str,str))  → Level 2  (title, author, year)
      None                                  → Level 4  (cannot generate key)
    """

    # ===== Level 1: DOI-based =====
    doi = get_field_value(block, "DI")
    if doi:
        doi_lower = doi.strip().lower()
        # Remove common DOI URL prefixes
        doi_clean = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi_lower)
        doi_clean = normalize_text(doi_clean)
        if doi_clean:
            return ("doi", doi_clean)

    # ===== Common field extraction for Level 2 =====
    title_raw   = get_field_value(block, "TI")
    year_raw    = get_field_value(block, "PY")
    authors_raw = get_field_value(block, "AU")

    title_norm    = normalize_title(title_raw)     # lowercase + no punctuation
    year_clean    = year_raw.strip()
    author_surname = extract_first_author_surname(authors_raw)

    # ===== Level 2: Composite key =====
    if title_norm and year_clean and author_surname:
        return ("composite", (title_norm, author_surname, year_clean))

    # ===== Level 4: Insufficient metadata =====
    if not title_norm:
        log("Record lacks DOI and valid title; retained without deduplication (L4)", "WARN")
    elif not year_clean:
        log(f"Record missing publication year (Title: {title_norm[:40]}…); retained (L4)", "WARN")
    elif not author_surname:
        log(f"Record missing author info (Title: {title_norm[:40]}…); retained (L4)", "WARN")

    return None


# ==================== Core Deduplication Function ====================

def deduplicate(input_path=None, output_path=None, flagged_output_path=None):
    """
    Perform stratified precise deduplication on a WOS-format file.

    Args:
      input_path         : Path to input WOS-format .txt file
      output_path        : Path to output WOS-format .txt file (deduplicated)
      flagged_output_path: Path for records flagged for manual inspection

    Returns:
      (kept_count, duplicate_count, no_key_count, flagged_count)
    """
    input_path         = input_path         or DEFAULT_INPUT
    output_path        = output_path        or DEFAULT_OUTPUT
    flagged_output_path = flagged_output_path or DEFAULT_FLAGGED_OUT

    if not os.path.exists(input_path):
        log(f"Input file not found: {input_path}", "ERROR")
        return 0, 0, 0, 0

    blocks = read_blocks(input_path)
    log(f"Parsed {len(blocks)} raw records")

    # -------- Level 1: DOI-based pass --------
    doi_seen = {}           # doi_clean → index in doi_kept
    doi_kept = []
    doi_dup_count = 0

    for block in blocks:
        key = generate_dedup_key(block)
        if key and key[0] == "doi":
            doi_val = key[1]
            if doi_val in doi_seen:
                doi_dup_count += 1
                continue
            doi_seen[doi_val] = len(doi_kept)
            doi_kept.append(block)
        else:
            # No DOI or non-DOI key → carry forward
            doi_kept.append(block)

    log(f"  After DOI pass: {len(doi_kept)} kept, {doi_dup_count} DOI duplicates removed")

    # -------- Level 2 + 3: Composite key + Journal verification --------
    # We rebuild: separate DOI records (already finalized) from no-DOI records
    doi_final_blocks = []
    no_doi_blocks = []
    for block in doi_kept:
        if get_field_value(block, "DI").strip():
            doi_final_blocks.append(block)
        else:
            no_doi_blocks.append(block)

    # comp_seen: composite_key → index in final_blocks
    comp_seen = {}
    final_blocks = list(doi_final_blocks)   # start with DOI-resolved records

    duplicate_count = 0
    no_key_count = 0
    flagged_blocks = []
    flagged_count = 0
    level_stats = {"doi": len(doi_seen), "composite": 0}

    for block in no_doi_blocks:
        key = generate_dedup_key(block)

        # ---- Level 4: Cannot generate key ----
        if key is None:
            no_key_count += 1
            final_blocks.append(block)
            continue

        # key[0] == "composite"
        title_norm, author_surname, year_clean = key[1]

        # Build comparison tuple with journal for secondary verification
        journal_norm = normalize_journal(get_field_value(block, "SO"))
        composite_key = ("composite", (title_norm, author_surname, year_clean))

        if composite_key not in comp_seen:
            # First occurrence → keep
            comp_seen[composite_key] = {
                "index": len(final_blocks),
                "journal": journal_norm,
                "year": extract_year(block),
                "block": block
            }
            level_stats["composite"] += 1
            final_blocks.append(block)
        else:
            # ---- Candidate duplicate → Level 3 journal verification ----
            prev = comp_seen[composite_key]
            prev_journal = prev["journal"]
            curr_journal = journal_norm

            if prev_journal and curr_journal and prev_journal == curr_journal:
                # Exact journal match → auto-dedup, keep EARLIER year
                curr_year = extract_year(block)
                prev_year = prev["year"]

                if curr_year and prev_year and curr_year < prev_year:
                    # Replace previously kept block with the earlier one
                    idx = prev["index"]
                    final_blocks[idx] = block
                    comp_seen[composite_key]["block"] = block
                    comp_seen[composite_key]["year"] = curr_year
                    log(f"Replaced with earlier record (year {curr_year} < {prev_year})", "INFO")

                duplicate_count += 1
            else:
                # Journal mismatch → preserve both, flag for manual inspection
                flagged_count += 1
                flagged_blocks.append(block)
                # Also keep in final output (do NOT remove)
                log(
                    f"Composite key matched but journal differs "
                    f"('{prev_journal}' vs '{curr_journal}'); "
                    f"both retained, flagged for manual review",
                    "WARN"
                )
                # Register a NEW entry so future matches still work
                comp_seen[composite_key] = {
                    "index": len(final_blocks),
                    "journal": journal_norm,
                    "year": extract_year(block),
                    "block": block
                }
                final_blocks.append(block)

    # -------- Write outputs --------
    write_blocks(final_blocks, output_path)
    if flagged_blocks:
        write_blocks(flagged_blocks, flagged_output_path)

    # -------- Summary --------
    log("-" * 62)
    log("Deduplication Complete (Stratified Precise Matching Strategy)")
    log(f"  Level 1 — DOI exact match                : {level_stats['doi']} kept, {doi_dup_count} removed")
    log(f"  Level 2 — Composite key (Title+Author+Yr): {level_stats['composite']} kept")
    log(f"  Level 3 — Auto-dedup via journal verify  : {duplicate_count} removed (kept earliest)")
    log(f"  Level 3 — Flagged (journal mismatch)     : {flagged_count} preserved for manual review")
    log(f"  Level 4 — No valid key (retained)        : {no_key_count} kept")
    log(f"  {'-'*48}")
    log(f"  Total duplicates removed : {doi_dup_count + duplicate_count}")
    log(f"  Final records kept      : {len(final_blocks)}")
    log(f"  Output file             : {output_path}")
    if flagged_count > 0:
        log(f"  Flagged file            : {flagged_output_path}")
    log("  Strategy: Conservative — prioritize preventing false positives.")

    return len(final_blocks), (doi_dup_count + duplicate_count), no_key_count, flagged_count


# ==================== Standalone Execution ====================

if __name__ == "__main__":
    # CLI usage: python deduplicator.py [input] [output] [flagged_output]
    input_arg   = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    output_arg  = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT
    flagged_arg = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_FLAGGED_OUT
    deduplicate(input_arg, output_arg, flagged_arg)
