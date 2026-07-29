# -*- coding: utf-8 -*-
"""
Utility Functions: Regex parsing, text cleaning, etc.
"""

import re
import os
import glob
from collections import OrderedDict


# ==================== File & Path Operations ====================

def ensure_dir(path):
    """Ensure a directory exists; create it if it does not."""
    os.makedirs(path, exist_ok=True)


def find_files(folder, pattern="*.txt"):
    """Return a sorted list of files matching the given pattern in a directory."""
    return sorted(glob.glob(os.path.join(folder, pattern)))


# ==================== Record Block Operations ====================

def split_wos_blocks(content):
    blocks = re.split(r"(?=^PT )", content, flags=re.MULTILINE)
    return [b.strip() for b in blocks if b.strip()]


def write_blocks(blocks, filepath, separator="\n\n"):
    """Write a list of record blocks back to a file."""
    with open(filepath, "w", encoding="utf-8") as f:
        for block in blocks:
            f.write(block.strip())
            f.write(separator)


def read_blocks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return split_wos_blocks(content)


# ==================== Field Extraction ====================

def get_field_value(block, tag):
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


def parse_wos_lines(lines):
    records = []
    current = {}
    in_record = False

    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue

        if line.startswith("PT J") or line.startswith("PT S"):
            if current:
                records.append(current)
            current = {}
            in_record = True
            current["PT"] = line.split()[1] if len(line.split()) > 1 else "J"
            continue

        if line.startswith("ER"):
            if current:
                records.append(current)
            current = {}
            in_record = False
            continue

        if in_record:
            match = re.match(r"^([A-Z]{2,3})\s+(.*)$", line)
            if match:
                tag, value = match.group(1), match.group(2)
                if tag in current:
                    current[tag] += "; " + value
                else:
                    current[tag] = value
            else:
                # Continuation line
                if current:
                    last_tag = list(current.keys())[-1]
                    current[last_tag] += " " + line.strip()

    if current:
        records.append(current)
    return records


def parse_wos_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return parse_wos_lines(lines)


# ==================== Text Cleaning ====================

def clean_text(text):
    """Trim whitespace, collapse consecutive spaces, and convert to lowercase."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def normalize_doi(doi):
    """Normalize a DOI: remove URL prefixes and convert to lowercase."""
    if not doi:
        return ""
    doi_clean = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi_clean.strip().lower()


# ==================== Record ====================

def write_wos_record(f, rec, ordered_keys=None):
    if ordered_keys is None:
        ordered_keys = [
            "PT", "AU", "TI", "SO", "PY", "VL", "IS",
            "BP", "EP", "DI", "AB", "DE", "ID", "TC", "UT",
        ]

    f.write(f"PT {rec.get('PT', 'J')}\n")
    written = {"PT"}
    for key in ordered_keys:
        if key in rec and rec[key]:
            f.write(f"{key} {rec[key]}\n")
            written.add(key)
    # Write remaining fields
    for key, val in rec.items():
        if key not in written and val:
            f.write(f"{key} {val}\n")
    f.write("ER\n\n")


# ==================== Logging ====================

def log(msg, level="INFO"):
    """Unified logging output with emoji prefixes."""
    prefix = {"INFO": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(level, "•")
    print(f"{prefix} {msg}")