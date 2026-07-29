# -*- coding: utf-8 -*-
"""
Merge Module
"""

import os
import glob

import config
from .utils import write_wos_record, log, find_files
from .parsers import (
    parse_wos_file,
    parse_pubmed_medline,
    parse_scopus_csv,
    map_scopus_to_wos,
    map_pubmed_to_wos,
)


def merge_all(wos_folder=None, pubmed_path=None, scopus_path=None, output_path=None):
    wos_folder = wos_folder or config.WOS_FOLDER
    pubmed_path = pubmed_path or config.PUBMED_TXT
    scopus_path = scopus_path or config.SCOPUS_CSV
    output_path = output_path or config.MERGED_FILE

    all_records = []

    # 1. WOS files
    log("Parsing WOS files...")
    wos_files = find_files(wos_folder, "*.txt")
    if not wos_files:
        log(f"No WOS files found ({wos_folder}), skipping", "WARN")
    for fp in wos_files:
        recs = parse_wos_file(fp)
        all_records.extend(recs)
        log(f"  {os.path.basename(fp)} → {len(recs)} records")

    # 2. PubMed
    if os.path.exists(pubmed_path):
        log("Parsing PubMed file...")
        pubmed_recs = parse_pubmed_medline(pubmed_path)
        log(f"  PubMed → {len(pubmed_recs)} records")
        for rec in pubmed_recs:
            all_records.append(map_pubmed_to_wos(rec))
    else:
        log(f"PubMed file not found ({pubmed_path}), skipping", "WARN")

    # 3. Scopus
    if os.path.exists(scopus_path):
        log("Parsing Scopus CSV file...")
        scopus_recs = parse_scopus_csv(scopus_path)
        log(f"  Scopus → {len(scopus_recs)} records")
        for row in scopus_recs:
            all_records.append(map_scopus_to_wos(row))
    else:
        log(f"Scopus file not found ({scopus_path}), skipping", "WARN")

    log(f"Total merged records: {len(all_records)}")

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            write_wos_record(f, rec)

    log(f"Merge complete → {output_path}")
    return len(all_records)


if __name__ == "__main__":
    merge_all()