# -*- coding: utf-8 -*-
"""
Keyword Normalization Module: Standardizes terminology in DE/ID fields.
Rules are centralized in a lookup table for easy maintenance and scalability.
"""

import re

import config
from .utils import read_blocks, write_blocks, log


# ==================== Normalization Rule Table ====================
# Format: (regex_pattern, replacement_text)
# Applied sequentially from top to bottom.
# Place longer phrases before abbreviations to prevent false matches.

NORMALIZE_RULES = [
    (r"\bConvolutional Neural Network\b", "CNN"),
    (r"\bConvolutional Neural Networks\b", "CNN"),
    (r"\bConvNet\b", "CNN"),
    (r"\bDeep Neural Network\b", "DNN"),
    (r"\bDeep Neural Networks\b", "DNN"),
    (r"\bRecurrent Neural Network\b", "RNN"),
    (r"\bRecurrent Neural Networks\b", "RNN"),
    (r"\bLong Short-Term Memory\b", "LSTM"),
    (r"\bLong Short Term Memory\b", "LSTM"),
    (r"\bSupport Vector Machine\b", "SVM"),
    (r"\bSupport Vector Machines\b", "SVM"),
    (r"\bGenerative Adversarial Network\b", "GAN"),
    (r"\bGenerative Adversarial Networks\b", "GAN"),
    (r"\bResidual Network\b", "ResNet"),
    (r"\bResidual Networks\b", "ResNet"),
    (r"\bRandom Forest\b", "RF"),
    (r"\bRandom Forests\b", "RF"),
    (r"\bArtificial Neural Network\b", "ANN"),
    (r"\bArtificial Neural Networks\b", "ANN"),
    (r"\bArtificial Intelligence(ai)\b", "Artificial Intelligence"),
    (r"\bArtificial-Intelligence\b", "Artificial Intelligence"),
    (r"\bDiabetic Retinopathy\b", "Diabetic Retinopathy"),
    (r"\bDiabetic-Retinopathy\b", "Diabetic Retinopathy"),
    (r"\bDR\b", "Diabetic Retinopathy"),
    (r"\bDiabetic Macular Edema\b", "Diabetic Macular Edema"),
    (r"\bDME\b", "Diabetic Macular Edema"),
    (r"\bNon-Proliferative Diabetic Retinopathy\b", "NPDR"),
    (r"\bNonproliferative Diabetic Retinopathy\b", "NPDR"),
    (r"\bProliferative Diabetic Retinopathy\b", "PDR"),
    (r"\bDiabetes Mellitus\b", "Diabetes Mellitus"),
    (r"\bDiabetes\b", "Diabetes Mellitus"),
    (r"\bImage Processing\b", "Image Processing"),
    (r"\bImage Analysis\b", "Image Processing"),
    (r"\bMachine Learning\b", "Machine Learning"),
    (r"\bDeep Learning\b", "Deep Learning"),
    (r"\bTransfer Learning\b", "Transfer Learning"),
    (r"\bDimensionality Reduction\b", "Dimensionality Reduction"),
]


# ==================== Core Logic ====================

def normalize_text(text):
    """Apply all normalization rules to a single keyword string."""
    if not text:
        return text

    # Split by semicolons or commas
    terms = re.split(r"[;,]\s*", text)
    normalized_terms = []

    for term in terms:
        term = term.strip()
        if not term:
            continue

        original = term
        for pattern, replacement in NORMALIZE_RULES:
            term = re.sub(pattern, replacement, term, flags=re.IGNORECASE)

        # Keep original if normalization resulted in empty string
        normalized_terms.append(term.strip() if term.strip() else original)

    return "; ".join(normalized_terms)


def process_block(block):
    lines = block.split("\n")
    new_lines = []

    for line in lines:
        if line.startswith("DE ") or line.startswith("ID "):
            tag = line[:2]
            content = line[3:]
            normalized = normalize_text(content)
            new_lines.append(f"{tag} {normalized}")
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def normalize_file(input_path=None, output_path=None):
    input_path = input_path or config.DEDUP_FILE
    output_path = output_path or config.NORMALIZED_FILE

    blocks = read_blocks(input_path)
    log(f"Parsed {len(blocks)} records, starting normalization...")

    processed = [process_block(b) for b in blocks]

    write_blocks(processed, output_path)
    log(f"Normalization complete → {output_path} ({len(processed)} records)")
    return len(processed)


if __name__ == "__main__":
    normalize_file()