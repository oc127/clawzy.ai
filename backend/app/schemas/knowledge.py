from datetime import datetime

from pydantic import BaseModel


class KnowledgeBaseCreate(BaseModel):
    name: str
    description: str | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str | None
    document_count: int
    total_chunks: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SearchResult(BaseModel):
    content: str
    score: float
    document: str
    knowledge_base: str
    chunk_index: int


class SearchRequest(BaseModel):
    query: str
    kb_ids: list[str] | None = None
    limit: int = 5
