# -*- coding: utf-8 -*-
"""
Analysis & Visualization Module:
  - High-frequency candidate term extraction
  - Stacked area plots (trend analysis)
  - Hierarchical heatmaps
  - Sankey diagrams (Model → Modality → Disease)
  - One-click PDF / HTML report generation
"""

import re
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams["font.family"] = "WenQuanYi Micro Hei"
matplotlib.rcParams["axes.unicode_minus"] = False

import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.feature_extraction.text import CountVectorizer

import config
from .utils import log, parse_wos_lines, get_field_value
from .keywords import (
    BASE_MODEL_KEYWORDS,
    MODALITY_KEYWORDS,
    DISEASE_KEYWORDS,
    expand_model_keywords,
    is_likely_model_name,
)


# ==================== Color Utilities ====================

def get_academic_colors(n):
    """Return n distinct colors based on the 'tab20' palette."""
    return sns.color_palette("tab20", n).as_hex()


# ==================== Parsing ====================

def parse_wos_file(filepath):
    """Parse a normalized WOS file into a list of record dictionaries."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    records = []
    current = {}
    inside = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("PT J") or line.startswith("PT S"):
            if current:
                records.append(current)
            current = {}
            inside = True
            current["PT"] = line.split()[1] if len(line.split()) > 1 else "J"
            continue
        if line.startswith("ER"):
            if current:
                records.append(current)
            current = {}
            inside = False
            continue
        if inside:
            match = re.match(r"^([A-Z]{2,3})\s+(.*)$", line)
            if match:
                tag, value = match.groups()
                if tag in current:
                    current[tag] += " " + value
                else:
                    current[tag] = value
            else:
                if current:
                    last_tag = list(current.keys())[-1]
                    current[last_tag] += " " + line
    if current:
        records.append(current)
    return records


# ==================== Keyword Matching ====================

def count_keywords(text, keyword_dict):
    """Perform binary keyword matching (0/1) on text.
    
    Returns:
        dict: {category: 0/1}
    """
    counts = {}
    for cat, pattern in keyword_dict.items():
        counts[cat] = 1 if re.search(pattern, text, flags=re.IGNORECASE) else 0
    return counts


def build_corpus(records):
    """Extract text corpus (Title + Abstract + Keywords) from records."""
    texts = []
    for rec in records:
        parts = [rec.get("TI", ""), rec.get("AB", ""), rec.get("DE", ""), rec.get("ID", "")]
        text = " ".join(parts)
        if text.strip():
            texts.append(text)
    return texts


# ==================== High-Frequency Candidate Terms ====================

def extract_candidates(texts, top_n=None, min_freq=None):
    """Extract high-frequency n-gram candidates using CountVectorizer."""
    top_n = top_n or config.CANDIDATE_TOP_N
    min_freq = min_freq or config.CANDIDATE_MIN_FREQ

    vectorizer = CountVectorizer(
        ngram_range=(1, 4),
        stop_words="english",
        max_df=0.8,
        min_df=min_freq,
        max_features=5000,
    )
    X = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()
    counts = X.toarray().sum(axis=0)

    candidates = []
    for word, count in zip(feature_names, counts):
        if len(word) < 2 or word[0].isdigit():
            continue
        if word.lower() in config.CUSTOM_STOP_WORDS:
            continue
        parts = word.split()
        if all(p.lower() in config.CUSTOM_STOP_WORDS for p in parts):
            continue
        candidates.append((word, int(count)))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:top_n]


def print_candidates(candidates, n=30):
    """Print the list of candidate terms."""
    print("\n" + "=" * 70)
    print("🔍 High-Frequency Candidates (Consider adding to model list)")
    print("=" * 70)
    print(f"{'Freq':<6} {'Candidate Phrase':<35} {'Feature'}")
    print("-" * 70)
    for word, count in candidates[:n]:
        flag = "✅ Likely a model" if is_likely_model_name(word) else "🤔 Possibly generic"
        print(f"{count:<6} {word:<35} {flag}")
    print("=" * 70)


# ==================== DataFrame Construction ====================

def records_to_dataframe(records, model_keywords):
    """Convert record list to DataFrame with year and hit markers."""
    data = []
    for rec in records:
        year = rec.get("PY")
        if not year or not str(year).isdigit():
            continue
        year = int(year)
        if year < 1900 or year > 2030:
            continue
        text = " ".join([rec.get("TI", ""), rec.get("AB", ""), rec.get("DE", ""), rec.get("ID", "")])
        row = {"year": year}
        row.update({f"model_{k}": v for k, v in count_keywords(text, model_keywords).items()})
        row.update({f"modality_{k}": v for k, v in count_keywords(text, MODALITY_KEYWORDS).items()})
        row.update({f"disease_{k}": v for k, v in count_keywords(text, DISEASE_KEYWORDS).items()})
        data.append(row)
    return pd.DataFrame(data)


# ==================== Stacked Area Plots ====================

def plot_stream(df, prefix, title, top_n=None, xlabel="Year", ylabel=None,
                normalize=False, palette=None, figsize=(12, 6)):
    """Generate a stacked area plot."""
    yearly = df.groupby("year").sum()
    cols = [c for c in yearly.columns if c.startswith(prefix)]
    if not cols:
        return None

    total_counts = yearly[cols].sum().sort_values(ascending=False)
    total_counts = total_counts[total_counts > 0]
    if total_counts.empty:
        return None

    top_n = top_n or len(total_counts)
    plot_cols = total_counts.head(top_n).index.tolist()
    plot_labels = [c.replace(prefix, "") for c in plot_cols]

    data = yearly[plot_cols].fillna(0)
    if normalize:
        col_sums = data.sum(axis=1).replace(0, np.nan)
        data = data.div(col_sums, axis=0)
        ylabel = ylabel or "Proportion"
        title = title + " (Proportion)"
    else:
        ylabel = ylabel or "Number of Publications"

    years = data.index.values
    n_cats = len(plot_cols)
    colors = sns.color_palette(palette or "tab20", n_cats).as_hex() if isinstance(palette, str) \
        else (palette or get_academic_colors(n_cats))

    fig, ax = plt.subplots(figsize=figsize)
    ax.stackplot(years, data.values.T, labels=plot_labels, colors=colors,
                 baseline="zero", alpha=0.85)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), frameon=False)
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()
    return fig


# ==================== Hierarchical Heatmaps ====================

def _prepare_heatmap_data(yearly, prefix, top_n=None, normalize=False):
    """Extract and format data for a single-layer heatmap."""
    cols = [c for c in yearly.columns if c.startswith(prefix)]
    if not cols:
        return None
    data = yearly[cols].T
    data = data[data.sum(axis=1) > 0]
    if data.empty:
        return None
    if top_n and len(data) > top_n:
        keep = data.sum(axis=1).sort_values(ascending=False).head(top_n).index
        data = data.loc[keep]
    if normalize:
        row_sums = data.sum(axis=1).replace(0, np.nan)
        data = data.div(row_sums, axis=0)
    data.columns = data.columns.astype(str)
    data.index = [c.replace(prefix, "") for c in data.index]
    return data


def plot_hierarchical_heatmap(df, pdf, year_start=None, top_n_model=None,
                                top_n_modality=None, top_n_disease=None,
                                normalize_model=False, normalize_modality=False,
                                normalize_disease=False, vmax_prop=0.6):
    """Generate three-layer hierarchical heatmaps and save to PDF."""
    if year_start is not None:
        df = df[df["year"] >= year_start].copy()
    if df.empty:
        return

    yearly = df.groupby("year").sum()
    cmaps = {"model": "Reds", "modality": "Blues", "disease": "Greens"}
    name_map = {
        "model": "Models / Algorithms",
        "modality": "Data Modalities",
        "disease": "Diseases / Conditions",
    }

    layers = []
    norms = []
    for key, prefix in [("model", "model_"), ("modality", "modality_"), ("disease", "disease_")]:
        top = {"model": top_n_model, "modality": top_n_modality, "disease": top_n_disease}[key]
        norm = {"model": normalize_model, "modality": normalize_modality, "disease": normalize_disease}[key]
        data = _prepare_heatmap_data(yearly, prefix, top_n=top, normalize=norm)
        layers.append((key, data))
        norms.append(norm)

    valid = [(k, d) for k, d in layers if d is not None]
    if not valid:
        return

    n_rows = len(valid)
    fig, axes = plt.subplots(n_rows, 1, figsize=(14, 4 * n_rows), sharex=True)
    if n_rows == 1:
        axes = [axes]

    for idx, (key, data) in enumerate(valid):
        norm = norms[idx]
        ax = axes[idx]
        base_title = name_map[key]
        title_str = base_title + (" (Proportion per Category)" if norm else " (Absolute Counts)")
        cbar_label = "Proportion" if norm else "Publication Count"

        sns.heatmap(
            data,
            cmap=cmaps[key],
            annot=False,
            vmin=0,
            vmax=vmax_prop if norm else None,
            cbar_kws={"label": cbar_label},
            ax=ax,
            square=False,
            linewidths=0.1,
            linecolor="black",
        )
        ax.set_title(title_str, fontsize=14)
        ax.set_ylabel("")
        if len(data.columns) > 20:
            step = max(1, len(data.columns) // 15)
            for i, label in enumerate(ax.get_xticklabels()):
                if i % step != 0:
                    label.set_visible(False)

    axes[-1].set_xlabel("Year", fontsize=12)
    fig.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


# ==================== Sankey Diagrams ====================

# 40-color warm-tone palette (first 16 fixed + 24 extended)
_CUSTOM_40 = [
    "#F86B58", "#FFA06E", "#F9E296", "#D2E4C4", "#57CBD9",
    "#62A99E", "#07C0C0", "#D8B396", "#F2B3CB", "#DCC8E0",
    "#89F0B3", "#96D7E6", "#D6DD96", "#FFD700", "#FFC470",
    "#FFC8D3",
    "#F5A08C", "#F7B08A", "#FAC08A", "#FCD08A", "#FEE08A",
    "#F0D080", "#E8C87A", "#E0B86A", "#D8A85A", "#D09850",
    "#C89048", "#C08040", "#B87838", "#B07030", "#A86828",
    "#F0C8C0", "#E8B8B0", "#E0A8A0", "#D89890", "#D08880",
    "#C0D8D0", "#B0C8C0", "#A0B8B0", "#90A8A0",
]
# Shuffle order (stride sampling) to maximize color contrast between adjacent nodes
_CUSTOM_SHUFFLED = _CUSTOM_40[::2] + _CUSTOM_40[1::2]


def _get_sankey_palette(n, palette_type="custom"):
    """Return a list of n colors for Sankey nodes."""
    if palette_type == "custom":
        return [_CUSTOM_SHUFFLED[i % len(_CUSTOM_SHUFFLED)] for i in range(n)]
    elif palette_type == "vivid":
        pal = sns.color_palette("Set1", n)
    elif palette_type == "husl":
        pal = sns.color_palette("husl", n, desat=0.2)
    elif palette_type == "pastel":
        pal = sns.color_palette("pastel", n)
    elif palette_type == "morandi":
        morandi = [
            "#E8D5C4", "#C6D8D0", "#D4C5D0", "#D0D6B5", "#E8C9C0",
            "#B8D0C5", "#D0C5C0", "#C8D8E0", "#E0D0C0", "#D8C8C0",
            "#C0D0D8", "#D0C8D8", "#E0D0D0", "#C8D8C0", "#D8D0C0",
            "#C0C8D0", "#D0C0C8", "#E0C8C0", "#C0D0C0", "#D0D8D8",
        ]
        return [morandi[i % len(morandi)] for i in range(n)]
    else:
        pal = sns.color_palette("tab20", n)

    return [f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for r, g, b in pal]


def plot_sankey(df, output_file, title, top_model=15, top_modality=12, top_disease=12,
                palette_type="custom"):
    """Generate a 3-layer Sankey diagram (Model → Modality → Disease) as HTML."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        log("plotly not installed, skipping Sankey diagram", "WARN")
        return

    def get_items(row, prefix):
        cols = [c for c in row.index if c.startswith(prefix) and row[c] == 1]
        return [c.replace(prefix, "") for c in cols]

    # Count frequencies & select Top N
    model_counts = df[[c for c in df.columns if c.startswith("model_")]].sum()
    modality_counts = df[[c for c in df.columns if c.startswith("modality_")]].sum()
    disease_counts = df[[c for c in df.columns if c.startswith("disease_")]].sum()

    top_models = set(model_counts.sort_values(ascending=False).head(top_model).index.str.replace("model_", ""))
    top_modalities = set(modality_counts.sort_values(ascending=False).head(top_modality).index.str.replace("modality_", ""))
    top_diseases = set(disease_counts.sort_values(ascending=False).head(top_disease).index.str.replace("disease_", ""))

    # Build links
    pairs_mm = {}   # model → modality
    pairs_md = {}   # modality → disease

    for _, row in df.iterrows():
        models = [m for m in get_items(row, "model_") if m in top_models]
        modalities = [m for m in get_items(row, "modality_") if m in top_modalities]
        diseases = [d for d in get_items(row, "disease_") if d in top_diseases]
        for m in models:
            for mod in modalities:
                pairs_mm[(m, mod)] = pairs_mm.get((m, mod), 0) + 1
        for mod in modalities:
            for d in diseases:
                pairs_md[(mod, d)] = pairs_md.get((mod, d), 0) + 1

    labels = list(top_models) + list(top_modalities) + list(top_diseases)
    idx_map = {label: i for i, label in enumerate(labels)}

    sources, targets, values = [], [], []
    for (m, mod), cnt in pairs_mm.items():
        if cnt > 0:
            sources.append(idx_map[m])
            targets.append(idx_map[mod])
            values.append(cnt)
    for (mod, d), cnt in pairs_md.items():
        if cnt > 0:
            sources.append(idx_map[mod])
            targets.append(idx_map[d])
            values.append(cnt)

    if not values:
        log(f"No valid co-occurrence links, skipping Sankey: {output_file}", "WARN")
        return

    node_colors = _get_sankey_palette(len(labels), palette_type)

    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="rgba(0,0,0,0.15)", width=0.5),
                  label=labels, color=node_colors),
        link=dict(source=sources, target=targets, value=values),
    )])
    fig.update_layout(title_text=title, font_size=12)
    fig.write_html(output_file)
    log(f"Sankey diagram saved: {output_file}")


