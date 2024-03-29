"""
TODO:

How to handle CVEs that have always been there?
How to handle CVEs that are never remediated?
"""

# Standard lib
from typing import Dict, Tuple, Set, List
import os
from datetime import datetime
import multiprocess as mp

# 3rd party
import pandas as pd
from pymongo import MongoClient, ASCENDING
from pymongo.cursor import Cursor
from gryft.scanning.report import GrypeReport
from gryft.scanning.types import CVE
from tqdm import tqdm


MONGO_URI = os.environ["MONGO_URI"]


def init_active_table(first_scan: Dict) -> Dict[str, datetime]:
    report = GrypeReport.from_json(first_scan["grype"])
    return {cve: first_scan["scan_start"] for cve in report.cves}


def append_remediation(cve: Dict, scan: Dict, first_seen_at: datetime,
                       df:pd.DataFrame) -> pd.DataFrame:
    row = {
        "id": cve.id,
        "severity": cve.severity,
        "registry": scan["registry"],
        "repository": scan["repository"],
        "tag": scan["tag"],
        "labels": scan["labels"],
        "first_seen_at": first_seen_at,
        "remediated_at": scan["scan_start"]
    }
    row_df = pd.DataFrame(row, index=[0])
    return pd.concat([df, row_df], ignore_index=True)


def get_remediated_cves(discovered: set[CVE], active: Dict[CVE, datetime]) -> Set[CVE]:
    past = set(active.keys())
    return past - discovered


def get_new_cves(discovered: set[CVE], active: Dict[CVE, datetime]) -> Set[CVE]:
    past = set(active.keys())
    return discovered - past

    
def fetch_images() -> List[str]:
    client = MongoClient(MONGO_URI)
    collection = client["gallery"]["images"]
    cursor = collection.find()
    images = list(cursor)
    client.close()
    return images
    
def fetch_scans(registry: str, repository: str, tag: str
        )-> Tuple[int, Cursor]:
    client = MongoClient(MONGO_URI)
    collection = client["gallery"]["scans"]
    query = {"registry": registry,
             "repository": repository,
             "tag": tag}
    cursor = collection.find({"registry": registry,
            "repository": repository,
            "tag": tag},
            ).sort([("scan_start", ASCENDING)])
    scans = list(cursor)
    client.close()
    return list(scans)


def parse_image(image: Dict) -> Tuple[str, str, str]:
    return image["registry"], image["repository"], image["tag"]


def get_image_remediations(image: Dict) -> pd.DataFrame:
    """
    Currently this method assumes all CVEs in the first scan were
    introduced at that exact moment in time, and all CVEs after the last scan
    are immediately remediated.
    """
    active = None
    last_scan = None
    rem_df = pd.DataFrame()

    registry, repository, tag = parse_image(image)

    scans = fetch_scans(registry, repository,
                        tag)

    for s in scans:
        if active is None:
            active = init_active_table(s)
        else:
            report = GrypeReport.from_json(s)
            discovered_cves = set(report.cves)
            remediated_cves = get_remediated_cves(discovered_cves, active)
            for cve in remediated_cves:
                rem_df = append_remediation(cve, s,
                        first_seen_at=active[cve], df=rem_df)
                del active[cve]
            new_cves = get_new_cves(discovered_cves, active)
            for cve in new_cves:
                active[cve] = s["scan_start"]
        last_scan = s

    # Consider all remaining CVEs in the table "remediated"
    if active is not None:
        for cve, first_seen_at in active.items():
            rem_df = append_remediation(cve, last_scan,
                    first_seen_at=first_seen_at, df=rem_df)

    csv_name = f"{registry}-{repository}-{tag}.csv"
    rem_df.to_csv(os.path.join("remediations", csv_name), index=False)


if __name__ == "__main__":
    images = fetch_images()
    with mp.Pool(mp.cpu_count()) as pool:
        list(tqdm(pool.imap_unordered(get_image_remediations, images),
                  total=len(images)))
