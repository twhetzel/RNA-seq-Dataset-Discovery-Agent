"""GEO client for fetching and parsing GEO dataset metadata."""

import json
import re
from pathlib import Path
from typing import Optional

import requests

from model.schema import Dataset


GEO_BASE_URL = "https://www.ncbi.nlm.nih.gov/geo"
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "datasets.json"


def ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_cached_datasets() -> dict[str, dict]:
    """
    Load cached datasets from JSON file.

    Returns:
        Dictionary mapping GSE ID to dataset data
    """
    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading cache: {e}")
        return {}


def save_cached_datasets(datasets: dict[str, dict]):
    """
    Save datasets to cache JSON file.

    Args:
        datasets: Dictionary mapping GSE ID to dataset data
    """
    ensure_cache_dir()
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(datasets, f, indent=2)
    except IOError as e:
        print(f"Error saving cache: {e}")


def fetch_gse_soft(gse_id: str) -> Optional[str]:
    """
    Fetch GSE dataset in SOFT format.

    Args:
        gse_id: GEO Series ID (e.g., "GSE123456")

    Returns:
        SOFT format text or None if fetch fails
    """
    url = f"{GEO_BASE_URL}/query/acc.cgi"
    params = {"acc": gse_id, "targ": "self", "form": "text", "view": "full"}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {gse_id}: {e}")
        return None


def parse_soft(soft_text: str, gse_id: str) -> Optional[dict]:
    """
    Parse SOFT format to extract dataset metadata.

    Args:
        soft_text: SOFT format text
        gse_id: GEO Series ID

    Returns:
        Dictionary with dataset metadata or None if parsing fails
    """
    try:
        lines = soft_text.split("\n")
        data: dict[str, any] = {
            "dataset_id": gse_id,
            "title": "",
            "summary": None,
            "organism": None,
            "platform": None,
            "samples_total": 0,
            "characteristics_raw": "",
        }

        in_series = False
        sample_count = 0
        organisms = []
        characteristics = []
        seen_samples = set()  # Track unique sample IDs

        for line in lines:
            line = line.strip()

            if line.startswith("^SERIES"):
                in_series = True
                continue

            if line.startswith("^SAMPLE"):
                sample_count += 1
                in_series = False
                # Extract sample ID if present
                if "=" in line:
                    sample_id = line.split("=", 1)[1].strip()
                    if sample_id and sample_id not in seen_samples:
                        seen_samples.add(sample_id)
                continue

            if line.startswith("^"):
                in_series = False
                continue

            if in_series:
                if line.startswith("!Series_title"):
                    data["title"] = line.split("=", 1)[1].strip()
                elif line.startswith("!Series_summary"):
                    summary = line.split("=", 1)[1].strip()
                    if data["summary"]:
                        data["summary"] += " " + summary
                    else:
                        data["summary"] = summary
                elif line.startswith("!Series_platform_id"):
                    platform = line.split("=", 1)[1].strip()
                    data["platform"] = platform
                # Count samples from !Series_sample_id fields
                elif line.startswith("!Series_sample_id"):
                    sample_count += 1
                    if "=" in line:
                        sample_id = line.split("=", 1)[1].strip()
                        if sample_id and sample_id not in seen_samples:
                            seen_samples.add(sample_id)
                # Extract organism from Series metadata
                elif line.startswith("!Series_platform_organism") or \
                     line.startswith("!Series_sample_organism") or \
                     line.startswith("!Series_organism_ch1"):
                    if "=" in line:
                        organism = line.split("=", 1)[1].strip()
                        if organism and organism.lower() not in ["", "n/a", "na", "none", "not applicable"]:
                            organisms.append(organism)

            # Extract organism from samples (check multiple field names)
            if line.startswith("!Sample_organism_ch1") or \
               line.startswith("!Sample_organism") or \
               line.startswith("!Sample_source_name_ch1"):
                if "=" in line:
                    organism = line.split("=", 1)[1].strip()
                    if organism and organism.lower() not in ["", "n/a", "na", "none", "not applicable"]:
                        organisms.append(organism)
                        
            # Extract characteristics from samples
            if line.startswith("!Sample_characteristics_ch1"):
                if "=" in line:
                    char = line.split("=", 1)[1].strip()
                    if char:
                        characteristics.append(char)

        # Use sample IDs count if we found any, otherwise use ^SAMPLE count
        if seen_samples:
            data["samples_total"] = len(seen_samples)
        elif sample_count > 0:
            data["samples_total"] = sample_count

        # Use most common organism
        if organisms:
            # Clean up organism names and get most common
            cleaned_organisms = [org.strip() for org in organisms if org.strip()]
            if cleaned_organisms:
                data["organism"] = max(set(cleaned_organisms), key=cleaned_organisms.count)

        data["characteristics_raw"] = "\n".join(characteristics)

        # Ensure title exists
        if not data["title"]:
            data["title"] = gse_id

        return data

    except Exception as e:
        print(f"Error parsing SOFT for {gse_id}: {e}")
        return None


def fetch_and_parse_gse(
    gse_id: str, use_cache: bool = True, cache_dict: Optional[dict] = None
) -> Optional[dict]:
    """
    Fetch and parse GSE dataset, using cache if available.

    Args:
        gse_id: GEO Series ID (e.g., "GSE123456")
        use_cache: Whether to use cached data if available
        cache_dict: Optional pre-loaded cache dictionary to avoid file I/O

    Returns:
        Dictionary with dataset metadata or None if fetch/parse fails
    """
    # Check cache first
    if use_cache:
        if cache_dict is not None:
            # Use provided cache dict
            if gse_id in cache_dict:
                return cache_dict[gse_id]
        else:
            # Load cache from file
            cached = load_cached_datasets()
            if gse_id in cached:
                return cached[gse_id]

    # Fetch from GEO
    soft_text = fetch_gse_soft(gse_id)
    if not soft_text:
        return None

    # Parse
    data = parse_soft(soft_text, gse_id)
    if not data:
        return None

    # Update cache dict if provided (will be saved later)
    if use_cache and cache_dict is not None:
        cache_dict[gse_id] = data

    return data


def ingest_gse_list(gse_ids: list[str], use_cache: bool = True) -> list[dict]:
    """
    Ingest multiple GSE datasets.

    Args:
        gse_ids: List of GSE IDs
        use_cache: Whether to use cached data

    Returns:
        List of dataset dictionaries
    """
    # Load cache once at the start to avoid race conditions
    cache_dict = load_cached_datasets() if use_cache else None

    datasets = []
    for gse_id in gse_ids:
        gse_id = gse_id.strip()
        if not gse_id:
            continue

        data = fetch_and_parse_gse(gse_id, use_cache=use_cache, cache_dict=cache_dict)
        if data:
            datasets.append(data)
        else:
            print(f"Failed to ingest {gse_id}")

    # Save cache once at the end
    if use_cache and cache_dict is not None:
        save_cached_datasets(cache_dict)

    return datasets


def load_gse_list_from_file(filepath: str) -> list[str]:
    """
    Load GSE IDs from a text file (one per line).

    Args:
        filepath: Path to text file with GSE IDs

    Returns:
        List of GSE IDs
    """
    try:
        with open(filepath, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error reading file {filepath}: {e}")
        return []