# ==================== Report Generation ====================

def generate_reports(df, output_prefix, title_suffix="", mode="count"):
    """Generate trend PDFs (stacked area + heatmaps)."""
    is_prop = (mode == "proportion")
    stream_norm = is_prop
    hm_norms = {
        "model": is_prop,
        "modality": is_prop,
        "disease": is_prop,
    }
    mode_label = "prop" if is_prop else "count"

    palette_map = {"modality_": "Set2", "disease_": "Set3", "model_": "tab20"}

    # ---- Trend Plots PDF ----
    stream_pdf = f"{output_prefix}_{mode_label}_streams.pdf"
    with PdfPages(stream_pdf) as pdf:
        for prefix, title_base in [
            ("modality_", "Data Modality Trends"),
            ("disease_", "Disease/Tissue Trends"),
            ("model_", "Top 15 Model/Algorithm Trends"),
        ]:
            top = config.STREAM_TOP_N.get(prefix.rstrip("_"), 15)
            fig = plot_stream(
                df, prefix, f"{title_base} {title_suffix}",
                top_n=top, normalize=stream_norm,
                palette=palette_map.get(prefix, "tab20"),
            )
            if fig:
                pdf.savefig(fig)
                plt.close(fig)

        # Summary page
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axis("off")
        years = sorted(df["year"].unique())
        text = f"Total papers: {len(df)}\nYear range: {min(years)} – {max(years)}\nMode: {mode}"
        ax.text(0.1, 0.5, text, fontsize=12, va="center")
        pdf.savefig(fig)
        plt.close(fig)

    log(f"Generated: {stream_pdf}")

    # ---- Heatmaps PDF ----
    heatmap_pdf = f"{output_prefix}_{mode_label}_heatmap.pdf"
    with PdfPages(heatmap_pdf) as pdf:
        plot_hierarchical_heatmap(
            df, pdf,
            top_n_model=config.HEATMAP_TOP_N["model"],
            top_n_modality=config.HEATMAP_TOP_N["modality"],
            top_n_disease=config.HEATMAP_TOP_N["disease"],
            normalize_model=hm_norms["model"],
            normalize_modality=hm_norms["modality"],
            normalize_disease=hm_norms["disease"],
            vmax_prop=0.6,
        )
    log(f"Generated: {heatmap_pdf}")


