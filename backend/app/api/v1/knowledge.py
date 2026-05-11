"""Knowledge Base API — CRUD for knowledge bases, document upload, and semantic search."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.knowledge import (
    DocumentResponse,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    SearchRequest,
    SearchResult,
)
from app.services import knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lucy/knowledge", tags=["lucy-knowledge"])

# Supported file extensions and their type mappings
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "pdf",
    ".md": "markdown",
    ".txt": "text",
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".tsx": "code",
    ".jsx": "code",
    ".java": "code",
    ".go": "code",
    ".rs": "code",
    ".c": "code",
    ".cpp": "code",
    ".h": "code",
    ".css": "code",
    ".html": "code",
    ".json": "code",
    ".yaml": "code",
    ".yml": "code",
    ".toml": "code",
    ".xml": "code",
    ".sql": "code",
    ".sh": "code",
    ".rb": "code",
    ".php": "code",
    ".swift": "code",
    ".kt": "code",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _get_file_type(filename: str) -> str:
    """Determine file_type from filename extension."""
    for ext, file_type in SUPPORTED_EXTENSIONS.items():
        if filename.lower().endswith(ext):
            return file_type
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported file type. Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS.keys()))}",
    )


# ---------------------------------------------------------------------------
#  Search (defined before /{kb_id} routes to avoid path parameter conflicts)
# ---------------------------------------------------------------------------


@router.post("/search", response_model=list[SearchResult])
async def search_knowledge(
    body: SearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic search across the user's knowledge bases."""
    results = await knowledge_service.search_knowledge(
        db, user.id, body.query, body.kb_ids, body.limit
    )
    return results


# ---------------------------------------------------------------------------
#  Knowledge Base CRUD
# ---------------------------------------------------------------------------


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    body: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base for the current user."""
    kb = await knowledge_service.create_knowledge_base(
        db, user.id, body.name, body.description
    )
    return kb


@router.get("", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all knowledge bases for the current user."""
    return await knowledge_service.list_knowledge_bases(db, user.id)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single knowledge base by ID."""
    kb = await knowledge_service.get_knowledge_base(db, kb_id, user.id)
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )
    return kb


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    body: KnowledgeBaseUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a knowledge base's name, description, or active status."""
    kb = await knowledge_service.update_knowledge_base(
        db, kb_id, user.id, body.name, body.description, body.is_active
    )
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )
    return kb


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge base and all its documents/chunks."""
    deleted = await knowledge_service.delete_knowledge_base(db, kb_id, user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )


# ---------------------------------------------------------------------------
#  Document Management
# ---------------------------------------------------------------------------


@router.post("/{kb_id}/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to a knowledge base for processing and chunking."""
    # Validate the knowledge base exists and belongs to the user
    kb = await knowledge_service.get_knowledge_base(db, kb_id, user.id)
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # Validate filename is present
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Validate file type
    file_type = _get_file_type(file.filename)

    # Read file bytes and validate size
    content_bytes = await file.read()
    if len(content_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    if len(content_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    doc = await knowledge_service.upload_document(
        db, kb_id, user.id, file.filename, content_bytes, file_type
    )
    return doc


@router.get("/{kb_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    kb_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents in a knowledge base."""
    # Validate the knowledge base exists and belongs to the user
    kb = await knowledge_service.get_knowledge_base(db, kb_id, user.id)
    if kb is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )
    return await knowledge_service.list_documents(db, kb_id, user.id)


@router.get("/{kb_id}/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    kb_id: str,
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single document's details."""
    doc = await knowledge_service.get_document(db, doc_id, user.id)
    if doc is None or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.delete("/{kb_id}/documents/{doc_id}", status_code=204)
async def delete_document(
    kb_id: str,
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its chunks from a knowledge base."""
    doc = await knowledge_service.get_document(db, doc_id, user.id)
    if doc is None or doc.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    await knowledge_service.delete_document(db, doc_id, user.id)
