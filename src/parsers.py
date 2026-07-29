# -*- coding: utf-8 -*-
"""
Database Format Parsers:
  - parse_wos_file: Parse Web of Science plain text exports
  - parse_pubmed_medline: Parse PubMed MEDLINE formatted files
  - parse_scopus_csv: Parse Scopus CSV exports
"""

import re
import csv
import os

from .utils import parse_wos_lines, normalize_doi


# ==================== WOS Parser ====================

def parse_wos_file(filepath):
    """Parse Web of Science plain text (.txt) files and return a list of record dictionaries."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return parse_wos_lines(lines)


# ==================== PubMed Parser ====================

def parse_pubmed_medline(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    records = []
    current = {}

    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue

        match = re.match(r"^([A-Z]{2,4})\s*[-]?\s*(.*)", line)
        if match:
            tag = match.group(1)
            value = match.group(2).strip()

            if tag == "PMID":
                if current:
                    records.append(current)
                current = {"PMID": value}
            else:
                if tag in current:
                    if isinstance(current[tag], list):
                        current[tag].append(value)
                    else:
                        current[tag] = [current[tag], value]
                else:
                    current[tag] = value
        else:
            # Continuation line
            if current:
                last_key = list(current.keys())[-1]
                if isinstance(current[last_key], list):
                    current[last_key][-1] += " " + line.strip()
                else:
                    current[last_key] += " " + line.strip()

    if current:
        records.append(current)
    return records


# ==================== Scopus Parser ====================

def parse_scopus_csv(filepath):
    """Parse Scopus-exported CSV files and return a list of record dictionaries (one per row)."""
    records = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


# ==================== Field Mapping ====================

def map_scopus_to_wos(row):
    """Map a single Scopus record to the Web of Science (WOS) field schema."""
    wos = {"PT": "J"}

    field_map = [
        ("Authors", "AU"),
        ("Title", "TI"),
        ("Source title", "SO"),
        ("Year", "PY"),
        ("Volume", "VL"),
        ("Issue", "IS"),
        ("DOI", "DI"),
        ("Abstract", "AB"),
        ("Cited by", "TC"),
    ]
    for src, dst in field_map:
        if row.get(src):
            wos[dst] = row[src]

    # Page numbers
    start = row.get("Page start", "")
    end = row.get("Page end", "")
    if start and end:
        wos["BP"] = start
        wos["EP"] = end
    elif start:
        wos["BP"] = start

    # Keywords
    keywords = []
    if row.get("Author Keywords"):
        keywords.append(row["Author Keywords"])
    if row.get("Index Keywords"):
        keywords.append(row["Index Keywords"])
    if keywords:
        wos["DE"] = "; ".join(keywords)

    # Accession Number (UT field)
    if row.get("EID"):
        wos["UT"] = "SCOPUS:" + row["EID"]
    elif row.get("DOI"):
        wos["UT"] = "DOI:" + row["DOI"]
    else:
        wos["UT"] = "SCOPUS:" + str(hash(row.get("Title", "")))

    return wos


def map_pubmed_to_wos(rec):
    """Map a single PubMed record to the Web of Science (WOS) field schema."""
    wos = {"PT": "J"}

    # Authors
    if "AU" in rec:
        au = rec["AU"]
        wos["AU"] = "; ".join(au) if isinstance(au, list) else au

    # Title / Source
    for src, dst in [("TI", "TI"), ("SO", "SO")]:
        if rec.get(src):
            wos[dst] = rec[src]

    # Publication Year
    if "DP" in rec:
        yr_match = re.search(r"(\d{4})", rec["DP"])
        if yr_match:
            wos["PY"] = yr_match.group(1)

    # Volume / Issue
    if "VI" in rec:
        wos["VL"] = rec["VI"]
    if "IP" in rec:
        wos["IS"] = rec["IP"]

    # Page Numbers
    if "PG" in rec:
        pages = rec["PG"]
        if "-" in pages:
            parts = pages.split("-")
            wos["BP"] = parts[0].strip()
            wos["EP"] = parts[1].strip()
        else:
            wos["BP"] = pages

    # DOI
    if "AID" in rec:
        aid_data = rec["AID"]
        if not isinstance(aid_data, list):
            aid_data = [aid_data]
        for item in aid_data:
            doi_match = re.search(r"(10\.\S+)", item)
            if doi_match:
                wos["DI"] = doi_match.group(1)
                break

    # Abstract
    if "AB" in rec:
        wos["AB"] = rec["AB"]

    # MeSH Terms
    if "MH" in rec:
        mh = rec["MH"]
        wos["DE"] = "; ".join(mh) if isinstance(mh, list) else mh

    # Accession Number (UT field)
    if "PMID" in rec:
        wos["UT"] = "PUBMED:" + rec["PMID"]
    else:
        wos["UT"] = "PUBMED:" + str(hash(rec.get("TI", "")))

    return wos