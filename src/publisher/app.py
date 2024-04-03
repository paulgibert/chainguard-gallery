# Standard lib
from typing import Dict
import os
import json
from datetime import datetime
import uuid

# 3rd party
from google.cloud import tasks_v2
import google.oauth2.id_token
import google.auth.transport.requests
from pymongo import MongoClient
from pymongo.cursor import Cursor
from flask import Flask, jsonify

# Local
from monitor import ProgressMonitor, ProgressReport


MONGO_DB_NAME = "gallery"
MONGO_COLLECTION_NAME = "images"
MONGO_URI = os.environ["MONGO_URI"] # TODO: Better error handling for missing env

CLOUD_PROJECT_NAME = os.environ["CLOUD_PROJECT_NAME"] 
CLOUD_QUEUE_LOCATION = os.environ["CLOUD_QUEUE_LOCATION"]
CLOUD_QUEUE_NAME = os.environ["CLOUD_QUEUE_NAME"]

SCANNER_URL = os.environ["SCANNER_URL"]

app = Flask(__name__)


def get_auth_token() -> str:
    audience = SCANNER_URL
    client = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(client, audience)
    return id_token


def fetch_images(client) -> Cursor:
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    return collection.find()


def validate_image(image: Dict):
    # TODO: Image validation
    pass


def push_task(data: Dict, client):
    """
    Push `record` to cloud tasks.
    """
    task_id = str(uuid.uuid4())
    task_path = client.task_path(CLOUD_PROJECT_NAME, CLOUD_QUEUE_LOCATION, CLOUD_QUEUE_NAME, task_id)

    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {get_auth_token()}"
    }

    task = tasks_v2.Task(
        http_request=tasks_v2.HttpRequest(
        http_method=tasks_v2.HttpMethod.POST,
        url=SCANNER_URL,
        headers=headers,
        body=json.dumps(data).encode()),
        name=task_path
    )

    client.create_task(
        tasks_v2.CreateTaskRequest(
            parent=client.queue_path(CLOUD_PROJECT_NAME, CLOUD_QUEUE_LOCATION, CLOUD_QUEUE_NAME),
            task=task,
        )
    )


@app.route("/", methods=["POST"])
def main():
    images = fetch_images(MongoClient(MONGO_URI))
    for img in images:
        validate_image(img)
        scan_args = {
            "registry": img["registry"],
            "repository": img["repository"],
            "tag": img["tag"],
            "labels": img["labels"]
        }
        push_task(scan_args, tasks_v2.CloudTasksClient())

    return jsonify({"message": "success"}), 200
