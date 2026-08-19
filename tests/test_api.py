import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Isolated in-memory SQLite DB for tests — never touches tasks.db on disk,
# and each test run starts from a clean schema. StaticPool keeps a single
# connection alive so the in-memory DB isn't wiped between sessions.
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


def test_create_task():
    response = client.post(
        "/tasks",
        json={"title": "Learn Kubernetes", "description": "Prepare for CKA"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Learn Kubernetes"
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data


def test_get_tasks():
    client.post("/tasks", json={"title": "Task A"})
    client.post("/tasks", json={"title": "Task B"})
    response = client.get("/tasks")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert "Task A" in titles
    assert "Task B" in titles


def test_get_single_task():
    created = client.post("/tasks", json={"title": "Single Task"}).json()
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Single Task"


def test_get_task_not_found():
    response = client.get("/tasks/99999")
    assert response.status_code == 404


def test_update_task():
    created = client.post("/tasks", json={"title": "Original"}).json()
    response = client.put(
        f"/tasks/{created['id']}", json={"completed": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["title"] == "Original"  # unchanged fields stay as-is


def test_update_task_not_found():
    response = client.put("/tasks/99999", json={"completed": True})
    assert response.status_code == 404


def test_delete_task():
    created = client.post("/tasks", json={"title": "To Delete"}).json()
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204

    follow_up = client.get(f"/tasks/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_task_not_found():
    response = client.delete("/tasks/99999")
    assert response.status_code == 404


def test_create_task_missing_title_is_invalid():
    response = client.post("/tasks", json={"description": "no title here"})
    assert response.status_code == 422


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.content
