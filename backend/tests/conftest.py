import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from jose import jwt

from main import app
from database.core import get_session
from features.auth.service import SECRET_KEY, ALGORITHM, get_password_hash
from entities.user import User

# 1) In-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


# 2) Create / drop tables around each test session
@pytest.fixture(autouse=True, scope="session")
def initialize_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


# 3) Provide a Session-local to every test
@pytest.fixture()
def session():
    with Session(engine) as sess:
        yield sess


# 4) Override get_session dependency so FastAPI uses our in-mem DB
@pytest.fixture()
def client(session):
    def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# 5) Make a test user in the DB and mint a JWT
@pytest.fixture()
def test_user(session):
    user = User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("password123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture()
def test_token(test_user):
    # same payload as your real login
    to_encode = {"sub": test_user.id}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# 6) Helper to set auth header
@pytest.fixture()
def auth_client(client, test_token):
    client.headers.update({"Authorization": f"Bearer {test_token}"})
    return client
