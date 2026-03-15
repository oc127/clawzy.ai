"""Shared test fixtures for the Clawzy backend test suite.

Uses SQLite in-memory via aiosqlite so tests run without PostgreSQL/Redis/Docker.
"""

import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.agent import Agent, AgentStatus
from app.models.skill import Skill
from app.models.credits import CreditTransaction, CreditReason
from app.models.subscription import Subscription, PlanType, SubStatus


# Use SQLite in-memory for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db():
    """Create tables and yield a session, then drop everything."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """FastAPI test client with DB override and docker_manager mock."""
    # Mock docker_manager globally to prevent real Docker calls
    mock_dm = MagicMock()
    mock_dm.create_agent_container.return_value = "fake-container-id"
    mock_dm.wait_for_healthy.return_value = True
    mock_dm.start_container.return_value = None
    mock_dm.stop_container.return_value = None
    mock_dm.remove_container.return_value = None
    mock_dm.generate_agent_config.return_value = {"model": "test"}

    # Disable rate limiting for tests
    from app.config import settings as _settings
    _settings.rate_limit_per_minute = 10000
    _settings.rate_limit_auth_per_minute = 10000

    # Import modules first so patch string paths resolve
    import app.services.agent_service as _agent_svc  # noqa: F811
    import app.core.docker_manager as _dm_mod  # noqa: F811
    from app.main import app as fastapi_app

    with patch.object(_agent_svc, "docker_manager", mock_dm), \
         patch.object(_dm_mod, "docker_manager", mock_dm), \
         patch("os.makedirs"), \
         patch("builtins.open", MagicMock()):

        async def override_get_db():
            yield db

        fastapi_app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        fastapi_app.dependency_overrides.clear()


# ─── Helpers ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """Create and return a test user with 500 credits."""
    user = User(
        email="test@clawzy.ai",
        password_hash=hash_password("password123"),
        name="Test User",
        credit_balance=500,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_token(test_user: User) -> str:
    """Return a valid access token for the test user."""
    return create_access_token(test_user.id)


@pytest_asyncio.fixture
async def auth_headers(test_user_token: str) -> dict:
    """Return authorization headers for test user."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest_asyncio.fixture
async def test_agent(db: AsyncSession, test_user: User) -> Agent:
    """Create a test agent."""
    agent = Agent(
        user_id=test_user.id,
        name="Test Agent",
        model_name="deepseek-chat",
        status=AgentStatus.running,
        ws_port=19000,
        container_id="fake-container-id",
        gateway_token="fake-token",
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def test_skill(db: AsyncSession) -> Skill:
    """Create a test skill."""
    skill = Skill(
        slug="web-search",
        name="Web Search",
        summary="Search the web",
        description="A skill that searches the web using Google.",
        category="search",
        tags=["web", "search"],
        install_count=100,
        is_featured=True,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@pytest_asyncio.fixture
async def second_user(db: AsyncSession) -> User:
    """Create a second user for ownership tests."""
    user = User(
        email="other@clawzy.ai",
        password_hash=hash_password("password456"),
        name="Other User",
        credit_balance=500,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
