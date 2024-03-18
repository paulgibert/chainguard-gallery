# Standard lib
import json
from datetime import datetime

# 3rd party
import pytest
from cloudevents.http import CloudEvent
from sh import ErrorReturnCode_1
from pymongo import MongoClient

# Local
from functions.process_image.main import scan_image, store_scan, process_image


DB_NAME = "gallery"
COLLECTION_NAME = "scans"


def test__scan_image__success():
    scan = scan_image("cgr.dev", "chainguard/python", "latest")
    for key in ["matches", "source", "distro", "descriptor"]:
        assert key in scan.keys()


def test__scan_image__grype_fails(monkeypatch):
    def bad_grype(*args):
        raise ErrorReturnCode_1(b"some cmd", b"", b"Something bad happened")

    monkeypatch.setattr("functions.process_image.main.grype", bad_grype)

    with pytest.raises(RuntimeError):
        scan = scan_image("cgr.dev", "chainguard/python", "latest")


def test__scan_image__json_decode_fails(monkeypatch):
    def bad_grype(*args):
        return "{some invalid json string"

    monkeypatch.setattr("functions.process_image.main.grype", bad_grype)

    with pytest.raises(json.JSONDecodeError):
        scan = scan_image("cgr.dev", "chainguard/python", "latest")


@pytest.fixture
def client():
    client = MongoClient("localhost", 27017)
    db = client[DB_NAME]
    db[COLLECTION_NAME]

    yield client

    client.drop_database(DB_NAME)
    client.close()


def test__store_scan__success(client):
    scan = {
        "results": [1, 2, 3]
    }
    
    store_scan(scan, client, key1="one", key2="two")
    
    document = client[DB_NAME][COLLECTION_NAME].find_one()
    assert document is not None
    assert document["grype"] == scan
    assert document["key1"] == "one"
    assert document["key2"] == "two"


def test__process_image__success(monkeypatch, client):
    def mock_connect_to_mongo() -> MongoClient:
        return client
    
    monkeypatch.setattr("functions.process_image.main.MONGO_DB_NAME",
                        DB_NAME)
    monkeypatch.setattr("functions.process_image.main.MONGO_COLLECTION_NAME",
                        COLLECTION_NAME)
    monkeypatch.setattr("functions.process_image.main.connect_to_mongo",
                        mock_connect_to_mongo)
    
    attributes = {
        "type": None,
        "source": None
    }

    data = {
        "scan_start": datetime(2023, 1, 1, 12),
        "registry": "cgr.dev",
        "repository": "chainguard/python",
        "tag": "latest"
    }

    event = CloudEvent(attributes, data)
    process_image(event)

    document = client[DB_NAME][COLLECTION_NAME].find_one()
    assert document is not None
    assert "grype" in document.keys()
    assert "scan_duration" in document.keys()
    for key, value in data.items():
        assert key in document.keys()
        assert document[key] == value
