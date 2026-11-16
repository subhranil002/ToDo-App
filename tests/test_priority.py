import pytest
import mongomock
import database
from app import app


@pytest.fixture
def mock_mongo(monkeypatch):
    """Fixture to mock mongo.db.inventory with an in-memory mongomock collection."""
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["myDatabase"]
    monkeypatch.setattr(database.mongo, "db", mock_db)
    return mock_db


@pytest.fixture
def client(mock_mongo):
    """Flask test client fixture."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def seed_tasks(mock_db):
    """Seed test tasks across multiple priority tiers."""
    tasks = [
        {
            "title": "Production Incident 1",
            "description": "Sev1 outage",
            "datetime": "2025-10-24 10:00:00",
            "priority": "high",
            "status": "Pending"
        },
        {
            "title": "Vendor Review",
            "description": "Vendor SLA check",
            "datetime": "2025-10-24 10:05:00",
            "priority": "low",
            "status": "Pending"
        },
        {
            "title": "Database Backup Check",
            "description": "Verify backup dumps",
            "datetime": "2025-10-24 10:10:00",
            "priority": "medium",
            "status": "Pending"
        },
        {
            "title": "Infrastructure Patch",
            "description": "Kernel patch",
            "datetime": "2025-10-24 10:15:00",
            "priority": "high",
            "status": "Pending"
        },
        {
            "title": "Archive Stale Accounts",
            "description": "Cleanup jobs",
            "datetime": "2025-10-24 10:20:00",
            "priority": "low",
            "status": "Done"
        },
    ]
    mock_db.inventory.insert_many(tasks)


def test_filter_pending_tasks_by_high_priority(client, mock_mongo):
    """ARCH-S1-AC01: Filter Pending Tasks by High Priority"""
    seed_tasks(mock_mongo)
    response = client.get("/?priority=high")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Production Incident 1" in html
    assert "Infrastructure Patch" in html
    assert "Vendor Review" not in html
    assert "Database Backup Check" not in html


@pytest.mark.parametrize("priority,expected_title", [
    ("low", "Vendor Review"),
    ("medium", "Database Backup Check"),
])
def test_filter_pending_tasks_by_low_and_medium(client, mock_mongo, priority, expected_title):
    """ARCH-S1-AC02: Filter Pending Tasks by Low and Medium Priorities"""
    seed_tasks(mock_mongo)
    response = client.get(f"/?priority={priority}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert expected_title in html
    assert "Production Incident 1" not in html


@pytest.mark.parametrize("raw_input", ["HIGH", "High", "hIgH", "  high  "])
def test_case_insensitive_priority_parameter(client, mock_mongo, raw_input):
    """ARCH-S1-AC03: Case-Insensitive Priority Parameter Normalization"""
    seed_tasks(mock_mongo)
    response = client.get(f"/?priority={raw_input}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Production Incident 1" in html
    assert "Infrastructure Patch" in html


@pytest.mark.parametrize("invalid_input", ["critical", "urgent", "12345", "ultra_high", "undefined"])
def test_fallback_behavior_for_invalid_priority(client, mock_mongo, invalid_input):
    """ARCH-S1-AC04: Fallback Behavior for Invalid or Unrecognized Priority Inputs"""
    seed_tasks(mock_mongo)
    response = client.get(f"/?priority={invalid_input}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Should display all records without crashing
    assert "Production Incident 1" in html
    assert "Vendor Review" in html
    assert "Database Backup Check" in html


def test_backward_compatibility_omitted_priority(client, mock_mongo):
    """ARCH-S1-AC05: Backward Compatibility for Omitted Priority Parameter"""
    seed_tasks(mock_mongo)
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Production Incident 1" in html
    assert "Vendor Review" in html


@pytest.mark.parametrize("payload", [
    "[$ne]=null",
    '{"$gt": ""}',
    "' or '1'='1",
    "'; db.tasks.drop(); --",
])
def test_defensive_handling_malicious_nosql_injection(client, mock_mongo, payload):
    """ARCH-S1-AC06: Defensive Handling of Malicious NoSQL Injection in Priority Parameter"""
    seed_tasks(mock_mongo)
    response = client.get(f"/?priority={payload}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Safe fallback to all records
    assert "Production Incident 1" in html


def test_empty_priority_query_parameter_handling(client, mock_mongo):
    """ARCH-S1-AC07: Empty Priority Query Parameter Handling"""
    seed_tasks(mock_mongo)
    response = client.get("/?priority=")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Production Incident 1" in html
    assert "Vendor Review" in html
