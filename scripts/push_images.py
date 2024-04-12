"""
Pushes a CSV file of images to MongoDB for routine scanning.

Run `python push_images.py --help` for usage.
"""

# Standard lib
from typing import Dict, List
import os
import csv
import argparse

# 3rd party
from pymongo import MongoClient


MONGO_URI = os.environ["MONGO_URI"]
MONGO_DB_NAME = "gallery"
MONGO_COLLECTION_NAME = "images"


def image_str(image: Dict) -> str:
    return f"{image['registry']}/{image['repository']}:{image['tag']}"


def fetch_image_names() -> List[str]:
    client = MongoClient(MONGO_URI)
    images = client[MONGO_DB_NAME][MONGO_COLLECTION_NAME].find()
    return [image_str(img) for img in images]


def is_in(sample: Dict, image_names: List[str]) -> bool:
    return image_str(sample) in image_names


def push_images(images: List[Dict]):
    client = MongoClient(MONGO_URI)
    client[MONGO_DB_NAME][MONGO_COLLECTION_NAME].insert_many(images)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file")
    csv_file = parser.parse_args().csv_file

    existing_images = fetch_image_names()

    images = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                continue # Skip headers
            registry = row[1]
            repository = row[2]
            tag = row[3]
            img = {
                "publisher": row[0],
                "registry": registry,
                "repository": repository,
                "tag": tag,
                "labels": row[4].split(",")
            }
            if is_in(img, existing_images):
                print(f"WARNING: Duplicate image {image_str(img)}")
            else:
                images.append(img)

    push_images(images)


if __name__ == "__main__":
    main()