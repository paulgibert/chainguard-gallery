# Standard lib
from typing import Dict
import os
import csv
import argparse
import json

# 3rd party
from sh import docker, ErrorReturnCode
from pymongo import MongoClient


MONGO_URI = os.environ["MONGO_URI"]
MONGO_DB_NAME = "gallery"
MONGO_COLLECTION_NAME = "images"

# MAX_IMAGE_SZ = 100000000


# def get_image_size(registry: str, repository: str, tag: str) -> int:
#     json_str = docker("inspect", f"{registry}/{repository}:{tag}")
#     json_data = json.loads(json_str)
#     return json_data[0]["Size"]


def push_images(images: Dict):
    client = MongoClient(MONGO_URI)
    client[MONGO_DB_NAME][MONGO_COLLECTION_NAME].insert_many(images)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    csv_file = parser.parse_args().csv_file

    images = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                continue # Skip headers
            registry = row[1]
            repository = row[2]
            tag = row[3]
            images.append({
                "publisher": row[0],
                "registry": registry,
                "repository": repository,
                "tag": tag,
                "labels": row[4].split(",")
            })

    push_images(images)


if __name__ == "__main__":
    main()