"""Script to populate seed GSE file from example queries."""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from bs4 import BeautifulSoup

# GEO search URL
GEO_BASE_URL = "https://www.ncbi.nlm.nih.gov/geo"


def search_geo_by_query(query: str, max_results: int = 15) -> list[str]:
    """
    Search GEO for datasets matching a query using NCBI E-utilities.
    
    Args:
        query: Search query string (e.g., "human liver rna-seq")
        max_results: Maximum number of GSE IDs to return
        
    Returns:
        List of GSE IDs (e.g., ["GSE123456", "GSE789012"])
    """
    # Use NCBI E-utilities for more reliable search
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "gds",  # Gene Expression Omnibus database
        "term": f"{query} AND GSE[Entry Type]",  # Search for GSE entries
        "retmax": max_results,
        "retmode": "json",
    }
    
    try:
        response = requests.get(esearch_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract IDs from response
        id_list = data.get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return []
        
        # Convert IDs to GSE format
        # E-utilities returns numeric IDs, we need to fetch to get GSE IDs
        # Actually, for GDS database, IDs are already accession numbers
        # Let's fetch details to get GSE IDs
        
        # Use EFetch to get accession numbers (use text mode for simpler parsing)
        import re
        efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        efetch_params = {
            "db": "gds",
            "id": ",".join(id_list[:max_results]),  # Limit to max_results
            "retmode": "text",
        }
        
        fetch_response = requests.get(efetch_url, params=efetch_params, timeout=30)
        fetch_response.raise_for_status()
        
        # Extract GSE IDs from text format (looks like "Accession: GSE123456")
        text = fetch_response.text
        gse_ids = re.findall(r"Accession:\s*(GSE\d+)", text)
        
        # Remove duplicates and limit
        unique_gse_ids = []
        seen = set()
        for gse_id in gse_ids:
            if gse_id not in seen:
                seen.add(gse_id)
                unique_gse_ids.append(gse_id)
                if len(unique_gse_ids) >= max_results:
                    break
        
        return unique_gse_ids
        
    except Exception as e:
        print(f"Error searching GEO for '{query}': {e}")
        # Return empty list on error
        return []


def populate_seed_file_from_queries(
    queries: list[str],
    output_file: str = None,
    max_per_query: int = 15
) -> list[str]:
    """
    Populate seed file with GSE IDs from example queries.
    
    Args:
        queries: List of search query strings
        output_file: Path to output file (default: data/seed_gse.txt)
        max_per_query: Maximum GSE IDs per query
        
    Returns:
        List of all GSE IDs found
    """
    if output_file is None:
        output_file = project_root / "data" / "seed_gse.txt"
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_gse_ids = []
    seen = set()
    
    print(f"Searching GEO for {len(queries)} queries...")
    print("=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Searching: '{query}'")
        gse_ids = search_geo_by_query(query, max_results=max_per_query)
        
        new_count = 0
        for gse_id in gse_ids:
            if gse_id not in seen:
                seen.add(gse_id)
                all_gse_ids.append(gse_id)
                new_count += 1
                print(f"  ✓ Found: {gse_id}")
        
        print(f"  Found {new_count} new IDs (total so far: {len(seen)})")
        
        # Small delay to be respectful to GEO servers
        if i < len(queries):
            time.sleep(1)
    
    # Write to file
    with open(output_path, "w") as f:
        for gse_id in sorted(all_gse_ids):
            f.write(f"{gse_id}\n")
    
    print("\n" + "=" * 60)
    print(f"✓ Wrote {len(all_gse_ids)} unique GSE IDs to {output_path}")
    
    return all_gse_ids


if __name__ == "__main__":
    # Example queries from README
    example_queries = [
        "human liver rna-seq",
        "mouse brain single cell",
        "influenza vaccine",
        "NAFLD non-alcoholic fatty liver disease"
    ]
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        queries = sys.argv[1:]
    else:
        queries = example_queries
    
    # Populate seed file
    gse_ids = populate_seed_file_from_queries(
        queries=queries,
        max_per_query=15  # Get ~15 datasets per query
    )
    
    print(f"\nTotal unique GSE IDs: {len(gse_ids)}")

