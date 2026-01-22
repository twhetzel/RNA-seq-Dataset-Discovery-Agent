"""LLM client for generating alternative names when OLS lookup fails."""

import os
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def generate_alternative_names(term: str, entity_type: str = "entity") -> list[str]:
    """
    Generate alternative names/synonyms using OpenAI API.

    Args:
        term: The term to generate alternatives for
        entity_type: Type of entity ('tissue', 'disease', or generic 'entity')

    Returns:
        List of alternative names/synonyms, or empty list if API key not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return []

    client = OpenAI(api_key=api_key)

    # Build prompt based on entity type
    if entity_type == "tissue":
        prompt = f"""Generate 3-5 alternative names, synonyms, or common variations for the biomedical tissue/anatomical term: "{term}"

Examples:
- "liver" -> ["hepatic tissue", "hepatocyte", "liver tissue"]
- "brain" -> ["neural tissue", "brain tissue", "cerebral tissue"]

Return only the alternative names, one per line, without numbering or bullets."""
    elif entity_type == "disease":
        prompt = f"""Generate 3-5 alternative names, synonyms, or common variations for the biomedical disease/condition term: "{term}"

Examples:
- "NAFLD" -> ["non-alcoholic fatty liver disease", "non alcoholic fatty liver disease", "fatty liver disease"]
- "diabetes" -> ["diabetes mellitus", "DM", "diabetic condition"]

Return only the alternative names, one per line, without numbering or bullets."""
    else:
        prompt = f"""Generate 3-5 alternative names, synonyms, or common variations for the biomedical term: "{term}"

Return only the alternative names, one per line, without numbering or bullets."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-efficient model
            messages=[
                {
                    "role": "system",
                    "content": "You are a biomedical terminology expert. Generate concise alternative names and synonyms.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=100,
        )

        content = response.choices[0].message.content.strip()
        # Parse line-separated alternatives
        alternatives = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.strip().startswith(("-", "*", "•"))
        ]

        # Filter out the original term
        alternatives = [alt for alt in alternatives if alt.lower() != term.lower()]

        return alternatives[:5]  # Return up to 5 alternatives

    except Exception as e:
        print(f"OpenAI API error generating alternatives for '{term}': {e}")
        return []

