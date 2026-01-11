# RNA-seq Dataset Discovery Agent

Hackathon MVP project for the AGI House AI4Healthcare event (10-Jan-2026).

## Overview

A web application for discovering and ranking RNA-seq datasets from GEO (Gene Expression Omnibus) based on:
- **Relevance** to natural language queries
- **Reuse readiness** (sample counts, conditions, donors)
- **Metadata completeness** with ontology normalization (UBERON for tissues, MONDO for diseases)

The system uses OLS (Ontology Lookup Service) for ontology normalization and optionally OpenAI for generating alternative names when direct lookups fail.

## Features

- **GEO Integration**: Fetches and parses dataset metadata from GEO
- **Ontology Normalization**: Normalizes tissues (UBERON) and diseases (MONDO) using OLS
- **LLM Enhancement** (optional): Uses OpenAI to generate alternative names when OLS lookups fail
- **Scoring System**: Multi-factor scoring (relevance, reuse readiness, completeness)
- **Interactive UI**: Streamlit-based interface with search, filtering, and detailed explanations

## Architecture

```
User Query → Streamlit UI → Scoring Engine → Ranked Results
                     ↓
            Dataset Cache ← GEO Ingestion
                     ↓
         Ontology Normalization (OLS + optional LLM)
```

For a detailed data flow diagram, see [docs/data_flow.md](docs/data_flow.md).

## Setup

### Prerequisites

- Python 3.10+
- Optional: OpenAI API key for LLM-enhanced normalization

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rna-seq-dataset-discovery-agent
   ```

2. **Create virtual environment and install dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```
   
   This will install all dependencies listed in `pyproject.toml` and make the project packages importable.

3. **Set up environment variables** (optional, for LLM enhancement):
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

### Data Setup

1. **Populate seed GSE list** (recommended):
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   python scripts/populate_seed.py
   ```
   
   This script searches GEO for datasets matching the example queries from the README and populates `data/seed_gse.txt` with real GSE IDs. It searches for:
   - "human liver rna-seq"
   - "mouse brain single cell"
   - "influenza vaccine"
   - "NAFLD non-alcoholic fatty liver disease"
   
   You can also run it with custom queries:
   ```bash
   python scripts/populate_seed.py "human liver" "diabetes" "cancer"
   ```
   
   **Note**: Run this script before first use, or whenever you want to update the seed list with new datasets.

2. **Manual seed list** (alternative): If you prefer, you can manually edit `data/seed_gse.txt` with your list of GEO Series IDs (one per line).

3. **Run the application**:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   streamlit run app/streamlit_app.py
   ```

## Usage

### Basic Usage

1. **Start the app**: Run `streamlit run app/streamlit_app.py`
2. **Load datasets**: Click "Load/Refresh Datasets" in the sidebar
3. **Search**: Enter a query (e.g., "human liver NAFLD bulk rna-seq")
4. **Filter**: Use sidebar filters (organism, assay type, min samples)
5. **Explore**: Click on dataset expanders to see detailed information and explanations

### Example Queries

- `human liver rna-seq`
- `mouse brain single cell`
- `influenza vaccine`
- `NAFLD non-alcoholic fatty liver disease`

### LLM Enhancement

To enable LLM-based alternative name generation:
1. Set `OPENAI_API_KEY` environment variable
2. Check "Use LLM Enhancement" in the sidebar
3. The system will use OpenAI to generate alternative names when OLS lookups fail

**Note**: OLS ontology lookup works without any API key. LLM enhancement is optional.

## Project Structure

```
.
├── app/
│   └── streamlit_app.py      # Streamlit UI
├── ingest/
│   ├── geo_client.py         # GEO data fetching and parsing
│   ├── extractors.py         # Metadata extraction
│   └── pipeline.py           # Dataset processing pipeline
├── normalize/
│   ├── ols_client.py         # OLS API client
│   ├── llm_client.py         # OpenAI client (optional)
│   └── ontology.py           # Ontology normalization
├── rank/
│   ├── scoring.py            # Scoring functions
│   └── ranker.py             # Ranking pipeline
├── model/
│   └── schema.py             # Pydantic data models
├── data/
│   ├── seed_gse.txt          # Seed GSE IDs
│   └── cache/                # Cached dataset JSON
├── scripts/
│   └── populate_seed.py      # Script to populate seed file from GEO queries
└── README.md
```

## Scoring Details

### Relevance Score (55% weight)
- Keyword overlap between query and dataset metadata
- Boosted for normalized tissue/disease matches
- Boosted for organism/assay type matches

### Reuse Score (30% weight)
- **Bulk RNA-seq**: Based on minimum samples per condition
  - ≥10 samples/group → 1.0
  - 6-9 samples/group → 0.7
  - 3-5 samples/group → 0.4
  - <3 samples/group → 0.1
- **scRNA-seq**: Based on number of donors
  - ≥6 donors → 1.0
  - 3-5 donors → 0.6
  - <3 donors → 0.2

### Completeness Score (15% weight)
- Fraction of key fields present (organism, assay type, tissue, disease, sample count)
- Bonus for normalized CURIEs

### Final Score
```
final_score = 0.55 * relevance + 0.30 * reuse + 0.15 * completeness
```

## Ontology Normalization

The system normalizes tissues and diseases using:

1. **OLS (Ontology Lookup Service)** - Primary method (no API key needed)
   - UBERON for tissues/anatomy
   - MONDO for diseases/conditions
   - Searches by label and synonyms

2. **LLM Alternative Names** (optional fallback)
   - Uses OpenAI to generate alternative names when OLS lookup fails
   - Requires `OPENAI_API_KEY` environment variable
   - Gracefully degrades if API key not set

## Caching

Dataset metadata is cached in `data/cache/datasets.json` to avoid re-fetching from GEO during development and demos.

## Limitations (MVP)

- Limited to GEO datasets only
- Simple keyword-based extraction (no NER)
- Best-effort ontology normalization (not comprehensive)
- Sample-level condition extraction is simplified
- No differential expression analysis
- Fixed seed list of GSE IDs

## Future Enhancements

- Multi-repository support (ArrayExpress, SRA)
- Better condition/group extraction
- Semantic search using embeddings
- Export results to CSV
- More comprehensive ontology mappings

## License

MIT License

## Acknowledgments

- GEO (Gene Expression Omnibus) for dataset access
- OLS (Ontology Lookup Service) for ontology lookups
- OpenAI for optional LLM enhancement
