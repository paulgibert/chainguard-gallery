# Standard lib
from datetime import datetime

# 3rd party
from pymongo import MongoClient
import requests


def test__scanner():
    payload = {
        "scan_start": datetime(2024, 3, 1, 5).isoformat(),
        "registry": "cgr.dev",
        "repository": "chainguard/python",
        "tag": "latest"
    }

    response = requests.post("http://localhost:5000", json=payload)
    assert response.status_code == 200
    
    client = MongoClient("localhost", 27017)
    document = client["gallery"]["scans"].find_one()
    
    assert document is not None
    assert "grype" in document.keys()
    assert "scan_duration" in document.keys()

    for key, value in payload.items():
        assert key in document.keys()
        assert document[key] == value
