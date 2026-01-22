"""Ontology normalization using OLS with optional LLM fallback."""

from typing import Literal, Optional, Tuple

from normalize.llm_client import generate_alternative_names
from normalize.ols_client import extract_best_match, search_mondo, search_uberon


def normalize_tissue(
    text: str, use_llm: bool = False
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Normalize tissue text to UBERON CURIE.

    Pipeline:
    1. Try OLS lookup (UBERON)
    2. If fails and use_llm=True, generate alternatives with LLM and retry OLS

    Args:
        text: Raw tissue text to normalize
        use_llm: Whether to use LLM fallback if OLS lookup fails

    Returns:
        Tuple of (normalized_label, curie, source)
        - normalized_label: Normalized tissue label
        - curie: UBERON CURIE (e.g., "UBERON:0002107")
        - source: "ols" or "llm" or None
    """
    if not text or not text.strip():
        return (None, None, None)

    # Clean text
    text = text.strip()

    # Step 1: Try OLS lookup
    response = search_uberon(text, exact=True)
    match = extract_best_match(response)

    if match:
        label, curie = match
        return (label, curie, "ols")

    # Try with exact=False for fuzzy matching
    response = search_uberon(text, exact=False)
    match = extract_best_match(response)

    if match:
        label, curie = match
        return (label, curie, "ols")

    # Step 2: If OLS failed and LLM is enabled, try LLM fallback
    if use_llm:
        alternatives = generate_alternative_names(text, entity_type="tissue")
        for alt in alternatives:
            response = search_uberon(alt, exact=True)
            match = extract_best_match(response)
            if match:
                label, curie = match
                return (label, curie, "llm")

            # Try fuzzy match for alternative
            response = search_uberon(alt, exact=False)
            match = extract_best_match(response)
            if match:
                label, curie = match
                return (label, curie, "llm")

    return (None, None, None)


def normalize_disease(
    text: str, use_llm: bool = False
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Normalize disease text to MONDO CURIE.

    Pipeline:
    1. Try OLS lookup (MONDO)
    2. If fails and use_llm=True, generate alternatives with LLM and retry OLS

    Args:
        text: Raw disease text to normalize
        use_llm: Whether to use LLM fallback if OLS lookup fails

    Returns:
        Tuple of (normalized_label, curie, source)
        - normalized_label: Normalized disease label
        - curie: MONDO CURIE (e.g., "MONDO:0005015")
        - source: "ols" or "llm" or None
    """
    if not text or not text.strip():
        return (None, None, None)

    # Clean text
    text = text.strip()

    # Step 1: Try OLS lookup
    response = search_mondo(text, exact=True)
    match = extract_best_match(response)

    if match:
        label, curie = match
        return (label, curie, "ols")

    # Try with exact=False for fuzzy matching
    response = search_mondo(text, exact=False)
    match = extract_best_match(response)

    if match:
        label, curie = match
        return (label, curie, "ols")

    # Step 2: If OLS failed and LLM is enabled, try LLM fallback
    if use_llm:
        alternatives = generate_alternative_names(text, entity_type="disease")
        for alt in alternatives:
            response = search_mondo(alt, exact=True)
            match = extract_best_match(response)
            if match:
                label, curie = match
                return (label, curie, "llm")

            # Try fuzzy match for alternative
            response = search_mondo(alt, exact=False)
            match = extract_best_match(response)
            if match:
                label, curie = match
                return (label, curie, "llm")

    return (None, None, None)

