# Standard lib
from typing import Dict, Tuple, List
import os
import json
from datetime import datetime, timezone
import logging
from dataclasses import dataclass, asdict

# 3rd Party
# import google.cloud.logging
from pymongo import MongoClient
from sh import grype, ErrorReturnCode
from gryft.scanning.report import GrypeReport
from flask import Flask, request, jsonify


MONGO_DB_NAME = "gallery"
MONGO_COLLECTION_NAME = "cves"
MONGO_URI = os.environ.get("MONGO_URI", None)

app = Flask(__name__)


@dataclass
class ScanArgs:
    registry: str
    repository: str
    tag: str
    labels: List[str]


def parse_args(json_data: Dict) -> ScanArgs:
    if json_data is None:
        raise ValueError("No JSON data was provided")
    
    registry = json_data.get("registry", None)
    if registry is None:
        raise ValueError("Missing `registry` field")
    
    repository = json_data.get("repository", None)
    if repository is None:
        raise ValueError("Missing `repository` field")
    
    tag = json_data.get("tag", None)
    if tag is None:
        raise ValueError("Missing `tag` field")
    
    labels = json_data.get("labels", None)
    if labels is None:
        raise ValueError("Missing `labels` field"
                         )
    return ScanArgs(registry=registry, repository=repository,
                    tag=tag, labels=labels)


def error(e: Exception, status_code: int) -> Tuple[Dict, int]:
    logging.error("Error: " + str(e))
    return jsonify({"error": str(e)}), status_code


def scan_image(args: ScanArgs) -> Dict:
    endpoint = f"{args.registry}/{args.repository}:{args.tag}"
    try:
        # TODO: Add timeout
        json_str = grype(endpoint, "--output", "json")
        return json.loads(json_str)
    except ErrorReturnCode as e:
        raise RuntimeError(f"Error running grype: {e.stderr}")


def store_scan(scan: Dict, scan_start: datetime, scan_duration: float, args: ScanArgs, client: MongoClient):
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]

    report = GrypeReport.from_json(scan)
    cves = [asdict(cve) for cve in report.cves]

    document = {
        "scan_start": scan_start,
        "scan_duration_secs": scan_duration,
        "cves": cves
    }

    for key, value in asdict(args).items():
        document[key] = value
    collection.insert_one(document)


@app.route("/", methods=["POST"])
def main():
    try:
        args = parse_args(request.json)
        scan_start = datetime.now(timezone.utc)
        scan = scan_image(args)
        scan_end = datetime.now(timezone.utc)
        scan_duration = (scan_end - scan_start).total_seconds()
        
        if MONGO_URI is None:
            raise ValueError("MONGO_URI not provided")
        client = MongoClient(MONGO_URI)

        store_scan(scan, scan_start, scan_duration, args, client)

    except Exception as e:
        return error(e, 400)
    
    return jsonify({"message": "success"}), 200
