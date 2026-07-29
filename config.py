# -*- coding: utf-8 -*-
"""
Global Configuration: Paths, parameters, keyword dictionary toggles, etc.
All paths are relative to the project root directory (literature_analysis/).
"""


import os

# ==================== Path Configuration ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
WOS_FOLDER = os.path.join(DATA_DIR, "2", "WOS")         
PUBMED_TXT = os.path.join(DATA_DIR, "2", "PubMed", "pubmed.txt")
SCOPUS_CSV = os.path.join(DATA_DIR, "2", "Scopus", "scopus.csv")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MERGED_FILE = os.path.join(OUTPUT_DIR, "merged_wos_format.txt")
DEDUP_FILE = os.path.join(OUTPUT_DIR, "dedup_wos_format.txt")
NORMALIZED_FILE = os.path.join(OUTPUT_DIR, "normalized_wos_format.txt")
CANDIDATES_CSV = os.path.join(OUTPUT_DIR, "keyword_candidates.csv")

# ==================== Plotting Parameters ====================
STREAM_TOP_N = {
    "model": 15,
    "modality": 12,
    "disease": 12,
}

HEATMAP_TOP_N = {
    "model": 15,
    "modality": 12,
    "disease": 12,
}

SANKEY_TOP_N = {
    "model": 15,
    "modality": 12,
    "disease": 12,
}

YEAR_RANGE_FULL = (1996, 2026)
YEAR_RANGE_RECENT = (2010, 2025)

# ==================== Normalization Rules Toggle ====================
ENABLE_NORMALIZATION = True

# ==================== Sankey Diagram Color Scheme ====================
SANKEY_PALETTE = "custom"  # custom | vivid | husl | morandi | pastel

# ==================== High-Frequency Term Extraction ====================
CANDIDATE_TOP_N = 200
CANDIDATE_MIN_FREQ = 2

CUSTOM_STOP_WORDS = [
    "study", "method", "analysis", "result", "results", "aim", "purpose",
    "background", "objective", "conclusion", "introduction", "material", "methodology",
    "patient", "eye", "retina", "retinal", "image", "imaging", "vision",
    "optical", "coherence", "tomography", "angiography", "fundus", "photography",
    "diagnosis", "detection", "segmentation", "classification", "evaluation",
    "assessment", "measurement", "comparison", "prognosis", "outcome",
    "clinical", "model", "approach", "technique", "algorithm",
]
