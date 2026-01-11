# Scoring Algorithm

## Overview

The RNA-seq Dataset Discovery Agent uses a multi-factor scoring system to rank datasets. The final score is a weighted combination of three components:

**Final Score = 0.55 × Relevance + 0.30 × Reuse + 0.15 × Completeness**

## Scoring Components

### 1. Relevance Score (55% weight)

Measures how well a dataset matches the user's query.

| Component | Calculation | Details |
|-----------|-------------|---------|
| **Base Score** | `matches / total_query_keywords` | Counts how many query keywords appear in: title, summary, tissue_raw, disease_raw, organism |
| **Tissue Boost** | +0.2 | Applied if dataset has a normalized tissue CURIE AND query contains "tissue", "organ", or the tissue_raw term |
| **Disease Boost** | +0.2 | Applied if dataset has a normalized disease CURIE AND query contains "disease", "condition", or the disease_raw term |
| **Organism Boost** | +0.15 | Applied if query keyword matches organism (supports common→scientific name mappings: human→Homo sapiens, mouse→Mus musculus, rat→Rattus) |
| **Assay Boost** | +0.15 | Applied if query contains assay-related keywords (bulk, scrna, single cell, sc-rna, rna-seq) AND matches dataset assay_type |
| **Final Relevance** | `min(1.0, base_score + sum(boosts))` | Capped at 1.0 |

**Example**: Query "human liver NAFLD bulk"
- Base: 3/4 keywords match = 0.75
- Organism boost: +0.15 (human matches)
- Assay boost: +0.15 (bulk matches)
- **Total: min(1.0, 0.75 + 0.30) = 1.0**

---

### 2. Reuse Score (30% weight)

Measures the statistical power/reuse readiness of the dataset.

#### Bulk RNA-seq

| Minimum Samples per Condition | Reuse Score |
|-------------------------------|-------------|
| ≥10 samples/group | 1.0 |
| 6-9 samples/group | 0.7 |
| 3-5 samples/group | 0.4 |
| <3 samples/group | 0.1 |

*Note: If conditions are not extracted, falls back to total sample count with same thresholds.*

#### Single-cell RNA-seq (scRNA)

| Number of Donors | Reuse Score |
|------------------|-------------|
| ≥6 donors | 1.0 |
| 3-5 donors | 0.6 |
| <3 donors | 0.2 |

*Note: If donor count is unknown, uses total sample count with adjusted thresholds.*

---

### 3. Completeness Score (15% weight)

Measures metadata quality and normalization.

| Component | Score Contribution |
|-----------|-------------------|
| **Base Completeness** | Fraction of key fields present (0-1) |
| | - organism: present/absent (1/0) |
| | - assay_type: known/unknown (1/0) |
| | - tissue_raw: present/absent (1/0) |
| | - disease_raw: present/absent (1/0) |
| | - samples_total: present/absent (1/0) |
| | Base = (present_count) / 5 |
| **Normalization Bonus** | +0.1 per normalized CURIE (tissue or disease) |
| **Final Completeness** | `min(1.0, base_completeness + normalization_bonus)` |

**Example**: Dataset has organism, assay_type, tissue_raw, samples_total, and tissue_curie
- Base: 4/5 = 0.8
- Bonus: +0.1 (tissue normalized)
- **Total: min(1.0, 0.8 + 0.1) = 0.9**

---

## Final Score Calculation

```
final_score = 0.55 × relevance_score + 0.30 × reuse_score + 0.15 × completeness_score
```

**Example Calculation**:
- Relevance: 1.0 (perfect match)
- Reuse: 0.7 (6-9 samples per condition)
- Completeness: 0.9 (good metadata + normalization)

**Final Score** = 0.55 × 1.0 + 0.30 × 0.7 + 0.15 × 0.9 = 0.55 + 0.21 + 0.135 = **0.895**

---

## Reuse Badge Assignment

Based on raw reuse_score (0-1 range, before weighting in final score):

| Reuse Score | Badge |
|-------------|-------|
| ≥0.7 | 🟢 High |
| 0.4-0.69 | 🟡 Medium |
| <0.4 | 🔴 Low |
| 0.0 | Unknown |

---

## Notes

- All scores are normalized to [0, 1] range
- Final score determines ranking (higher = better)
- Relevance is weighted highest (55%) to prioritize query matching
- Reuse readiness (30%) ensures datasets have sufficient statistical power
- Completeness (15%) rewards well-annotated datasets with ontology normalization

