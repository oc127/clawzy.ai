"""Knowledge Base Service — Lucy's document understanding system.

Upload documents -> extract text -> chunk intelligently -> embed -> search.
Lucy can then discuss document contents in-character.
"""

import asyncio
import io
import json
import logging
import math
import uuid
from datetime import UTC, datetime

import litellm
from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.knowledge import KnowledgeBase, KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)

# --- Constants ---
CHUNK_SIZE = 500  # target tokens per chunk
CHUNK_OVERLAP = 50  # overlap tokens between chunks
EMBEDDING_MODEL = "text-embedding-3-small"  # via litellm
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
EMBEDDING_BATCH_SIZE = 100  # max texts per embedding request


# --- Helpers ---

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: word count * 1.3."""
    return int(len(text.split()) * 1.3)


# --- Knowledge Base CRUD ---

async def create_knowledge_base(
    db: AsyncSession,
    user_id: str,
    name: str,
    description: str | None = None,
) -> KnowledgeBase:
    """Create a new knowledge base."""
    kb = KnowledgeBase(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=name,
        description=description,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


async def list_knowledge_bases(db: AsyncSession, user_id: str) -> list[KnowledgeBase]:
    """List all knowledge bases for a user."""
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == user_id)
        .order_by(KnowledgeBase.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_knowledge_base(db: AsyncSession, kb_id: str, user_id: str) -> KnowledgeBase | None:
    """Get a single knowledge base."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_knowledge_base(
    db: AsyncSession,
    kb_id: str,
    user_id: str,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> KnowledgeBase | None:
    """Update knowledge base metadata."""
    kb = await get_knowledge_base(db, kb_id, user_id)
    if kb is None:
        return None
    if name is not None:
        kb.name = name
    if description is not None:
        kb.description = description
    if is_active is not None:
        kb.is_active = is_active
    kb.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(kb)
    return kb


async def delete_knowledge_base(db: AsyncSession, kb_id: str, user_id: str) -> bool:
    """Delete a knowledge base and all its documents/chunks (via CASCADE)."""
    kb = await get_knowledge_base(db, kb_id, user_id)
    if kb is None:
        return False
    await db.delete(kb)
    await db.commit()
    return True


# --- Document Processing ---

