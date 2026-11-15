"""Registered NASA Scientific Documents Catalogue (Milestone 10.4).

Provides authoritative metadata, file locations, and explicit epistemic attributions.
Attribution is declared directly from document type and publishing authority,
ensuring attribution is NEVER inferred from filenames alone.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

# Stable namespace for deterministic Document and Chunk UUIDs
NAMESPACE_FLARE_DOCS = UUID("b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e")


@dataclass(frozen=True)
class RegisteredDocumentSpec:
    """Specification for a registered NASA literature or technical report document."""
    doc_key: str
    original_filename: str
    relative_path: str
    investigation_code: str
    source_type: str  # 'pdf' or 'docx'
    document_type: str  # 'technical_report', 'readme', 'faq', 'mini_book', etc.
    epistemic_attribution: str  # 'experimental_observation', 'reference_information', 'numerical_simulation'
    title: str
    description: str
    authors: str
    publication_year: int
    doi: str | None = None
    is_validated_measurement: bool = False  # Text passages are NEVER quantitative analytical measurements


REGISTERED_DOCUMENTS: dict[str, RegisteredDocumentSpec] = {
    "bass_ii_faq": RegisteredDocumentSpec(
        doc_key="bass_ii_faq",
        original_filename="BASS-II data FAQ.docx",
        relative_path="data/raw/bass_ii/original/BASS-II data FAQ.docx",
        investigation_code="PSI-25",
        source_type="docx",
        document_type="faq",
        epistemic_attribution="reference_information",
        title="BASS-II Experimental Data FAQ",
        description="Official NASA BASS-II data guide explaining test matrix structure, fan calibrations, and operational test parameters.",
        authors="NASA BASS-II Science Team",
        publication_year=2014,
    ),
    "bass_ii_readme": RegisteredDocumentSpec(
        doc_key="bass_ii_readme",
        original_filename="PSI-25_Science Documents_BASS-II_ReadMe.docx",
        relative_path="data/raw/challenge_resources/original/bass_ii/PSI-25_Science Documents_BASS-II_ReadMe.docx",
        investigation_code="PSI-25",
        source_type="docx",
        document_type="readme",
        epistemic_attribution="reference_information",
        title="BASS-II Experiment Overview Readme",
        description="NASA Physical Sciences Informatics BASS-II Readme detailing microgravity hardware and observation logging.",
        authors="NASA Physical Sciences Informatics",
        publication_year=2014,
    ),
    "bass_ii_summary_report": RegisteredDocumentSpec(
        doc_key="bass_ii_summary_report",
        original_filename="PSI-25_Reports_BASS-II Summary Report.pdf",
        relative_path="data/raw/challenge_resources/original/bass_ii/PSI-25_Reports_BASS-II Summary Report.pdf",
        investigation_code="PSI-25",
        source_type="pdf",
        document_type="technical_report",
        epistemic_attribution="experimental_observation",
        title="Burning and Suppression of Solids-II (BASS-II) Final Summary Report",
        description="Comprehensive NASA technical report detailing microgravity solid fuel combustion, flame propagation, and extinction on ISS.",
        authors="Sandra L. Olson, Paul V. Ferkul, Subrata Bhattacharjee, Fletcher J. Miller",
        publication_year=2015,
        doi="10.60555/4qc4-de67",
    ),
    "bass_ii_srd": RegisteredDocumentSpec(
        doc_key="bass_ii_srd",
        original_filename="PSI-25_Science Documents_BASS-II_SRD.pdf",
        relative_path="data/raw/challenge_resources/original/bass_ii/PSI-25_Science Documents_BASS-II_SRD.pdf",
        investigation_code="PSI-25",
        source_type="pdf",
        document_type="science_requirements",
        epistemic_attribution="reference_information",
        title="BASS-II Science Requirements Document",
        description="Formal NASA science requirements specifying solid fuel combustion regimes, air flow speeds, and extinction limits.",
        authors="NASA Glenn Research Center",
        publication_year=2012,
    ),
    "jsc_microgravity_mini_book": RegisteredDocumentSpec(
        doc_key="jsc_microgravity_mini_book",
        original_filename="np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf",
        relative_path="data/raw/challenge_resources/original/other/np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf",
        investigation_code="PSI-25",
        source_type="pdf",
        document_type="mini_book",
        epistemic_attribution="reference_information",
        title="Combustion in Reduced Gravity: ISS Research Mini-Book",
        description="NASA Johnson Space Center comprehensive reference on microgravity combustion physics, spherical flame diffusion, buoyancy suppression, and fire safety.",
        authors="NASA Johnson Space Center / International Space Station Program",
        publication_year=2015,
    ),
    "saffire_ices_report": RegisteredDocumentSpec(
        doc_key="saffire_ices_report",
        original_filename="ICES 2021-266 0503-2021 final.pdf",
        relative_path="data/raw/challenge_resources/original/saffire/NTRS-20210011521/ICES 2021-266 0503-2021 final.pdf",
        investigation_code="PSI-25",
        source_type="pdf",
        document_type="conference_paper",
        epistemic_attribution="experimental_observation",
        title="Saffire Large-Scale Spacecraft Fire Safety Flight Experiments",
        description="Flight results and flame spread observations from the Spacecraft Fire Safety Demonstration Project (Saffire) aboard Cygnus vehicles.",
        authors="David L. Urban, Gary A. Ruff, et al.",
        publication_year=2021,
    ),
    "iss_researchers_guide": RegisteredDocumentSpec(
        doc_key="iss_researchers_guide",
        original_filename="PSI-20_Science Documents_ISS_Researchers_Guide_-_Combustion_In_Reduced_Gravity.pdf",
        relative_path="data/raw/challenge_resources/original/acme/PSI-20/PSI-20_Science Documents_ISS_Researchers_Guide_-_Combustion_In_Reduced_Gravity.pdf",
        investigation_code="PSI-25",
        source_type="pdf",
        document_type="researchers_guide",
        epistemic_attribution="reference_information",
        title="ISS Researcher's Guide to Combustion Science in Reduced Gravity",
        description="NASA overview of microgravity combustion facilities, droplet combustion, solid surface flammability, and gaseous flame phenomena.",
        authors="Daniel L. Dietrich et al.",
        publication_year=2015,
    ),
}


def doc_uuid(file_sha256: str) -> UUID:
    """Generate a deterministic UUID for a source document from its authentic SHA-256."""
    return uuid5(NAMESPACE_FLARE_DOCS, f"source_document:{file_sha256}")


def chunk_uuid(source_doc_uuid: UUID | str, chunk_index: int) -> UUID:
    """Generate a deterministic UUID for a document chunk."""
    if isinstance(source_doc_uuid, str):
        source_doc_uuid = UUID(source_doc_uuid)
    return uuid5(source_doc_uuid, f"chunk:{chunk_index}")
