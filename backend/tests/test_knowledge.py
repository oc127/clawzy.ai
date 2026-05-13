"""Tests for Knowledge Base service and API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeBase
from app.services.knowledge_service import (
    chunk_text,
    cosine_similarity,
    create_knowledge_base,
    delete_knowledge_base,
    extract_text,
    get_knowledge_base,
    list_knowledge_bases,
    update_knowledge_base,
)


# ---------------------------------------------------------------------------
#  Knowledge Service unit tests (use `db` fixture directly)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_knowledge_base(db: AsyncSession, test_user):
    """Create a KB and verify its fields."""
    kb = await create_knowledge_base(
        db, test_user.id, "My KB", description="A test knowledge base"
    )
    assert kb.id is not None
    assert kb.name == "My KB"
    assert kb.description == "A test knowledge base"
    assert kb.user_id == test_user.id
    assert kb.is_active is True
    assert kb.document_count == 0


@pytest.mark.asyncio
async def test_list_knowledge_bases(db: AsyncSession, test_user):
    """Create 2 KBs, list them, verify count."""
    await create_knowledge_base(db, test_user.id, "KB One")
    await create_knowledge_base(db, test_user.id, "KB Two")

    kbs = await list_knowledge_bases(db, test_user.id)
    assert len(kbs) == 2
    names = {kb.name for kb in kbs}
    assert "KB One" in names
    assert "KB Two" in names


@pytest.mark.asyncio
async def test_get_knowledge_base(db: AsyncSession, test_user):
    """Create then retrieve a KB by id."""
    kb = await create_knowledge_base(db, test_user.id, "Retrievable KB")
    fetched = await get_knowledge_base(db, kb.id, test_user.id)
    assert fetched is not None
    assert fetched.id == kb.id
    assert fetched.name == "Retrievable KB"


@pytest.mark.asyncio
async def test_update_knowledge_base(db: AsyncSession, test_user):
    """Update a KB's name and is_active flag."""
    kb = await create_knowledge_base(db, test_user.id, "Original Name")
    updated = await update_knowledge_base(
        db, kb.id, test_user.id, name="Updated Name", is_active=False
    )
    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_delete_knowledge_base(db: AsyncSession, test_user):
    """Create then delete a KB, verify it is gone."""
    kb = await create_knowledge_base(db, test_user.id, "To Delete")
    deleted = await delete_knowledge_base(db, kb.id, test_user.id)
    assert deleted is True

    gone = await get_knowledge_base(db, kb.id, test_user.id)
    assert gone is None


@pytest.mark.asyncio
async def test_chunk_text():
    """chunk_text with multi-paragraph text returns chunks with content and chunk_index."""
    text = (
        "This is the first paragraph with enough words to be meaningful. "
        "It discusses various topics related to artificial intelligence and its impact.\n\n"
        "This is the second paragraph which covers different ground entirely. "
        "It talks about software engineering best practices and testing.\n\n"
        "The third paragraph wraps up the document with concluding remarks. "
        "We have covered a lot of ground in this brief document."
    )
    chunks = chunk_text(text)
    assert len(chunks) >= 1
    for i, chunk in enumerate(chunks):
        assert "content" in chunk
        assert "chunk_index" in chunk
        assert chunk["chunk_index"] == i
        assert len(chunk["content"]) > 0


@pytest.mark.asyncio
async def test_chunk_text_empty():
    """Empty string returns empty list."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []


@pytest.mark.asyncio
async def test_cosine_similarity():
    """Test cosine similarity: identical=1.0, orthogonal=0.0, zero vector=0.0."""
    # Identical vectors
    v = [1.0, 2.0, 3.0]
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    # Orthogonal vectors
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert abs(cosine_similarity(a, b) - 0.0) < 1e-6

    # Zero vector
    zero = [0.0, 0.0, 0.0]
    non_zero = [1.0, 2.0, 3.0]
    assert cosine_similarity(zero, non_zero) == 0.0
    assert cosine_similarity(non_zero, zero) == 0.0


@pytest.mark.asyncio
async def test_extract_text_utf8():
    """Plain text extraction from UTF-8 bytes."""
    raw = "Hello, this is a test document with UTF-8 content."
    result = extract_text(raw.encode("utf-8"), "text")
    assert result == raw


# ---------------------------------------------------------------------------
#  Knowledge API tests (use `client` + `auth_headers` fixtures)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_kb_api(client, auth_headers):
    """POST /api/v1/lucy/knowledge with name, check 201."""
    resp = await client.post(
        "/api/v1/lucy/knowledge",
        json={"name": "API Test KB", "description": "Created via API"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "API Test KB"
    assert data["description"] == "Created via API"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_kb_api(client, auth_headers):
    """GET /api/v1/lucy/knowledge returns a list."""
    # Create one first
    await client.post(
        "/api/v1/lucy/knowledge",
        json={"name": "List Test KB"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/lucy/knowledge", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_kb_api(client, auth_headers):
    """GET /api/v1/lucy/knowledge/{id}, check 200."""
    create_resp = await client.post(
        "/api/v1/lucy/knowledge",
        json={"name": "Get Test KB"},
        headers=auth_headers,
    )
    kb_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/lucy/knowledge/{kb_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == kb_id
    assert resp.json()["name"] == "Get Test KB"


@pytest.mark.asyncio
async def test_delete_kb_api(client, auth_headers):
    """DELETE /api/v1/lucy/knowledge/{id}, check 204."""
    create_resp = await client.post(
        "/api/v1/lucy/knowledge",
        json={"name": "Delete Test KB"},
        headers=auth_headers,
    )
    kb_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/lucy/knowledge/{kb_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Confirm it is gone
    get_resp = await client.get(f"/api/v1/lucy/knowledge/{kb_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_kb_unauthorized(client):
    """POST without auth returns 401."""
    resp = await client.post(
        "/api/v1/lucy/knowledge",
        json={"name": "Should Fail"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_search_empty(client, auth_headers):
    """POST /api/v1/lucy/knowledge/search with mocked embedding returns empty results."""
    fake_embedding = [0.1] * 1536  # text-embedding-3-small dimension

    mock_response = MagicMock()
    mock_response.data = [{"embedding": fake_embedding}]

    with patch("app.services.knowledge_service.litellm.aembedding", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = mock_response
        resp = await client.post(
            "/api/v1/lucy/knowledge/search",
            json={"query": "test query"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # No documents uploaded, so results should be empty
    assert len(data) == 0
