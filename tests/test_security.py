import csv
import io
import pytest
import mongomock
import database
from app import app, sanitize_csv_cell


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


@pytest.mark.parametrize("raw_input,expected_sanitized", [
    ("=cmd|' /C calc'!A0", "'=cmd|' /C calc'!A0"),
    ("+SUM(1+1)*cmd", "'+SUM(1+1)*cmd"),
    ("-10+20", "'-10+20"),
    ("@SUM(A1:A10)", "'@SUM(A1:A10)"),
    ('=HYPERLINK("http://evil.com")', '\'=HYPERLINK("http://evil.com")'),
    ("\t=2+5", "'\t=2+5"),
    ("\r-5+10", "'\r-5+10"),
    ("Safe Normal Task Title", "Safe Normal Task Title"),
    ("", ""),
    (None, ""),
])
def test_sanitize_csv_cell_direct(raw_input, expected_sanitized):
    """Test unit sanitization logic against OWASP formula injection vectors."""
    assert sanitize_csv_cell(raw_input) == expected_sanitized


@pytest.mark.parametrize("malicious_title,sanitized_title", [
    ("=cmd|' /C calc'!A0", "'=cmd|' /C calc'!A0"),
    ("+SUM(1+1)*cmd", "'+SUM(1+1)*cmd"),
    ("-10+20", "'-10+20"),
    ("@SUM(A1:A10)", "'@SUM(A1:A10)"),
    ('=HYPERLINK("http://evil.com")', '\'=HYPERLINK("http://evil.com")'),
])
def test_neutralization_of_spreadsheet_formula_injection(client, mock_mongo, malicious_title, sanitized_title):
    """ARCH-S2-AC02: Neutralization of Spreadsheet Formula Injection Characters"""
    mock_mongo.inventory.insert_one({
        "title": malicious_title,
        "description": "Exploit vector payload",
        "datetime": "2025-10-24 15:00:00",
        "priority": "high",
        "status": "Done"
    })

    response = client.get("/export/completed/csv")
    assert response.status_code == 200

    csv_text = response.get_data(as_text=True)
    reader = list(csv.reader(io.StringIO(csv_text)))

    assert len(reader) == 2
    row_title = reader[1][0]
    assert row_title == sanitized_title
    assert row_title.startswith("'")
