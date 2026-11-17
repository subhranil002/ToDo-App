import csv
import io
import pytest
import mongomock
import database
from app import app


@pytest.fixture
def mock_mongo(monkeypatch):
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["myDatabase"]
    monkeypatch.setattr(database.mongo, "db", mock_db)
    return mock_db


@pytest.fixture
def client(mock_mongo):
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def seed_export_tasks(mock_db):
    tasks = [
        {
            "title": "Quarterly Audit Wrap-up",
            "description": "Auditing",
            "datetime": "2025-10-20 14:30:00",
            "priority": "high",
            "status": "Done"
        },
        {
            "title": "Firewall Rule Hardening",
            "description": "Hardening",
            "datetime": "2025-10-21 09:15:00",
            "priority": "medium",
            "status": "Done"
        },
        {
            "title": "SAN Storage Rebalancing",
            "description": "Rebalancing",
            "datetime": "2025-10-22 11:00:00",
            "priority": "low",
            "status": "Done"
        },
        {
            "title": "Active Backlog Grooming",
            "description": "Grooming",
            "datetime": "2025-10-23 10:00:00",
            "priority": "high",
            "status": "Pending"
        },
    ]
    mock_db.inventory.insert_many(tasks)


def test_bulk_export_completed_tasks_rfc4180(client, mock_mongo):
    """ARCH-S2-AC01: Successful Bulk Export of Completed Tasks in RFC 4180 Format"""
    seed_export_tasks(mock_mongo)
    response = client.get("/export/completed/csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers.get("Content-Type", "")
    assert "attachment; filename=" in response.headers.get("Content-Disposition", "")

    csv_text = response.get_data(as_text=True)
    reader = list(csv.reader(io.StringIO(csv_text)))

    # Verify Header
    assert reader[0] == ["Title", "Status", "Priority"]

    # Verify 3 completed records exported (Pending record excluded)
    data_rows = reader[1:]
    assert len(data_rows) == 3

    titles = [row[0] for row in data_rows]
    assert "Quarterly Audit Wrap-up" in titles
    assert "Firewall Rule Hardening" in titles
    assert "SAN Storage Rebalancing" in titles
    assert "Active Backlog Grooming" not in titles


def test_bulk_export_proper_quoting_rfc4180(client, mock_mongo):
    """ARCH-S2-AC03: Proper Quoting of Fields Containing Commas, Double Quotes, and Newlines"""
    mock_mongo.inventory.insert_one({
        "title": 'Deploy "Hotfix 2", Patch System',
        "description": "Critical patch",
        "datetime": "2025-10-24 12:00:00",
        "priority": "medium",
        "status": "Done"
    })

    response = client.get("/export/completed/csv")
    assert response.status_code == 200

    csv_text = response.get_data(as_text=True)
    reader = list(csv.reader(io.StringIO(csv_text)))

    assert len(reader) == 2
    assert reader[1][0] == 'Deploy "Hotfix 2", Patch System'
    assert reader[1][1] == "Done"
    assert reader[1][2] == "medium"


def test_bulk_export_zero_completed_tasks(client, mock_mongo):
    """ARCH-S2-AC04: Bulk Export When Zero Completed Tasks Exist"""
    mock_mongo.inventory.insert_one({
        "title": "Active Backlog Grooming",
        "description": "Grooming",
        "datetime": "2025-10-23 10:00:00",
        "priority": "high",
        "status": "Pending"
    })

    response = client.get("/export/completed/csv")
    assert response.status_code == 200

    csv_text = response.get_data(as_text=True)
    reader = list(csv.reader(io.StringIO(csv_text)))

    assert len(reader) == 1
    assert reader[0] == ["Title", "Status", "Priority"]


@pytest.mark.parametrize("method", ["post", "put", "delete", "patch"])
def test_rejection_of_non_get_methods(client, method):
    """ARCH-S2-AC05: Rejection of Non-GET HTTP Methods"""
    client_method = getattr(client, method)
    response = client_method("/export/completed/csv")
    assert response.status_code == 405


def test_proper_unicode_utf8_preservation(client, mock_mongo):
    """ARCH-S2-AC08: Proper Unicode and UTF-8 Character Preservation"""
    intl_tasks = [
        {
            "title": "Vérification des journaux système",
            "status": "Done",
            "priority": "high",
            "datetime": "2025-10-24 10:00:00"
        },
        {
            "title": "日本語タスクのバックアップ処理",
            "status": "Done",
            "priority": "medium",
            "datetime": "2025-10-24 10:05:00"
        },
        {
            "title": "Мониторинг кластера базы данных",
            "status": "Done",
            "priority": "low",
            "datetime": "2025-10-24 10:10:00"
        },
    ]
    mock_mongo.inventory.insert_many(intl_tasks)

    response = client.get("/export/completed/csv")
    assert response.status_code == 200

    csv_bytes = response.data
    # Must decode cleanly as UTF-8
    decoded_text = csv_bytes.decode("utf-8")
    assert "Vérification des journaux système" in decoded_text
    assert "日本語タスクのバックアップ処理" in decoded_text
    assert "Мониторинг кластера базы данных" in decoded_text
