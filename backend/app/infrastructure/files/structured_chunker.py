"""Utilitários para chunking estruturado de textos com metadados."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional
import re

from app.domain.artifacts.types import ChunkMetadata

try:  # pragma: no-cover - dependência opcional
    import tiktoken  # type: ignore
except ImportError:  # pragma: no-cover - fallback sem tiktoken
    tiktoken = None  # type: ignore


_ENCODER = None


def _get_encoder():
    global _ENCODER
    if _ENCODER or not tiktoken:  # type: ignore[truthy-bool]
        return _ENCODER
    try:  # pragma: no-cover - inicialização depende da lib externa
        _ENCODER = tiktoken.get_encoding("cl100k_base")  # type: ignore[attr-defined]
    except Exception:  # pragma: no-cover - fallback
        _ENCODER = None
    return _ENCODER


def estimate_tokens(text: str) -> int:
    """Estima a contagem de tokens para um texto."""
    if not text:
        return 0

    encoder = _get_encoder()
    if encoder is not None:
        try:  # pragma: no-cover - dependente de lib externa
            return len(encoder.encode(text))
        except Exception:
            pass

    # Fallback heurístico: número de palavras (~1 token)
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    word_tokens = len(words)
    char_tokens = max(1, len(text) // 4)
    return max(1, word_tokens, char_tokens)


@dataclass
class StructuredBlock:
    """Representa um bloco de texto analisado com contexto estrutural."""

    text: str
    section_title: Optional[str]
    section_level: Optional[int]
    content_type: str
    breadcrumbs: List[str]
    token_count: int


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
BULLET_RE = re.compile(r"^([\-\*\+]\s+|\d+[\.)]\s+).+")
QUOTE_RE = re.compile(r"^>\s+.+")
TABLE_RE = re.compile(r"^\|.*\|$")
CODE_FENCE_RE = re.compile(r"^```.*$")


def analyze_structure(text: str) -> List[StructuredBlock]:
    """Analisa a estrutura de um texto Markdown simples gerando blocos."""
    if not text:
        return []

    lines = text.splitlines()
    blocks: List[StructuredBlock] = []
    heading_stack: List[tuple[int, str]] = []
    current_lines: List[str] = []
    current_type: str | None = None
    in_code_fence = False

    def current_breadcrumbs() -> List[str]:
        return [title for _, title in heading_stack]

    def flush_block():
        nonlocal current_lines, current_type
        if not current_lines:
            return
        block_text = "\n".join(current_lines).strip()
        if not block_text:
            current_lines = []
            current_type = None
            return
        section_title = heading_stack[-1][1] if heading_stack else None
        section_level = heading_stack[-1][0] if heading_stack else None
        breadcrumbs = current_breadcrumbs()
        block_type = current_type or "paragraph"
        token_count = estimate_tokens(block_text)
        blocks.append(
            StructuredBlock(
                text=block_text,
                section_title=section_title,
                section_level=section_level,
                content_type=block_type,
                breadcrumbs=breadcrumbs,
                token_count=token_count,
            )
        )
        current_lines = []
        current_type = None

    for raw_line in lines:
        line = raw_line.rstrip()

        if CODE_FENCE_RE.match(line):
            if not in_code_fence:
                flush_block()
                in_code_fence = True
                current_type = "code"
            else:
                current_lines.append(line)
                flush_block()
                in_code_fence = False
            continue

        if in_code_fence:
            current_lines.append(line)
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush_block()
            hashes, title = heading_match.groups()
            level = len(hashes)
            # Atualiza pilha de breadcrumbs
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title.strip()))
            # Adiciona heading como bloco próprio
            token_count = estimate_tokens(title)
            blocks.append(
                StructuredBlock(
                    text=title.strip(),
                    section_title=title.strip(),
                    section_level=level,
                    content_type="heading",
                    breadcrumbs=current_breadcrumbs(),
                    token_count=token_count,
                )
            )
            continue

        if not line.strip():
            flush_block()
            continue

        if BULLET_RE.match(line):
            if current_type != "bullet":
                flush_block()
                current_type = "bullet"
            current_lines.append(line)
            continue

        if QUOTE_RE.match(line):
            if current_type != "quote":
                flush_block()
                current_type = "quote"
            current_lines.append(line)
            continue

        if TABLE_RE.match(line):
            if current_type != "table":
                flush_block()
                current_type = "table"
            current_lines.append(line)
            continue

        if current_type not in {"paragraph", None}:
            flush_block()
        current_type = "paragraph"
        current_lines.append(line)

    flush_block()
    return blocks


def _build_chunk_metadata(blocks: Iterable[StructuredBlock], position: int) -> ChunkMetadata:
    blocks_list = list(blocks)
    section_title = None
    section_level = None
    breadcrumbs: List[str] = []

    for block in reversed(blocks_list):
        if block.section_title:
            section_title = block.section_title
            section_level = block.section_level
            breadcrumbs = block.breadcrumbs
            break
    if not breadcrumbs and blocks_list:
        breadcrumbs = blocks_list[-1].breadcrumbs

    token_count = sum(block.token_count for block in blocks_list)
    content_type = blocks_list[-1].content_type if blocks_list else "paragraph"

    return ChunkMetadata(
        section_title=section_title,
        section_level=section_level,
        content_type=content_type,
        position=position,
        token_count=token_count,
        breadcrumbs=breadcrumbs,
    )


def generate_chunks(
    blocks: List[StructuredBlock],
    max_tokens: int = 350,
    overlap_tokens: int = 60,
) -> List[tuple[str, ChunkMetadata]]:
    """Gera chunks coerentes a partir de blocos estruturados."""
    if not blocks:
        return []

    chunks: List[tuple[str, ChunkMetadata]] = []
    current_blocks: List[StructuredBlock] = []
    current_tokens = 0

    def push_chunk():
        nonlocal current_blocks, current_tokens
        if not current_blocks:
            return
        content = "\n\n".join(b.text for b in current_blocks if b.text.strip()).strip()
        metadata = _build_chunk_metadata(current_blocks, len(chunks))
        chunks.append((content, metadata))
        # prepara overlap
        if overlap_tokens <= 0:
            current_blocks = []
            current_tokens = 0
            return
        overlap: List[StructuredBlock] = []
        overlap_count = 0
        for block in reversed(current_blocks):
            overlap.insert(0, block)
            overlap_count += block.token_count
            if overlap_count >= overlap_tokens:
                break
        current_blocks = overlap
        current_tokens = sum(block.token_count for block in current_blocks)

    for block in blocks:
        # Se o bloco sozinho já excede o limite, dividimos grosseiramente por frases
        if block.token_count > max_tokens:
            sentences = re.split(r"(?<=[.!?])\s+", block.text)
            if len(sentences) <= 1:
                char_window = max_tokens * 4
                if char_window <= 0:
                    char_window = len(block.text)
                for start in range(0, len(block.text), char_window):
                    snippet = block.text[start:start + char_window]
                    if not snippet.strip():
                        continue
                    estimated_tokens = estimate_tokens(snippet)
                    metadata = ChunkMetadata(
                        section_title=block.section_title,
                        section_level=block.section_level,
                        content_type=block.content_type,
                        position=len(chunks),
                        token_count=estimated_tokens,
                        breadcrumbs=block.breadcrumbs,
                    )
                    chunks.append((snippet.strip(), metadata))
                current_blocks = []
                current_tokens = 0
                continue
            sentence_chunks: List[str] = []
            sentence_tokens = 0
            for sentence in sentences:
                if not sentence.strip():
                    continue
                tokens = estimate_tokens(sentence)
                if sentence_chunks and sentence_tokens + tokens > max_tokens:
                    sentence_content = " ".join(sentence_chunks)
                    metadata = ChunkMetadata(
                        section_title=block.section_title,
                        section_level=block.section_level,
                        content_type=block.content_type,
                        position=len(chunks),
                        token_count=sentence_tokens,
                        breadcrumbs=block.breadcrumbs,
                    )
                    chunks.append((sentence_content, metadata))
                    sentence_chunks = []
                    sentence_tokens = 0
                sentence_chunks.append(sentence)
                sentence_tokens += tokens
            if sentence_chunks:
                sentence_content = " ".join(sentence_chunks)
                metadata = ChunkMetadata(
                    section_title=block.section_title,
                    section_level=block.section_level,
                    content_type=block.content_type,
                    position=len(chunks),
                    token_count=sentence_tokens,
                    breadcrumbs=block.breadcrumbs,
                )
                chunks.append((sentence_content, metadata))
            current_blocks = []
            current_tokens = 0
            continue

        if current_blocks and current_tokens + block.token_count > max_tokens:
            push_chunk()

        current_blocks.append(block)
        current_tokens += block.token_count

    if current_blocks:
        push_chunk()

    # Ajusta posições finais
    final_chunks: List[tuple[str, ChunkMetadata]] = []
    for index, (content, metadata) in enumerate(chunks):
        final_metadata = ChunkMetadata(
            section_title=metadata.section_title,
            section_level=metadata.section_level,
            content_type=metadata.content_type,
            position=index,
            token_count=metadata.token_count,
            breadcrumbs=metadata.breadcrumbs,
        )
        final_chunks.append((content, final_metadata))

    return final_chunks


