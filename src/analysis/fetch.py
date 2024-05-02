"""
Helper functions for fetching data from gallery.
"""

# Standard lib
from typing import List, Dict, Tuple
import os
from datetime import datetime

# 3rd party
from pymongo import MongoClient, ASCENDING, DESCENDING

# Local


def fetch_images() -> List[Dict]:
    """
    Pull the list of images from mongo and save.
    """
    with MongoClient(os.environ["MONGO_URI"]) as client:
        collection = client["gallery"]["images"]
        return list(collection.find())
    

def global_first_scan() -> datetime:
    """
    Fetch the datetime of the first scan in the dataset.
    """
    with MongoClient(os.environ["MONGO_URI"]) as client:
        collection = client["gallery"]["cves"]
        scan = collection.find_one({}, sort=[("scan_start", ASCENDING)])
        return scan["scan_start"]


def image_first_scan(image: Dict) -> datetime:
    """
    Fetch the datetime of the first scan in the dataset
    for a given image.
    """
    with MongoClient(os.environ["MONGO_URI"]) as client:
        collection = client["gallery"]["cves"]
        scan = collection.find_one({"registry": image["registry"],
                                    "repository": image["repository"],
                                    "tag": image["tag"]}, sort=[("scan_start", ASCENDING)])
        return scan["scan_start"]


def images_first_scan() -> Dict[Tuple[str, str], datetime]:
    """
    Fetch the datetime of the first scan in the dataset
    across all images. Optimization of image_first_scan to
    perform a single query for all images.
    """
    with MongoClient(os.environ["MONGO_URI"]) as client:
        collection = client["gallery"]["cves"]

        pipeline = [
            {
                "$group": {
                    "_id": {"registry": "$registry", "repository": "$repository"},
                    "first_scan": {"$min": "$scan_start"}
                }
            }
        ]

        results = collection.aggregate(pipeline)
        return {(d["_id"]["registry"], d["_id"]["repository"]): d["first_scan"]
                for d in results}


def global_latest_scan() -> datetime:
    """
    Fetch the datetime of the latest scan in the dataset.
    """
    with MongoClient(os.environ["MONGO_URI"]) as client:
        collection = client["gallery"]["cves"]
        scan = collection.find_one({}, sort=[("scan_start", DESCENDING)])
        return scan["scan_start"]
