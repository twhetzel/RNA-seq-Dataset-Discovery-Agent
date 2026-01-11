# RNA-seq Dataset Discovery Agent - Data Flow

```mermaid
flowchart TD
    Start([User Opens Streamlit App]) --> LoadButton{User Clicks<br/>Load/Refresh Datasets}
    
    LoadButton --> LoadSeed[Load GSE IDs from<br/>data/seed_gse.txt]
    
    LoadSeed --> CheckCache{Check Cache<br/>data/cache/datasets.json}
    
    CheckCache -->|Cache Hit| UseCached[Use Cached Dataset Data]
    CheckCache -->|Cache Miss| FetchGEO[Fetch from GEO API<br/>fetch_gse_soft]
    
    FetchGEO --> ParseSOFT[Parse SOFT Format<br/>Extract: title, summary, organism,<br/>samples_total, platform]
    
    ParseSOFT --> CacheData[Save to Cache]
    UseCached --> ExtractMetadata
    CacheData --> ExtractMetadata[Extract Metadata<br/>infer_assay_type<br/>extract_tissue<br/>extract_disease]
    
    ExtractMetadata --> NormalizeTissue{Extract Tissue?}
    ExtractMetadata --> NormalizeDisease{Extract Disease?}
    
    NormalizeTissue -->|Yes| OLSTissue[OLS Lookup UBERON]
    OLSTissue --> OLSTissueMatch{Match Found?}
    OLSTissueMatch -->|Yes| TissueCURIE[Store Tissue CURIE]
    OLSTissueMatch -->|No| LLMTissue{LLM Enabled?}
    LLMTissue -->|Yes| LLMGenTissue[Generate Alternative Names]
    LLMGenTissue --> OLSTissue
    LLMTissue -->|No| TissueRaw[Store Raw Tissue Only]
    
    NormalizeDisease -->|Yes| OLSDisease[OLS Lookup MONDO]
    OLSDisease --> OLSDiseaseMatch{Match Found?}
    OLSDiseaseMatch -->|Yes| DiseaseCURIE[Store Disease CURIE]
    OLSDiseaseMatch -->|No| LLMDisease{LLM Enabled?}
    LLMDisease -->|Yes| LLMGenDisease[Generate Alternative Names]
    LLMGenDisease --> OLSDisease
    LLMDisease -->|No| DiseaseRaw[Store Raw Disease Only]
    
    TissueCURIE --> StoreDataset[Store Dataset Object<br/>in Session State]
    TissueRaw --> StoreDataset
    DiseaseCURIE --> StoreDataset
    DiseaseRaw --> StoreDataset
    
    StoreDataset --> UserQuery{User Enters Query?}
    
    UserQuery -->|Yes| ApplyFilters[Apply Filters<br/>organism mapping<br/>assay_type<br/>min_samples]
    UserQuery -->|No| ShowAll[Show All Datasets<br/>First 20]
    
    ApplyFilters --> ComputeScores[Compute Scores for Each Dataset<br/>relevance_score 55%<br/>reuse_score 30%<br/>completeness_score 15%<br/>final_score = weighted sum]
    
    ComputeScores --> Rank[Rank Datasets<br/>Sort by final_score descending]
    
    Rank --> DisplayResults[Display Ranked Results<br/>with Explanations & Badges]
    ShowAll --> DisplayResults
    
    DisplayResults --> End([User Views Results])
    
    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style LoadButton fill:#fff4e6
    style FetchGEO fill:#ffe6e6
    style OLSTissue fill:#e6f3ff
    style OLSDisease fill:#e6f3ff
    style LLMGenTissue fill:#f0e6ff
    style LLMGenDisease fill:#f0e6ff
    style ComputeScores fill:#e6ffe6
    style Rank fill:#ffe6f5
    style DisplayResults fill:#fff9e6
```

## Component Details

### Data Ingestion
- **Input**: GSE IDs from `data/seed_gse.txt`
- **Source**: GEO (Gene Expression Omnibus) API
- **Format**: SOFT format text
- **Caching**: Results cached in `data/cache/datasets.json`

### Metadata Extraction
- **Assay Type**: Keyword-based inference (bulk/scRNA/unknown)
- **Tissue**: Simple keyword scanning from title/summary
- **Disease**: Simple keyword scanning from title/summary

### Ontology Normalization
- **Primary**: OLS (Ontology Lookup Service) - no API key needed
  - Tissues → UBERON
  - Diseases → MONDO
- **Fallback**: OpenAI LLM (optional) - generates alternative names
  - Requires OPENAI_API_KEY
  - Only used when OLS lookup fails

### Scoring
- **Relevance Score** (55%): Keyword overlap + ontology matches
- **Reuse Score** (30%): Sample counts/conditions (bulk) or donors (scRNA)
- **Completeness Score** (15%): Metadata fields present
- **Final Score**: Weighted combination

### Filtering & Ranking
- **Filters**: Organism (with common→scientific name mapping), assay type, min samples
- **Ranking**: Sort by final_score descending
- **Output**: Top 20 results with explanations

