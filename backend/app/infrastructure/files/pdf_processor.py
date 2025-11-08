"""Processamento de PDFs com suporte opcional a metadados estruturais."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, List, Tuple


try:  # pragma: no-cover - dependências opcionais podem faltar em testes
    import fitz  # type: ignore
except ImportError:  # pragma: no-cover
    fitz = None  # type: ignore

try:  # pragma: no-cover
    from pypdf import PdfReader  # type: ignore
except ImportError:  # pragma: no-cover
    PdfReader = None  # type: ignore


@dataclass
class _TocEntry:
    level: int
    title: str
    page_number: int


class PDFProcessor:
    """Processador de PDFs para extrair texto e metadados estruturais."""

    def extract_text(self, file_content: bytes) -> str:
        """Extrai texto contínuo do PDF, com fallback caso PyMuPDF não esteja disponível."""
        if fitz is not None:  # type: ignore[truthy-bool]
            try:
                with fitz.open(stream=file_content, filetype="pdf") as doc:  # type: ignore[attr-defined]
                    pages = [page.get_text("text") for page in doc]
                return "\n".join(pages)
            except Exception:
                pass

        if PdfReader is not None:  # type: ignore[truthy-bool]
            try:
                reader = PdfReader(self._bytes_io(file_content))
                texts = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(texts)
            except Exception:
                pass

        return ""

    def extract_with_metadata(self, file_content: bytes) -> List[Tuple[str, dict[str, Any]]]:
        """Extrai texto com metadados estruturais quando disponíveis."""
        if fitz is None:  # type: ignore[truthy-bool]
            plain_text = self.extract_text(file_content)
            if not plain_text:
                return []
            return [(plain_text, {})]

        try:
            with fitz.open(stream=file_content, filetype="pdf") as doc:  # type: ignore[attr-defined]
                toc = self._parse_toc(doc)
                segments: List[Tuple[str, dict[str, Any]]] = []
                heading_stack: deque[_TocEntry] = deque()
                toc_index = 0

                for page_number in range(doc.page_count):
                    while toc_index < len(toc) and toc[toc_index].page_number <= page_number:
                        entry = toc[toc_index]
                        while heading_stack and heading_stack[-1].level >= entry.level:
                            heading_stack.pop()
                        heading_stack.append(entry)
                        toc_index += 1

                    page = doc.load_page(page_number)
                    text = page.get_text("text")
                    if not text.strip():
                        continue

                    current_section = heading_stack[-1] if heading_stack else None
                    breadcrumbs = [entry.title for entry in heading_stack]
                    metadata = {
                        "section_title": current_section.title if current_section else None,
                        "section_level": current_section.level if current_section else None,
                        "content_type": "page",
                        "breadcrumbs": breadcrumbs,
                    }
                    segments.append((text, metadata))

                if segments:
                    return segments
        except Exception:
            pass

        plain_text = self.extract_text(file_content)
        if not plain_text:
            return []
        return [(plain_text, {})]

    @staticmethod
    def _bytes_io(file_content: bytes):
        from io import BytesIO
        return BytesIO(file_content)

    @staticmethod
    def _parse_toc(doc) -> List[_TocEntry]:  # pragma: no-cover - dependente de PyMuPDF
        try:
            raw_toc = doc.get_toc(simple=False)
        except Exception:
            raw_toc = []

        entries: List[_TocEntry] = []
        for item in raw_toc:
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                continue
            level, title, page_number = item[:3]
            if not isinstance(level, int):
                continue
            if not isinstance(title, str):
                continue
            if not isinstance(page_number, int):
                continue
            entries.append(_TocEntry(level=level, title=title.strip(), page_number=max(0, page_number - 1)))
        return entries

