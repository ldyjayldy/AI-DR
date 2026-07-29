# -*- coding: utf-8 -*-

import time
import config
from src.utils import log, ensure_dir
from src.merger import merge_all
from src.deduplicator import deduplicate
from src.normalizer import normalize_file
from src.analyzer import run_analysis


def main():
    start = time.time()
    ensure_dir(config.OUTPUT_DIR)

    log("=" * 60)
    log("🚀 Starting literature analysis pipeline")
    log("=" * 60)

    # Step 1: Merge
    log("\n📦 Step 1/4 — Merging multi-source data")
    n = merge_all()
    log(f"   → Merged {n} records")

    # Step 2: Deduplicate
    log("\n🔎 Step 2/4 — Deduplicating records")
    kept, dup, no_key = deduplicate()
    log(f"   → Kept {kept} records (removed {dup} duplicates, {no_key} without keys)")

    # Step 3: Normalize
    log("\n📝 Step 3/4 — Keyword normalization")
    n_norm = normalize_file()
    log(f"   → Normalized {n_norm} records")

    # Step 4: Analyze & Visualize
    log("\n📊 Step 4/4 — Analysis & Visualization")
    run_analysis()

    elapsed = time.time() - start
    log(f"\n✅ Pipeline completed! Total time: {elapsed:.1f}s")
    log(f"📁 Output directory: {config.OUTPUT_DIR}")


if __name__ == "__main__":
    main()