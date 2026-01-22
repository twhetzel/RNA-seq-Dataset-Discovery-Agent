"""OLS (Ontology Lookup Service) client for ontology lookups."""

import urllib.parse
from typing import Optional

import requests

OLS_BASE_URL = "https://www.ebi.ac.uk/ols4/api"


def search_ols(
    ontology_id: str, query: str, exact: bool = True, size: int = 10
) -> Optional[dict]:
    """
    Query OLS API for ontology terms.

    Args:
        ontology_id: Ontology ID (e.g., 'uberon', 'mondo')
        query: Search query string
        exact: Whether to use exact matching
        size: Maximum number of results to return

    Returns:
        API response dictionary or None if request fails
    """
    url = f"{OLS_BASE_URL}/search"
    params = {
        "q": query,
        "ontology": ontology_id,
        "exact": str(exact).lower(),
        "size": size,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as e:
        print(f"OLS search error for '{query}' in {ontology_id}: {e}")
        return None


def get_term_by_iri(ontology_id: str, iri: str) -> Optional[dict]:
    """
    Get term details by IRI.

    Args:
        ontology_id: Ontology ID (e.g., 'uberon', 'mondo')
        iri: Term IRI

    Returns:
        Term details dictionary or None if request fails
    """
    # URL encode the IRI
    encoded_iri = urllib.parse.quote(iri, safe="")
    url = f"{OLS_BASE_URL}/ontologies/{ontology_id}/terms/{encoded_iri}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as e:
        print(f"OLS get_term error for IRI '{iri}' in {ontology_id}: {e}")
        return None


def search_uberon(query: str, exact: bool = True) -> Optional[dict]:
    """
    Search UBERON ontology for tissues.

    Args:
        query: Search query string
        exact: Whether to use exact matching

    Returns:
        API response dictionary or None if request fails
    """
    return search_ols("uberon", query, exact=exact)


def search_mondo(query: str, exact: bool = True) -> Optional[dict]:
    """
    Search MONDO ontology for diseases.

    Args:
        query: Search query string
        exact: Whether to use exact matching

    Returns:
        API response dictionary or None if request fails
    """
    return search_ols("mondo", query, exact=exact)


def extract_best_match(response: Optional[dict]) -> Optional[tuple[str, str]]:
    """
    Extract the best matching term from OLS response.

    Args:
        response: OLS API response dictionary

    Returns:
        Tuple of (label, curie) or None if no match found
    """
    if not response or "response" not in response:
        return None

    docs = response.get("response", {}).get("docs", [])
    if not docs:
        return None

    # Get the first (best) match
    best_match = docs[0]

    # Extract IRI (CURIE format)
    iri = best_match.get("iri", "")
    if not iri:
        return None

    # Convert IRI to CURIE if possible
    # OLS returns IRIs like http://purl.obolibrary.org/obo/UBERON_0002107
    # We want CURIE format like UBERON:0002107
    curie = None
    if "UBERON_" in iri:
        uberon_id = iri.split("UBERON_")[-1].split("/")[0]
        curie = f"UBERON:{uberon_id}"
    elif "MONDO_" in iri:
        mondo_id = iri.split("MONDO_")[-1].split("/")[0]
        curie = f"MONDO:{mondo_id}"

    label = best_match.get("label", [])
    if isinstance(label, list) and label:
        label = label[0]
    elif not isinstance(label, str):
        label = ""

    if curie and label:
        return (label, curie)

    return None

