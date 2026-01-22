"""Streamlit app for RNA-seq dataset discovery."""

import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from ingest.pipeline import load_and_process_datasets
from rank.ranker import rank_datasets
from rank.scoring import generate_explanations
from model.schema import Dataset


# Page configuration
st.set_page_config(
    page_title="RNA-seq Dataset Discovery",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title and description
st.title("🧬 RNA-seq Dataset Discovery Agent")
st.markdown(
    """
    Discover and rank RNA-seq datasets from GEO based on:
    - **Relevance** to your query
    - **Reuse readiness** (sample counts, conditions)
    - **Metadata completeness** with ontology normalization
    """
)

# Sidebar
with st.sidebar:
    st.header("Search & Filters")

    # Query input
    query = st.text_input(
        "Search Query",
        placeholder="e.g., human liver NAFLD bulk rna-seq",
        help="Enter keywords to search for datasets (press Enter to search)",
        key="search_query",
    )

    # Filters
    st.subheader("Filters")

    organism_filter = st.selectbox(
        "Organism",
        ["any", "human", "mouse", "rat"],
        help="Filter by organism",
    )

    assay_filter = st.selectbox(
        "Assay Type",
        ["any", "bulk", "scRNA"],
        help="Filter by RNA-seq assay type",
    )

    min_samples = st.number_input(
        "Minimum Samples",
        min_value=0,
        value=0,
        step=1,
        help="Minimum number of samples required",
    )

    # LLM toggle
    use_llm = st.checkbox(
        "Use LLM Enhancement",
        value=False,
        help="Enable LLM-based alternative name generation for ontology normalization (requires OPENAI_API_KEY)",
    )

    if use_llm and not os.getenv("OPENAI_API_KEY"):
        st.warning("⚠️ OPENAI_API_KEY not set. LLM enhancement disabled.")
        use_llm = False

    # Load datasets button
    load_data = st.button("Load/Refresh Datasets", type="primary")

# Initialize session state
if "datasets" not in st.session_state:
    st.session_state.datasets = []

if "use_llm_state" not in st.session_state:
    st.session_state.use_llm_state = False

# Load datasets
if load_data or len(st.session_state.datasets) == 0:
    with st.spinner("Loading and processing datasets..."):
        try:
            datasets = load_and_process_datasets(use_llm=use_llm)
            st.session_state.datasets = datasets
            st.session_state.use_llm_state = use_llm
            st.success(f"Loaded {len(datasets)} datasets")
        except Exception as e:
            st.error(f"Error loading datasets: {e}")
            st.session_state.datasets = []

# Main content
if len(st.session_state.datasets) == 0:
    st.info("👆 Click 'Load/Refresh Datasets' to start")
else:
    # Prepare filters
    filters = {
        "organism": organism_filter if organism_filter != "any" else None,
        "assay_type": assay_filter if assay_filter != "any" else None,
        "min_samples": min_samples if min_samples > 0 else None,
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    # Rank datasets (apply filters even if no query)
    # Use a high top_k to show all matching results (not just 20)
    ranked = rank_datasets(
        st.session_state.datasets, 
        query=query if query else "", 
        filters=filters,
        top_k=len(st.session_state.datasets)  # Show all matching results
    )

    # Results header
    st.subheader(f"Results ({len(ranked)} datasets)")

    if len(ranked) == 0:
        st.info("No datasets match your query and filters. Try adjusting your search.")
    else:
        # Results table
        for idx, dataset in enumerate(ranked, 1):
            with st.expander(
                f"**{idx}. {dataset.dataset_id}** - {dataset.title[:100]}"
                + ("..." if len(dataset.title) > 100 else ""),
                expanded=False,
            ):
                # Basic info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Final Score ❓", f"{dataset.final_score:.3f}")
                    st.caption("Weighted combination of relevance (55%), reuse (30%), and completeness (15%)")
                    st.metric("Relevance ❓", f"{dataset.relevance_score:.3f}")
                    st.caption("How well the dataset matches your query (0-1)")
                with col2:
                    st.metric("Reuse Score ❓", f"{dataset.reuse_score:.3f}")
                    st.caption("Statistical power based on sample counts (0-1)")
                    st.metric("Reuse Badge ❓", dataset.reuse_badge)
                    st.caption("High: ≥0.7, Medium: 0.4-0.69, Low: <0.4")
                with col3:
                    st.metric("Completeness ❓", f"{dataset.completeness_score:.3f}")
                    st.caption("Metadata quality and normalization (0-1)")
                    st.metric("Samples ❓", dataset.samples_total or "Unknown")
                    st.caption("Total number of samples in the dataset")

                # Details
                st.markdown("### Dataset Details")
                details_col1, details_col2 = st.columns(2)

                with details_col1:
                    geo_url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={dataset.dataset_id}"
                    st.markdown(f"**Dataset ID:** [{dataset.dataset_id}]({geo_url})")
                    st.write(f"**Organism ❓:** {dataset.organism or 'Unknown'}")
                    st.caption("Species (e.g., Homo sapiens, Mus musculus)")
                    st.write(f"**Assay Type ❓:** {dataset.assay_type}")
                    st.caption("RNA-seq type: bulk, scRNA (single-cell), or unknown")
                    st.write(f"**Platform ❓:** {dataset.platform or 'Unknown'}")
                    st.caption("Sequencing platform used")

                with details_col2:
                    st.write(f"**Tissue ❓:** {dataset.tissue_raw or 'Unknown'}")
                    st.caption("Tissue or organ type extracted from metadata")
                    if dataset.tissue_curie:
                        source = dataset.tissue_normalization_source or "ols"
                        st.write(
                            f"**Tissue (normalized) ❓:** {dataset.tissue_curie} (via {source.upper()})"
                        )
                        st.caption(f"UBERON ontology term normalized via {source.upper()}")
                    st.write(f"**Disease ❓:** {dataset.disease_raw or 'Unknown'}")
                    st.caption("Disease or condition extracted from metadata")
                    if dataset.disease_curie:
                        source = dataset.disease_normalization_source or "ols"
                        st.write(
                            f"**Disease (normalized) ❓:** {dataset.disease_curie} (via {source.upper()})"
                        )
                        st.caption(f"MONDO ontology term normalized via {source.upper()}")

                # Summary
                if dataset.summary:
                    st.markdown("### Summary")
                    st.write(dataset.summary[:500] + ("..." if len(dataset.summary) > 500 else ""))

                # Explanations
                if query:
                    explanations = generate_explanations(dataset, query)
                    if explanations:
                        st.markdown("### Explanation")
                        for exp in explanations:
                            st.write(f"• {exp}")

                # Conditions
                if dataset.conditions:
                    st.markdown("### Conditions")
                    st.json(dataset.conditions)

                st.divider()

# Footer
st.markdown("---")
st.markdown(
    """
    **RNA-seq Dataset Discovery Agent** | 
    Powered by GEO, OLS (UBERON, MONDO), and optional OpenAI
    """
)

