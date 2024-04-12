# Standard lib
from datetime import datetime

# 3rd party
from pymongo import MongoClient
import requests


def test__scanner():
    payload = {
        "registry": "docker.io",
        "repository": "python",
        "tag": "latest",
        "labels": "test,debug"
    }

    response = requests.post("http://localhost:5000", json=payload)
    assert response.status_code == 200
    
    client = MongoClient("localhost", 27017)
    document = client["gallery"]["cves"].find_one()
    import pdb
    pdb.set_trace()
    assert document is not None
    assert "cves" in document.keys()
    assert "scan_duration_secs" in document.keys()
    assert "scan_start" in document.keys()

    for key, value in payload.items():
        assert key in document.keys()
        assert document[key] == value
    
    assert len(document["cves"]) > 0
    
    print(document["cves"][0])


if __name__ == "__main__":
    test__scanner()