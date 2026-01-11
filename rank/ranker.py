"""Ranking pipeline for dataset discovery."""

from typing import Literal, Optional

from model.schema import Dataset
from rank.scoring import (
    compute_completeness_score,
    compute_final_score,
    compute_relevance_score,
    compute_reuse_score,
    get_reuse_badge,
)


def matches_organism_filter(organism: str, filter_term: str) -> bool:
    """
    Check if organism matches filter term (handles common vs scientific names).
    
    Args:
        organism: Organism string (e.g., "Homo sapiens", "Mus musculus")
        filter_term: Filter term (e.g., "human", "mouse", "rat")
        
    Returns:
        True if organism matches filter
    """
    if not organism:
        return False
    
    organism_lower = organism.lower()
    filter_lower = filter_term.lower()
    
    # Direct substring match
    if filter_lower in organism_lower:
        return True
    
    # Common name to scientific name mappings
    mappings = {
        "human": "homo",
        "mouse": "mus ",  # Space to avoid matching "muscle"
        "rat": "rattus",
    }
    
    if filter_lower in mappings:
        return mappings[filter_lower] in organism_lower
    
    return False


def rank_datasets(
    datasets: list[Dataset],
    query: str,
    filters: Optional[dict] = None,
    top_k: int = 20,
) -> list[Dataset]:
    """
    Rank datasets based on query and filters.

    Args:
        datasets: List of datasets to rank
        query: User query string
        filters: Optional filters (organism, assay_type, min_samples)
        top_k: Number of top results to return

    Returns:
        Sorted list of top k datasets
    """
    if filters is None:
        filters = {}

    # Apply filters
    filtered = []
    for dataset in datasets:
        # Organism filter
        if "organism" in filters and filters["organism"] != "any":
            if not matches_organism_filter(dataset.organism, filters["organism"]):
                continue

        # Assay type filter
        if "assay_type" in filters and filters["assay_type"] != "any":
            if dataset.assay_type != filters["assay_type"]:
                continue

        # Min samples filter
        if "min_samples" in filters:
            min_samples = filters["min_samples"]
            if dataset.samples_total is None or dataset.samples_total < min_samples:
                continue

        filtered.append(dataset)

    # Compute scores for each dataset
    for dataset in filtered:
        dataset.relevance_score = compute_relevance_score(dataset, query)
        dataset.reuse_score = compute_reuse_score(dataset)
        dataset.completeness_score = compute_completeness_score(dataset)
        dataset.final_score = compute_final_score(
            dataset.relevance_score, dataset.reuse_score, dataset.completeness_score
        )
        dataset.reuse_badge = get_reuse_badge(dataset.reuse_score)

    # Sort by final score (descending)
    sorted_datasets = sorted(filtered, key=lambda d: d.final_score, reverse=True)

    # Return top k
    return sorted_datasets[:top_k]

