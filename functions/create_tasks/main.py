# Standard lib
from typing import Dict
import os
import json
from datetime import datetime

# 3rd party
from pymongo import MongoClient
from pymongo.cursor import Cursor
import functions_framework
from google.cloud import pubsub_v1


MONGO_USER = os.environ.get("MONGO_USER", None)
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", None)
MONGO_CLUSTER_ADDR = os.environ.get("MONGO_CLUSTER_ADDR", None)
MONGO_APP_NAME = os.environ.get("MONGO_APP_NAME", None)
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "gallery") #TODO: Remove default. Set environment
MONGO_COLLECTION_NAME = os.environ.get("MONGO_COLLECTION_NAME", "scans")
pubsub_project_id = os.environ["PROJECT_ID"]
pubsub_topic_id = os.environ["TOPIC_ID"]


# TODO: Remove repeated code
def connect_to_mongo() -> MongoClient:
    uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER_ADDR}/?retryWrites=true&w=majority&appName={MONGO_APP_NAME}"
    return MongoClient(uri)


def fetch_images() -> Cursor:
    client = connect_to_mongo()
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    return collection.find()


def validate_image(image: Dict):
    # TODO: Image validation
    pass


@functions_framework.http
def create_tasks(_):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(pubsub_project_id, pubsub_topic_id)

    for image in fetch_images():
        validate_image(image)
        data = {
            "scan_start": datetime.utcnow(),
            "registry": image["registry"],
            "repository": image["repository"],
            "tag": image["tag"]
        }
        data = json.dumps(data).encode("utf-8")
        future = publisher.publish(topic_path, data)
