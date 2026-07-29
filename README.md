# Literature Analysis Toolkit

A toolkit for merging, deduplicating, and normalizing multi-source literature data (Web of Science / PubMed / Scopus), with automated generation of trend plots, heatmaps, and Sankey diagrams.

## Project Structure

```
literature_analysis/
├── config.py              # Global configuration (paths, parameters)
├── src/
│   ├── __init__.py
│   ├── parsers.py         # Database-specific parsers
│   ├── merger.py          # Merge
│   ├── deduplicator.py    # Deduplication
│   ├── normalizer.py      # Keyword normalization
│   ├── keywords.py        # Model/Modality/Disease keyword dictionaries
│   ├── analyzer.py        # Statistics + Visualization + Sankey diagrams
│   └── utils.py           # Shared utility functions
├── data/
│   ├── 2/WOS/*.txt
│   ├── 2/PubMed/pubmed.txt
│   └── 2/Scopus/scopus.csv
├── output/                # Intermediates & visualization outputs
├── main.py                # One-click pipeline entry point
└── README.md
```

## Quick Start

```bash
# Install dependencies
pip install pandas matplotlib seaborn scikit-learn plotly

# Run the full pipeline
python main.py
```

## Run Steps

```bash
python -m src.merger        # Merge only
python -m src.deduplicator   # Deduplicate only (requires merged data)
python -m src.normalizer     # Normalize only (requires deduplicated data)
python -m src.analyzer       # Analyze & visualize only (requires normalized data)
```

## Configuration

Edit config.py to modify input/output paths, plotting parameters, and other settings.
