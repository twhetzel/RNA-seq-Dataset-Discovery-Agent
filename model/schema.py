"""Data models for RNA-seq dataset discovery agent."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Dataset(BaseModel):
    """Core dataset schema with all required and inferred fields."""

    # Required fields
    dataset_id: str = Field(..., description="GEO dataset ID (e.g., GSE12345)")
    title: str = Field(..., description="Dataset title")
    summary: Optional[str] = Field(None, description="Dataset summary/description")
    organism: Optional[str] = Field(None, description="Organism (e.g., Homo sapiens)")
    assay_type: Literal["bulk", "scRNA", "unknown"] = Field(
        "unknown", description="Type of RNA-seq assay"
    )
    platform: Optional[str] = Field(None, description="Platform/technology used")

    # Extracted/inferred fields
    tissue_raw: Optional[str] = Field(None, description="Raw extracted tissue string")
    disease_raw: Optional[str] = Field(None, description="Raw extracted disease string")
    tissue_curie: Optional[str] = Field(None, description="UBERON CURIE for tissue")
    disease_curie: Optional[str] = Field(None, description="MONDO CURIE for disease")
    samples_total: Optional[int] = Field(None, description="Total number of samples")
    conditions: Optional[dict[str, int]] = Field(
        None, description="Mapping of condition to sample count"
    )
    donors: Optional[int] = Field(
        None, description="Number of donors (for scRNA-seq)"
    )

    # Normalization tracking
    tissue_normalization_source: Optional[Literal["ols", "llm"]] = Field(
        None, description="Source of tissue normalization (ols or llm)"
    )
    disease_normalization_source: Optional[Literal["ols", "llm"]] = Field(
        None, description="Source of disease normalization (ols or llm)"
    )

    # Metadata quality
    completeness_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Metadata completeness score (0-1)"
    )
    normalization_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence in normalization (0-1)"
    )

    # Scoring fields (computed)
    relevance_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Relevance score (0-1)"
    )
    reuse_score: float = Field(0.0, ge=0.0, le=1.0, description="Reuse score (0-1)")
    final_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Final weighted score (0-1)"
    )

    # Reuse badge (computed from reuse_score)
    reuse_badge: Literal["High", "Medium", "Low", "Unknown"] = Field(
        "Unknown", description="Reuse readiness badge"
    )

    class Config:
        """Pydantic configuration."""

        frozen = False  # Allow updates after creation


# Optional: Sample model (for future use if time permits)
class Sample(BaseModel):
    """Sample schema (optional for MVP)."""

    sample_id: str = Field(..., description="Sample ID (e.g., GSM123456)")
    dataset_id: str = Field(..., description="Parent dataset ID")
    characteristics: dict[str, str] = Field(
        default_factory=dict, description="Parsed sample characteristics"
    )
    condition: Optional[str] = Field(None, description="Sample condition/group")
    donor_id: Optional[str] = Field(None, description="Donor ID (for scRNA-seq)")

