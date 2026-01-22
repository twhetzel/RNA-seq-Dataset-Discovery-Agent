"""Scoring functions for dataset ranking."""

from typing import Literal

from model.schema import Dataset


def compute_relevance_score(dataset: Dataset, query: str) -> float:
    """
    Compute relevance score based on keyword overlap.

    Args:
        dataset: Dataset to score
        query: User query string

    Returns:
        Relevance score (0-1)
    """
    if not query or not query.strip():
        return 0.0

    query_lower = query.lower().split()
    text_parts = []

    # Collect text fields
    if dataset.title:
        text_parts.append(dataset.title.lower())
    if dataset.summary:
        text_parts.append(dataset.summary.lower())
    if dataset.tissue_raw:
        text_parts.append(dataset.tissue_raw.lower())
    if dataset.disease_raw:
        text_parts.append(dataset.disease_raw.lower())
    if dataset.organism:
        text_parts.append(dataset.organism.lower())

    full_text = " ".join(text_parts)

    # Count keyword matches
    matches = 0
    for keyword in query_lower:
        if keyword in full_text:
            matches += 1

    # Base score from keyword overlap
    base_score = matches / len(query_lower) if query_lower else 0.0

    # Boost for normalized tissue/disease matches
    boost = 0.0
    query_lower_str = query.lower()

    if dataset.tissue_curie and any(
        keyword in query_lower_str for keyword in ["tissue", "organ", dataset.tissue_raw.lower()] if dataset.tissue_raw
    ):
        boost += 0.2

    if dataset.disease_curie and any(
        keyword in query_lower_str
        for keyword in ["disease", "condition", dataset.disease_raw.lower()] if dataset.disease_raw
    ):
        boost += 0.2

    # Boost for organism/assay match
    if dataset.organism:
        organism_keywords = ["human", "mouse", "rat", "homo sapiens", "mus musculus", "homo", "mus ", "rattus"]
        organism_lower = dataset.organism.lower()
        # Check if any query keyword matches organism (common or scientific name)
        for keyword in query_lower:
            # Direct match
            if keyword in organism_lower:
                boost += 0.15
                break
            # Common name mappings
            mappings = {"human": "homo", "mouse": "mus ", "rat": "rattus"}
            if keyword in mappings and mappings[keyword] in organism_lower:
                boost += 0.15
                break

    if dataset.assay_type != "unknown":
        assay_keywords = ["bulk", "scrna", "single cell", "sc-rna", "rna-seq"]
        if any(keyword in query_lower_str and dataset.assay_type.lower() in keyword for keyword in assay_keywords):
            boost += 0.15

    # Combine base score and boost (capped at 1.0)
    score = min(1.0, base_score + boost)

    return score


def compute_reuse_score(dataset: Dataset) -> float:
    """
    Compute reuse readiness score.

    Args:
        dataset: Dataset to score

    Returns:
        Reuse score (0-1)
    """
    if dataset.assay_type == "scRNA":
        # For scRNA, prioritize by donors
        if dataset.donors is not None:
            if dataset.donors >= 6:
                return 1.0
            elif dataset.donors >= 3:
                return 0.6
            else:
                return 0.2
        else:
            # Unknown donors - weak proxy using total samples
            if dataset.samples_total:
                if dataset.samples_total >= 20:
                    return 0.3
                elif dataset.samples_total >= 10:
                    return 0.2
                else:
                    return 0.1
            return 0.1
    else:
        # For bulk RNA-seq, prioritize by samples per condition
        if dataset.conditions and len(dataset.conditions) > 0:
            min_per_condition = min(dataset.conditions.values())
            if min_per_condition >= 10:
                return 1.0
            elif min_per_condition >= 6:
                return 0.7
            elif min_per_condition >= 3:
                return 0.4
            else:
                return 0.1
        else:
            # Unknown conditions - use total samples heuristic
            if dataset.samples_total:
                if dataset.samples_total >= 20:
                    return 0.7
                elif dataset.samples_total >= 10:
                    return 0.4
                else:
                    return 0.1
            return 0.1