# ==================== Main Entry Point ====================

def run_analysis(input_path=None):
    """
    Execute the full analysis pipeline:
      1. Parse normalized WOS file
      2. Extract high-frequency candidates → Expand model dictionary
      3. Construct DataFrame
      4. Generate trend plots / heatmaps / Sankey diagrams
    """
    input_path = input_path or config.NORMALIZED_FILE

    if not os.path.exists(input_path):
        log(f"File not found: {input_path}", "ERROR")
        return

    # 1. Parse
    log("Step 1: Parsing WoS file")
    records = parse_wos_file(input_path)
    log(f"  Parsed {len(records)} literature records")

    # 2. Candidate terms
    log("Step 2: Auto-extracting high-frequency candidate keywords")
    texts = build_corpus(records)
    candidates = extract_candidates(texts)
    print_candidates(candidates)

    df_candidates = pd.DataFrame(candidates, columns=["phrase", "count"])
    df_candidates["is_likely_model"] = df_candidates["phrase"].apply(is_likely_model_name)
    df_candidates.to_csv(config.CANDIDATES_CSV, index=False, encoding="utf-8-sig")
    log(f"Candidate list exported → {config.CANDIDATES_CSV}")

    # 3. Expand model dictionary
    log("Step 3: Auto-expanding model list")
    model_keywords, added = expand_model_keywords(candidates, BASE_MODEL_KEYWORDS)
    for phrase, key in added:
        log(f"  Added model: {phrase} → {key}")
    log(f"  Added {len(added)} new models, current total: {len(model_keywords)}")

    # 4. Build DataFrame
    df = records_to_dataframe(records, model_keywords)
    if df.empty:
        log("No valid data", "ERROR")
        return

    yearly = df.groupby("year").sum()
    model_cols = [c for c in yearly.columns if c.startswith("model_")]
    top15 = yearly[model_cols].sum().sort_values(ascending=False).head(15).index.tolist()
    log(f"Top 15 models: {[c.replace('model_', '') for c in top15]}")

    # 5. Generate reports
    log("Step 4: Generating reports (Full range 1996–2026)")
    generate_reports(df, os.path.join(config.OUTPUT_DIR, "trends_full"),
                     title_suffix="(1996–2026)", mode="count")
    generate_reports(df, os.path.join(config.OUTPUT_DIR, "trends_full"),
                     title_suffix="(1996–2026)", mode="proportion")

    df_2010 = df[(df["year"] >= 2010) & (df["year"] <= 2025)].copy()
    if not df_2010.empty:
        log("Step 4b: Generating reports (2010–2025)")
        generate_reports(df_2010, os.path.join(config.OUTPUT_DIR, "trends_2010"),
                         title_suffix="(2010–2025)", mode="count")
        generate_reports(df_2010, os.path.join(config.OUTPUT_DIR, "trends_2010"),
                         title_suffix="(2010–2025)", mode="proportion")

    # 6. Sankey diagrams
    log("Step 5: Generating Sankey diagrams")
    try:
        import plotly  # noqa
        plot_sankey(
            df,
            os.path.join(config.OUTPUT_DIR, "sankey_full_1996_2026.html"),
            "Sankey Diagram: Model → Modality → Disease (1996–2026)",
            **config.SANKEY_TOP_N, palette_type=config.SANKEY_PALETTE,
        )
        if not df_2010.empty:
            plot_sankey(
                df_2010,
                os.path.join(config.OUTPUT_DIR, "sankey_2010_2025.html"),
                "Sankey Diagram: Model → Modality → Disease (2010–2025)",
                **config.SANKEY_TOP_N, palette_type=config.SANKEY_PALETTE,
            )
    except ImportError:
        log("plotly not installed, skipping Sankey diagram", "WARN")


if __name__ == "__main__":
    run_analysis()