def extract_text(content_bytes: bytes, file_type: str) -> str:
    """Extract plain text from various file types.

    For PDF: attempts PyPDF2, then pdfplumber, then falls back to utf-8 decode
    with errors='ignore'. Install PyPDF2 or pdfplumber for proper PDF support.
    For markdown/text/code: decodes as utf-8.
    """
    if file_type == "pdf":
        # Try PyPDF2 first
        try:
            import PyPDF2  # noqa: F811

            reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            if pages:
                return "\n\n".join(pages)
        except ImportError:
            pass
        except Exception:
            logger.warning("PyPDF2 failed to extract text, trying pdfplumber")

        # Try pdfplumber
        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
                if pages:
                    return "\n\n".join(pages)
        except ImportError:
            pass
        except Exception:
            logger.warning("pdfplumber failed to extract text")

        # Fallback: decode as utf-8 with error handling
        # NOTE: This won't produce great results for binary PDFs.
        # Install PyPDF2 (`pip install PyPDF2`) for proper PDF support.
        return content_bytes.decode("utf-8", errors="ignore")

    # markdown, text, code — all are already text
    return content_bytes.decode("utf-8", errors="replace")


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """Split text into overlapping chunks.

    Strategy:
    1. Split by paragraphs (double newline)
    2. If a paragraph > chunk_size tokens, split by sentences
    3. Merge small consecutive paragraphs into one chunk
    4. Ensure overlap between chunks for context continuity

    Returns: list of {"content": str, "chunk_index": int, "token_count": int}
    """
    if not text or not text.strip():
        return []

    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Break oversized paragraphs into sentences
    segments: list[str] = []
    for para in paragraphs:
        if _estimate_tokens(para) <= chunk_size:
            segments.append(para)
        else:
            # Split by sentence-ending punctuation
            sentences = _split_sentences(para)
            segments.extend(sentences)

    # Merge small segments into chunks of ~chunk_size tokens
    chunks: list[dict] = []
    current_parts: list[str] = []
    current_tokens = 0

    for segment in segments:
        seg_tokens = _estimate_tokens(segment)

        if current_tokens + seg_tokens > chunk_size and current_parts:
            # Emit current chunk
            chunk_text_content = "\n\n".join(current_parts)
            chunks.append({
                "content": chunk_text_content,
                "chunk_index": len(chunks),
                "token_count": _estimate_tokens(chunk_text_content),
            })

            # Keep overlap: take the last part(s) that fit within overlap budget
            overlap_parts: list[str] = []
            overlap_tokens = 0
            for part in reversed(current_parts):
                part_tokens = _estimate_tokens(part)
                if overlap_tokens + part_tokens > overlap:
                    break
                overlap_parts.insert(0, part)
                overlap_tokens += part_tokens

            current_parts = overlap_parts
            current_tokens = overlap_tokens

        current_parts.append(segment)
        current_tokens += seg_tokens

    # Emit final chunk
    if current_parts:
        chunk_text_content = "\n\n".join(current_parts)
        chunks.append({
            "content": chunk_text_content,
            "chunk_index": len(chunks),
            "token_count": _estimate_tokens(chunk_text_content),
        })

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, keeping punctuation attached."""
    import re

    # Split on sentence-ending punctuation followed by whitespace
    raw = re.split(r"(?<=[.!?])\s+", text)
    # Merge very short fragments back
    sentences: list[str] = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        if sentences and _estimate_tokens(sentences[-1]) < 20:
            sentences[-1] = sentences[-1] + " " + s
        else:
            sentences.append(s)
    return sentences if sentences else [text]


async def generate_embeddings(texts: list[str]) -> list[list[float] | None]:
    """Generate embeddings for a list of texts using litellm.

    Batches requests if needed. Falls back to None per text if the embedding
    service is unavailable.
    """
    if not texts:
        return []

    results: list[list[float] | None] = [None] * len(texts)

    for batch_start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[batch_start : batch_start + EMBEDDING_BATCH_SIZE]
        try:
            response = await litellm.aembedding(
                model=EMBEDDING_MODEL,
                input=batch,
            )
            for i, item in enumerate(response.data):
                results[batch_start + i] = item["embedding"]
        except Exception:
            logger.exception(
                "Embedding generation failed for batch starting at %d (batch size %d)",
                batch_start,
                len(batch),
            )
            # Leave results as None for this batch — chunks still get stored without embeddings

    return results


async def process_document(db: AsyncSession, document_id: str) -> None:
    """Full processing pipeline for a document.

    1. Load document from DB
    2. Chunk the content
    3. Generate embeddings for each chunk
    4. Store chunks with embeddings
    5. Update document status and counts
    6. Update knowledge base counts
    """
    try:
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            logger.error("Document %s not found for processing", document_id)
            return

        doc.status = "processing"
        await db.commit()

        # Chunk
        chunks = chunk_text(doc.content_text)
        if not chunks:
            doc.status = "ready"
            doc.chunk_count = 0
            await db.commit()
            await _update_kb_counts(db, doc.knowledge_base_id)
            return

        # Generate embeddings
        chunk_texts = [c["content"] for c in chunks]
        embeddings = await generate_embeddings(chunk_texts)

        # Store chunks
        for chunk_data, embedding in zip(chunks, embeddings):
            chunk = KnowledgeChunk(
                id=str(uuid.uuid4()),
                document_id=doc.id,
                knowledge_base_id=doc.knowledge_base_id,
                user_id=doc.user_id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                token_count=chunk_data["token_count"],
                embedding=embedding,
            )
            db.add(chunk)

        doc.chunk_count = len(chunks)
        doc.status = "ready"
        await db.commit()

        await _update_kb_counts(db, doc.knowledge_base_id)
        logger.info(
            "Processed document %s: %d chunks created",
            document_id,
            len(chunks),
        )

    except Exception:
        logger.exception("Failed to process document %s", document_id)
        try:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "failed"
                doc.error = "Processing failed — see server logs for details."
                await db.commit()
        except Exception:
            logger.exception("Failed to update document status to failed")


async def _process_document_background(document_id: str) -> None:
    """Wrapper that opens its own DB session for background processing."""
    async with async_session() as db:
        await process_document(db, document_id)


async def upload_document(
    db: AsyncSession,
    kb_id: str,
    user_id: str,
    filename: str,
    content_bytes: bytes,
    file_type: str,
) -> KnowledgeDocument:
    """Upload and process a document.

    1. Validate file size
    2. Extract text from bytes based on file_type
    3. Store the document record
    4. Kick off async processing (chunking + embedding)
    """
    if len(content_bytes) > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {len(content_bytes)} bytes (max {MAX_FILE_SIZE})")

    # Verify the knowledge base exists and belongs to the user
    kb = await get_knowledge_base(db, kb_id, user_id)
    if kb is None:
        raise ValueError(f"Knowledge base {kb_id} not found")

    # Extract text
    content_text = extract_text(content_bytes, file_type)
    if not content_text.strip():
        raise ValueError("Could not extract text from file")

    doc = KnowledgeDocument(
        id=str(uuid.uuid4()),
        knowledge_base_id=kb_id,
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        file_size=len(content_bytes),
        content_text=content_text,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Kick off background processing
    asyncio.create_task(_process_document_background(doc.id))

    return doc


async def _update_kb_counts(db: AsyncSession, kb_id: str) -> None:
    """Recompute document_count and total_chunks for a knowledge base."""
    doc_count_result = await db.execute(
        select(func.count()).where(KnowledgeDocument.knowledge_base_id == kb_id)
    )
    doc_count = doc_count_result.scalar() or 0

    chunk_count_result = await db.execute(
        select(func.count()).where(KnowledgeChunk.knowledge_base_id == kb_id)
    )
    chunk_count = chunk_count_result.scalar() or 0

    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    if kb:
        kb.document_count = doc_count
        kb.total_chunks = chunk_count
        kb.updated_at = datetime.now(UTC)
        await db.commit()


# --- Semantic Search ---

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


async def search_knowledge(
    db: AsyncSession,
    user_id: str,
    query: str,
    kb_ids: list[str] | None = None,
    limit: int = 5,
) -> list[dict]:
    """Semantic search across user's knowledge bases.

    1. Generate embedding for the query
    2. Load all chunks from active knowledge bases (or specified kb_ids)
    3. Compute cosine similarity
    4. Return top-k results with content, similarity score, and source info

    Returns: [{"content": str, "score": float, "document": str, "knowledge_base": str}]
    """
    # Generate query embedding
    query_embeddings = await generate_embeddings([query])
    query_embedding = query_embeddings[0] if query_embeddings else None
    if query_embedding is None:
        logger.warning("Could not generate embedding for query, falling back to empty results")
        return []

    # Determine which knowledge bases to search
    if kb_ids:
        kb_filter = KnowledgeChunk.knowledge_base_id.in_(kb_ids)
    else:
        # Get active knowledge bases for the user
        active_kb_result = await db.execute(
            select(KnowledgeBase.id).where(
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.is_active.is_(True),
            )
        )
        active_kb_ids = [row[0] for row in active_kb_result.all()]
        if not active_kb_ids:
            return []
        kb_filter = KnowledgeChunk.knowledge_base_id.in_(active_kb_ids)

    # Load chunks with embeddings
    result = await db.execute(
        select(KnowledgeChunk)
        .where(
            KnowledgeChunk.user_id == user_id,
            kb_filter,
            KnowledgeChunk.embedding.isnot(None),
        )
    )
    chunks = result.scalars().all()

    if not chunks:
        return []

    # Compute similarities
    scored: list[tuple[float, KnowledgeChunk]] = []
    for chunk in chunks:
        score = cosine_similarity(query_embedding, chunk.embedding)
        scored.append((score, chunk))

    # Sort by score descending and take top-k
    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:limit]

    # Enrich with document and knowledge base names
    results = []
    # Cache document/kb lookups
    doc_cache: dict[str, str] = {}
    kb_cache: dict[str, str] = {}

    for score, chunk in top_results:
        # Get document filename
        if chunk.document_id not in doc_cache:
            doc_result = await db.execute(
                select(KnowledgeDocument.filename).where(KnowledgeDocument.id == chunk.document_id)
            )
            row = doc_result.first()
            doc_cache[chunk.document_id] = row[0] if row else "Unknown"

        # Get knowledge base name
        if chunk.knowledge_base_id not in kb_cache:
            kb_result = await db.execute(
                select(KnowledgeBase.name).where(KnowledgeBase.id == chunk.knowledge_base_id)
            )
            row = kb_result.first()
            kb_cache[chunk.knowledge_base_id] = row[0] if row else "Unknown"

        results.append({
            "content": chunk.content,
            "score": round(score, 4),
            "document": doc_cache[chunk.document_id],
            "knowledge_base": kb_cache[chunk.knowledge_base_id],
            "chunk_index": chunk.chunk_index,
        })

    return results


async def get_relevant_context(
    db: AsyncSession,
    user_id: str,
    query: str,
    max_tokens: int = 2000,
) -> str:
    """Get relevant knowledge base context for a chat message.

    This is the main integration point for the chat service:
    1. Search across all active knowledge bases
    2. Format results into a context string
    3. Respect max_tokens budget

    Returns a formatted string for inclusion in the system prompt.
    """
    results = await search_knowledge(db, user_id, query, limit=10)
    if not results:
        return ""

    # Filter by a minimum relevance threshold
    MIN_SCORE = 0.3
    relevant = [r for r in results if r["score"] >= MIN_SCORE]
    if not relevant:
        return ""

    parts: list[str] = []
    token_budget = max_tokens
    for r in relevant:
        entry = f"[From: {r['document']}] {r['content']}"
        entry_tokens = _estimate_tokens(entry)
        if entry_tokens > token_budget:
            # Try to fit a truncated version
            if token_budget > 100:
                # Rough truncation
                words = entry.split()
                max_words = int(token_budget / 1.3)
                entry = " ".join(words[:max_words]) + "..."
                parts.append(entry)
            break
        parts.append(entry)
        token_budget -= entry_tokens

    if not parts:
        return ""

    return "Based on your uploaded documents:\n" + "\n\n".join(parts)


# --- Document Listing ---

async def list_documents(db: AsyncSession, kb_id: str, user_id: str) -> list[KnowledgeDocument]:
    """List all documents in a knowledge base."""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(
            KnowledgeDocument.knowledge_base_id == kb_id,
            KnowledgeDocument.user_id == user_id,
        )
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return list(result.scalars().all())


async def get_document(db: AsyncSession, doc_id: str, user_id: str) -> KnowledgeDocument | None:
    """Get a single document."""
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_document(db: AsyncSession, doc_id: str, user_id: str) -> bool:
    """Delete a document and its chunks (via CASCADE), then update KB counts."""
    result = await db.execute(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.user_id == user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        return False

    kb_id = doc.knowledge_base_id
    await db.delete(doc)
    await db.commit()

    # Update knowledge base counts
    await _update_kb_counts(db, kb_id)
    return True