def compute_completeness_score(dataset: Dataset) -> float:
    """
    Compute metadata completeness score.

    Args:
        dataset: Dataset to score

    Returns:
        Completeness score (0-1)
    """
    # Key fields
    key_fields = [
        dataset.organism,
        dataset.assay_type != "unknown",
        dataset.tissue_raw,
        dataset.disease_raw,
        dataset.samples_total is not None,
    ]

    # Count present fields
    present = sum(1 for field in key_fields if field)

    # Base completeness
    base_score = present / len(key_fields)

    # Bonus for normalized CURIEs
    bonus = 0.0
    if dataset.tissue_curie:
        bonus += 0.1
    if dataset.disease_curie:
        bonus += 0.1

    # Cap at 1.0
    score = min(1.0, base_score + bonus)

    return score


def compute_final_score(
    relevance: float, reuse: float, completeness: float
) -> float:
    """
    Compute final weighted score.

    Args:
        relevance: Relevance score (0-1)
        reuse: Reuse score (0-1)
        completeness: Completeness score (0-1)

    Returns:
        Final weighted score (0-1)
    """
    # Weighted combination
    final = 0.55 * relevance + 0.30 * reuse + 0.15 * completeness

    return min(1.0, max(0.0, final))


def get_reuse_badge(reuse_score: float) -> Literal["High", "Medium", "Low", "Unknown"]:
    """
    Get reuse badge from reuse score.

    Args:
        reuse_score: Reuse score (0-1)

    Returns:
        Reuse badge
    """
    if reuse_score >= 0.7:
        return "High"
    elif reuse_score >= 0.4:
        return "Medium"
    elif reuse_score > 0.0:
        return "Low"
    else:
        return "Unknown"


def generate_explanations(dataset: Dataset, query: str) -> list[str]:
    """
    Generate explanation bullets for a dataset.

    Args:
        dataset: Dataset to explain
        query: User query

    Returns:
        List of explanation strings
    """
    explanations = []

    # Tissue match
    if dataset.tissue_curie:
        source = dataset.tissue_normalization_source or "ols"
        explanations.append(
            f"Tissue match: {dataset.tissue_raw} ({dataset.tissue_curie}, via {source.upper()})"
            if dataset.tissue_raw
            else f"Tissue match: {dataset.tissue_curie} (via {source.upper()})"
        )

    # Disease match
    if dataset.disease_curie:
        source = dataset.disease_normalization_source or "ols"
        explanations.append(
            f"Disease match: {dataset.disease_raw} ({dataset.disease_curie}, via {source.upper()})"
            if dataset.disease_raw
            else f"Disease match: {dataset.disease_curie} (via {source.upper()})"
        )

    # Reuse rationale
    if dataset.assay_type == "scRNA":
        if dataset.donors is not None:
            explanations.append(
                f"Reuse readiness: {dataset.assay_type} RNA-seq, {dataset.donors} donors ({dataset.reuse_badge})"
            )
        else:
            explanations.append(
                f"Reuse readiness: {dataset.assay_type} RNA-seq, {dataset.samples_total} samples ({dataset.reuse_badge}, donors unknown)"
            )
    else:
        if dataset.conditions and len(dataset.conditions) > 0:
            min_per_group = min(dataset.conditions.values())
            groups = ", ".join([f"{k}: {v}" for k, v in dataset.conditions.items()])
            explanations.append(
                f"Reuse readiness: {dataset.assay_type} RNA-seq, {min_per_group} samples/group ({groups}) ({dataset.reuse_badge})"
            )
        else:
            explanations.append(
                f"Reuse readiness: {dataset.assay_type} RNA-seq, {dataset.samples_total} samples ({dataset.reuse_badge}, conditions unknown)"
            )

    # Missing metadata warnings
    missing = []
    if not dataset.organism:
        missing.append("organism")
    if dataset.assay_type == "unknown":
        missing.append("assay_type")
    if not dataset.tissue_raw and not dataset.tissue_curie:
        missing.append("tissue")
    if not dataset.disease_raw and not dataset.disease_curie:
        missing.append("disease")
    if dataset.samples_total is None:
        missing.append("sample_count")

    if missing:
        explanations.append(f"Missing metadata: {', '.join(missing)}")

    return explanations

