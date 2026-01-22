"""Metadata extraction functions for GEO datasets."""

import re
from typing import Literal, Optional


def infer_assay_type(
    title: str, summary: Optional[str] = None, characteristics: Optional[str] = None
) -> Literal["bulk", "scRNA", "unknown"]:
    """
    Infer assay type from text fields.

    Args:
        title: Dataset title
        summary: Dataset summary
        characteristics: Sample characteristics

    Returns:
        "bulk", "scRNA", or "unknown"
    """
    text = " ".join([title, summary or "", characteristics or ""]).lower()

    # Check for single-cell markers first (more specific)
    scRNA_keywords = [
        "single cell",
        "single-cell",
        "scrna",
        "sc-rna",
        "10x",
        "chromium",
        "droplet",
        "smart-seq",
        "smartseq",
        "cel-seq",
        "celseq",
    ]
    for keyword in scRNA_keywords:
        if keyword in text:
            return "scRNA"

    # Check for bulk RNA-seq markers
    bulk_keywords = [
        "rna-seq",
        "rnaseq",
        "rna seq",
        "transcriptome",
        "bulk rna",
        "bulk-rna",
    ]
    for keyword in bulk_keywords:
        if keyword in text:
            return "bulk"

    return "unknown"


def extract_tissue(
    title: str, summary: Optional[str] = None, characteristics: Optional[str] = None
) -> Optional[str]:
    """
    Extract candidate tissue string from text.

    Simple keyword scanning - returns the first matching tissue keyword found.

    Args:
        title: Dataset title
        summary: Dataset summary
        characteristics: Sample characteristics

    Returns:
        Extracted tissue string or None
    """
    text = " ".join([title, summary or "", characteristics or ""])

    # Common tissue keywords (case-insensitive)
    tissue_keywords = [
        "liver",
        "brain",
        "blood",
        "lung",
        "heart",
        "kidney",
        "skin",
        "muscle",
        "pancreas",
        "spleen",
        "colon",
        "intestine",
        "stomach",
        "adipose",
        "fat",
        "bone marrow",
        "bone",
        "cartilage",
        "nerve",
        "neural",
        "cerebral",
        "cortex",
        "hepatic",
        "pulmonary",
        "cardiac",
        "renal",
        "skeletal muscle",
    ]

    # Look for tissue keywords (whole word matching preferred)
    text_lower = text.lower()
    for keyword in sorted(tissue_keywords, key=len, reverse=True):  # Longer first
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            # Extract a bit of context around the keyword
            idx = text_lower.find(keyword)
            start = max(0, idx - 20)
            end = min(len(text), idx + len(keyword) + 20)
            context = text[start:end].strip()
            # Return the keyword or a phrase containing it
            return keyword if len(keyword) > 5 else context

    return None


def extract_disease(
    title: str, summary: Optional[str] = None, characteristics: Optional[str] = None
) -> Optional[str]:
    """
    Extract candidate disease string from text.

    Simple keyword scanning - returns the first matching disease keyword found.

    Args:
        title: Dataset title
        summary: Dataset summary
        characteristics: Sample characteristics

    Returns:
        Extracted disease string or None
    """
    text = " ".join([title, summary or "", characteristics or ""])

    # Common disease keywords (case-insensitive)
    disease_keywords = [
        "cancer",
        "carcinoma",
        "tumor",
        "tumour",
        "diabetes",
        "obesity",
        "nafld",
        "nash",
        "alzheimer",
        "parkinson",
        "influenza",
        "flu",
        "covid",
        "sars-cov-2",
        "asthma",
        "copd",
        "hypertension",
        "ischemia",
        "infarction",
        "hepatitis",
        "cirrhosis",
        "fibrosis",
        "inflammation",
        "autoimmune",
        "arthritis",
        "lupus",
        "sclerosis",
    ]

    # Look for disease keywords (whole word matching preferred)
    text_lower = text.lower()
    for keyword in sorted(disease_keywords, key=len, reverse=True):  # Longer first
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            # Extract a bit of context around the keyword
            idx = text_lower.find(keyword)
            start = max(0, idx - 30)
            end = min(len(text), idx + len(keyword) + 30)
            context = text[start:end].strip()
            # Return the keyword or a phrase containing it
            return keyword if len(keyword) > 5 else context

    return None


def extract_conditions(samples: list[dict]) -> Optional[dict[str, int]]:
    """
    Extract conditions/groups and count samples per condition.

    Args:
        samples: List of sample dictionaries with characteristics

    Returns:
        Dictionary mapping condition to count, or None if no conditions found
    """
    conditions: dict[str, int] = {}
    condition_keywords = [
        "control",
        "treated",
        "treatment",
        "case",
        "disease",
        "healthy",
        "wildtype",
        "wt",
        "knockout",
        "ko",
        "mutant",
        "mut",
        "normal",
        "tumor",
        "tumour",
        "non-tumor",
        "non-tumour",
    ]

    for sample in samples:
        characteristics = sample.get("characteristics", {})
        if isinstance(characteristics, str):
            # Parse string characteristics if needed
            characteristics = {}
            for line in sample.get("characteristics_ch1", "").split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    characteristics[key.strip()] = val.strip()

        # Look for condition keywords in characteristics
        text = " ".join([str(v) for v in characteristics.values()]).lower()

        found_condition = None
        for keyword in condition_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                # Try to extract the full condition name
                for key, val in characteristics.items():
                    val_lower = str(val).lower()
                    if keyword in val_lower:
                        found_condition = str(val).strip()
                        break
                if not found_condition:
                    found_condition = keyword
                break

        if found_condition:
            conditions[found_condition] = conditions.get(found_condition, 0) + 1

    return conditions if conditions else None

