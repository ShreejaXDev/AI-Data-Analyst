import os
import sys
import io
import pytest
import pandas as pd
from fastapi.testclient import TestClient

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app
from backend.services.session_service import session_store

client = TestClient(app)


def test_health_endpoint():
    """1. Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI Data Analyst"


def test_csv_upload_valid():
    """2 & 5. Test valid CSV upload and dataset metadata profiler structure."""
    sales_path = os.path.join(BASE_DIR, "data", "sales.csv")
    with open(sales_path, "rb") as f:
        file_content = f.read()

    response = client.post(
        "/api/upload",
        files={"file": ("sales.csv", file_content, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()

    assert "dataset_id" in data
    assert data["filename"] == "sales.csv"
    assert data["rows"] == 10
    assert data["columns"] == 4
    assert set(data["column_names"]) == {"Product", "Region", "Sales", "Quantity"}
    assert data["duplicate_rows"] == 0
    assert isinstance(data["missing_values"], dict)
    assert isinstance(data["dtypes"], dict)
    assert len(data["preview"]) == 5


def test_invalid_file_extension():
    """3. Test rejection of unsupported file extension."""
    response = client.post(
        "/api/upload",
        files={"file": ("notes.txt", b"some text content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only .csv files are supported" in response.json()["detail"]


def test_empty_csv_upload():
    """4. Test rejection of empty CSV file."""
    response = client.post(
        "/api/upload",
        files={"file": ("empty.csv", b"", "text/csv")}
    )
    assert response.status_code == 400
    assert "Uploaded CSV file is empty" in response.json()["detail"]


def test_chat_missing_dataset():
    """6 (Error). Test chat endpoint with invalid/missing dataset_id."""
    response = client.post(
        "/api/chat",
        json={"dataset_id": "invalid-uuid-1234", "message": "What is the average sales?"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_chat_missing_message():
    """Validation test for empty message in chat endpoint."""
    # First upload a dataset to get a valid dataset_id
    sales_path = os.path.join(BASE_DIR, "data", "sales.csv")
    with open(sales_path, "rb") as f:
        upload_resp = client.post(
            "/api/upload",
            files={"file": ("sales.csv", f.read(), "text/csv")}
        )
    dataset_id = upload_resp.json()["dataset_id"]

    response = client.post(
        "/api/chat",
        json={"dataset_id": dataset_id, "message": "   "}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_chat_and_multi_turn_persistence():
    """6 & 7. Test chat endpoint and multi-turn transformation persistence."""
    titanic_path = os.path.join(BASE_DIR, "data", "train.csv")
    with open(titanic_path, "rb") as f:
        upload_resp = client.post(
            "/api/upload",
            files={"file": ("train.csv", f.read(), "text/csv")}
        )

    assert upload_resp.status_code == 200
    dataset_id = upload_resp.json()["dataset_id"]
    assert upload_resp.json()["missing_values"]["Age"] == 177

    # Turn 1: Transform missing values in Age
    chat1_resp = client.post(
        "/api/chat",
        json={"dataset_id": dataset_id, "message": "Fill missing Age values with the median"}
    )
    assert chat1_resp.status_code == 200
    res1_data = chat1_resp.json()
    assert res1_data["success"] is True
    assert "answer" in res1_data

    # Turn 2: Query missing values on active persistent DataFrame
    chat2_resp = client.post(
        "/api/chat",
        json={"dataset_id": dataset_id, "message": "How many missing values are in Age now?"}
    )
    assert chat2_resp.status_code == 200
    res2_data = chat2_resp.json()
    assert res2_data["success"] is True
    assert "0" in res2_data["answer"]


def test_chart_generation_and_retrieval():
    """8. Test chart request response and chart file retrieval."""
    sales_path = os.path.join(BASE_DIR, "data", "sales.csv")
    with open(sales_path, "rb") as f:
        upload_resp = client.post(
            "/api/upload",
            files={"file": ("sales.csv", f.read(), "text/csv")}
        )

    dataset_id = upload_resp.json()["dataset_id"]

    chat_resp = client.post(
        "/api/chat",
        json={"dataset_id": dataset_id, "message": "Compare total sales across regions and create a chart"}
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["success"] is True

    # If chart was generated, test retrieving it via GET /api/charts/{chart_id}
    if chat_data["chart"]:
        chart_url = chat_data["chart"]
        chart_id = chart_url.split("/")[-1]
        get_chart_resp = client.get(f"/api/charts/{chart_id}")
        assert get_chart_resp.status_code == 200
        assert get_chart_resp.headers["content-type"] == "image/png"


def test_source_csv_remains_untouched():
    """9. Verify original source CSV file on disk is completely untouched."""
    orig_path = os.path.join(BASE_DIR, "data", "train.csv")
    df_orig = pd.read_csv(orig_path)
    assert df_orig["Age"].isnull().sum() == 177, "Original train.csv must remain untouched with 177 missing Age values"
