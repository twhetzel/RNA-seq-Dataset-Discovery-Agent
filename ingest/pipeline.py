"""Pipeline for processing GEO datasets."""

import os
from pathlib import Path
from typing import Optional

from ingest.extractors import (
    extract_conditions,
    extract_disease,
    extract_tissue,
    infer_assay_type,
)
from ingest.geo_client import ingest_gse_list, load_gse_list_from_file
from model.schema import Dataset
from normalize.ontology import normalize_disease, normalize_tissue


def process_dataset(
    raw_data: dict, use_llm: bool = False
) -> Dataset:
    """
    Process raw dataset data through extraction and normalization.

    Args:
        raw_data: Raw dataset dictionary from GEO
        use_llm: Whether to use LLM for normalization fallback

    Returns:
        Processed Dataset object
    """
    # Extract basic fields
    dataset = Dataset(
        dataset_id=raw_data["dataset_id"],
        title=raw_data.get("title", raw_data["dataset_id"]),
        summary=raw_data.get("summary"),
        organism=raw_data.get("organism"),
        platform=raw_data.get("platform"),
        samples_total=raw_data.get("samples_total", 0),
    )

    # Extract assay type
    characteristics = raw_data.get("characteristics_raw", "")
    dataset.assay_type = infer_assay_type(
        dataset.title, dataset.summary, characteristics
    )

    # Extract tissue
    tissue_raw = extract_tissue(dataset.title, dataset.summary, characteristics)
    if tissue_raw:
        dataset.tissue_raw = tissue_raw
        label, curie, source = normalize_tissue(tissue_raw, use_llm=use_llm)
        if curie:
            dataset.tissue_curie = curie
            dataset.tissue_normalization_source = source
            # Update tissue_raw if we got a normalized label
            if label and label != tissue_raw:
                dataset.tissue_raw = label

    # Extract disease
    disease_raw = extract_disease(dataset.title, dataset.summary, characteristics)
    if disease_raw:
        dataset.disease_raw = disease_raw
        label, curie, source = normalize_disease(disease_raw, use_llm=use_llm)
        if curie:
            dataset.disease_curie = curie
            dataset.disease_normalization_source = source
            # Update disease_raw if we got a normalized label
            if label and label != disease_raw:
                dataset.disease_raw = label

    # Extract conditions (would need sample-level data - skip for MVP)
    # dataset.conditions = extract_conditions(samples)

    return dataset


def load_and_process_datasets(
    seed_file: Optional[str] = None,
    use_cache: bool = True,
    use_llm: bool = False,
) -> list[Dataset]:
    """
    Load and process datasets from seed file.

    Args:
        seed_file: Path to seed GSE file (default: data/seed_gse.txt)
        use_cache: Whether to use cached GEO data
        use_llm: Whether to use LLM for normalization fallback

    Returns:
        List of processed Dataset objects
    """
    if seed_file is None:
        seed_file = Path(__file__).parent.parent / "data" / "seed_gse.txt"

    # Load GSE IDs
    gse_ids = load_gse_list_from_file(str(seed_file))
    if not gse_ids:
        print(f"No GSE IDs found in {seed_file}")
        return []

    # Ingest from GEO
    raw_datasets = ingest_gse_list(gse_ids, use_cache=use_cache)

    # Process each dataset
    datasets = []
    for raw_data in raw_datasets:
        try:
            dataset = process_dataset(raw_data, use_llm=use_llm)
            datasets.append(dataset)
        except Exception as e:
            print(f"Error processing {raw_data.get('dataset_id', 'unknown')}: {e}")

    return datasets

