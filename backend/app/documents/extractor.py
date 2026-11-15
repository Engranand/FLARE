"""Document Text Extraction for NASA PDF and DOCX Files (Milestone 10.4).

Preserves page numbers, section headers, and paragraph boundaries without altering
source files or inventing missing text.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

import pypdf


@dataclass(frozen=True)
class DocumentPage:
    """Represents text extracted from a single physical or logical document page."""
    page_number: int
    text: str
    section_title: str | None = None


class DocumentExtractionError(Exception):
    """Raised when document extraction encounters unreadable or corrupt content."""


def extract_pdf(path: Path) -> list[DocumentPage]:
    """Extract text and page numbers from a PDF document using pypdf.
    
    Args:
        path: Path to the PDF file.
        
    Returns:
        List of DocumentPage objects with 1-indexed page numbers.
    """
    if not path.is_file():
        raise DocumentExtractionError(f"PDF file not found: {path}")

    try:
        reader = pypdf.PdfReader(str(path))
    except Exception as exc:
        raise DocumentExtractionError(f"Failed to read PDF {path.name}: {exc}") from exc

    pages: list[DocumentPage] = []
    current_section: str | None = None

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        try:
            raw_text = page.extract_text() or ""
        except Exception:
            raw_text = ""

        # Normalize line breaks and clean whitespace
        cleaned = re.sub(r"\r\n|\r", "\n", raw_text)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()

        # Simple section detection: look for prominent heading lines
        first_lines = [line.strip() for line in cleaned.split("\n") if line.strip()][:3]
        for line in first_lines:
            if len(line) < 80 and (
                re.match(r"^(SECTION|CHAPTER|\d+\.0|\d+\.\d+)\b", line, re.IGNORECASE)
                or (line.isupper() and len(line) > 5)
            ):
                current_section = line
                break

        pages.append(
            DocumentPage(
                page_number=page_num,
                text=cleaned,
                section_title=current_section,
            )
        )

    return pages


def extract_docx(path: Path) -> list[DocumentPage]:
    """Extract text, sections, and page references from a DOCX document using pure-Python XML parsing.
    
    Args:
        path: Path to the DOCX file.
        
    Returns:
        List of DocumentPage objects.
    """
    if not path.is_file():
        raise DocumentExtractionError(f"DOCX file not found: {path}")

    try:
        with zipfile.ZipFile(str(path)) as zf:
            if "word/document.xml" not in zf.namelist():
                raise DocumentExtractionError(f"Invalid DOCX: missing word/document.xml in {path.name}")
            xml_bytes = zf.read("word/document.xml")
    except Exception as exc:
        raise DocumentExtractionError(f"Failed to open DOCX archive {path.name}: {exc}") from exc

    try:
        tree = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise DocumentExtractionError(f"Malformed XML in {path.name}: {exc}") from exc

    w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    paragraphs: list[tuple[str, str | None]] = []
    current_section: str | None = None

    for p in tree.iter(f"{{{w_ns}}}p"):
        # Check paragraph style for headings
        p_style = p.find(f".//{{{w_ns}}}pStyle")
        is_heading = False
        if p_style is not None:
            style_val = p_style.attrib.get(f"{{{w_ns}}}val", "")
            if "heading" in style_val.lower() or "title" in style_val.lower():
                is_heading = True

        # Extract text nodes
        texts = [node.text for node in p.iter(f"{{{w_ns}}}t") if node.text]
        if texts:
            para_text = "".join(texts).strip()
            if para_text:
                if is_heading:
                    current_section = para_text
                paragraphs.append((para_text, current_section))

    # In DOCX without physical page breaks, group paragraphs into logical pages (~350 words each)
    pages: list[DocumentPage] = []
    current_page_paras: list[str] = []
    current_page_words = 0
    page_num = 1
    page_section: str | None = None

    for para_text, sec in paragraphs:
        words = len(para_text.split())
        if page_section is None and sec is not None:
            page_section = sec

        if current_page_words + words > 400 and current_page_paras:
            pages.append(
                DocumentPage(
                    page_number=page_num,
                    text="\n\n".join(current_page_paras),
                    section_title=page_section,
                )
            )
            page_num += 1
            current_page_paras = [para_text]
            current_page_words = words
            page_section = sec
        else:
            current_page_paras.append(para_text)
            current_page_words += words
            if sec:
                page_section = sec

    if current_page_paras:
        pages.append(
            DocumentPage(
                page_number=page_num,
                text="\n\n".join(current_page_paras),
                section_title=page_section,
            )
        )

    return pages


def extract_document_text(path: Path) -> list[DocumentPage]:
    """Dispatch document extraction based on file extension.
    
    Args:
        path: Path to target document (PDF or DOCX).
        
    Returns:
        List of DocumentPage objects with page numbers and text.
    """
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path)
    if ext == ".docx":
        return extract_docx(path)
    raise DocumentExtractionError(f"Unsupported document format '{ext}' for file {path.name}")
