# Standard lib
from typing import Dict
import os
import json
from datetime import datetime
import time

# 3rd Party
from pymongo import MongoClient
from sh import grype, ErrorReturnCode
import functions_framework
from cloudevents.http.event import CloudEvent


MONGO_USER = os.environ.get("MONGO_USER", None)
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", None)
MONGO_CLUSTER_ADDR = os.environ.get("MONGO_CLUSTER_ADDR", None)
MONGO_APP_NAME = os.environ.get("MONGO_APP_NAME", None)
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "gallery") #TODO: Remove default. Set environment
MONGO_COLLECTION_NAME = os.environ.get("MONGO_COLLECTION_NAME", "scans")


def validate_event_data(data: Dict):
    # TODO: Implement event data validation
    pass


def scan_image(registry: str, repository: str, tag: str) -> Dict:
    endpoint = f"{registry}/{repository}:{tag}"
    try:
        # TODO: Add timeout
        json_str = grype(endpoint, "--output", "json")
        return json.loads(json_str)
    except ErrorReturnCode as e:
        raise RuntimeError(f"Error running grype: {e.stderr}")


def connect_to_mongo() -> MongoClient:
    uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER_ADDR}/?retryWrites=true&w=majority&appName={MONGO_APP_NAME}"
    return MongoClient(uri)

    
def store_scan(scan: Dict, client: MongoClient, **kwargs):
    print(MONGO_DB_NAME)
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]

    document = {
        "grype": scan
    }

    for key, value in kwargs.items():
        document[key] = value

    collection.insert_one(document)


@functions_framework.cloud_event
def process_image(event: CloudEvent):
    validate_event_data(event.data)
    
    registry = event.data["registry"]
    repository = event.data["repository"]
    tag = event.data["tag"]
    scan_start = event.data["scan_start"]

    try:
        start_time = time.time()
        scan = scan_image(registry, repository, tag)
        scan_duration = time.time() - start_time
        
        client = connect_to_mongo()
        store_scan(scan, client,
                   scan_start=scan_start,
                   scan_duration=scan_duration,
                   registry=registry,
                   repository=repository,
                   tag=tag)

    except Exception as e:
        print(f"An error occured: {str(e)}")
        raise

    