"""
This is THE file that contains the remediation detection
algorithm. It contains a few classes for representing a scan
and remediation plus help functions for running the algorithm.

Algorithm outline:

Let T be a `Dict` where:
    key = A CVE match
    value = A timestamp for when that match was first observed

Let S be a scan that contains an image name, list of CVE matches, and timestamp.

Let T - S be all of the CVEs in T but not in S. These CVEs have disappeared or "remediatied".
Let S - T be all of the CVEs in S but not in T. These CVEs are newly discovered in this scan.

Group all scans by image and sort by timestamp starting with the earliest scan.


Let R be the set of remedations for a given image.

R = []
for each S in image:
    remediated = T - S
    discovered = S - T
    
    for CVE in remediated:
        R += (CVE, T[CVE], S.timestamp) # A tuple of the CVE and first_seen_at, and remediated_at times.
        del T[CVE]

    for CVE in discovered:
        T[CVE] = S.timestamp

return R

Exceptions:

The above pseudocode is the bulk of the algorithm, but there are two special cases.

Case 1: First scan:
    If we are processing the first scan, we have no idea how long the discovered CVEs have
    been in the image. We initializes T with these CVEs but with NULL timestamps.

Case 2: Last scan
    If we are processing the last scan, we have no idea when these CVEs will be remediated.
    We add these CVEs to R but with NULL remediated_at timestamps.
"""

# Standard lib
from typing import Set, Dict, List, Iterable
import os
from datetime import datetime
from dataclasses import dataclass

# 3rd party
from gryft.scanning.types import CVE, Component
import pandas as pd
from pymongo import MongoClient, ASCENDING
import multiprocess as mp
from tqdm import tqdm

# Local
from .stat import RemediationTable, Remediation, concat
from .fetch import fetch_images, fetch_chainguard_images


@dataclass(frozen=True)
class Scan:
    """
    Represents a scan.

    scan_start (datetime): The start of the scan.
    cves (List[CVE]): The list of CVEs observed in the scan.
    """
    scan_start: datetime
    cves: List[CVE]


def _validate_scan(scan: Dict, prev_scan: Dict):
    """
    Validates the ordering and contents of a scan.
    """
    if prev_scan is None:
        return
    if scan["scan_start"] <= prev_scan["scan_start"]:
        raise ValueError(f"A scan was provided out of order")
    
    # This check creates performance issues for some weird reason

    # for key in ["registry", "repository", "tag"]:
    #     if scan[key] != prev_scan[key]:
    #         raise ValueError(f"Scans from multiple images were provided")


def _extract_cves(scan: Dict) -> Set[CVE]:
    """
    Extracts CVEs from a scan.
    """
    cves = []
    for cve in scan["cves"]:
        # Handle case where component is not provided
        component_dict = {"name": None, "version": None, "type_": None}
        component_dict = cve.get("component", component_dict)
        component = Component(**component_dict)
        
        cve = CVE(id=cve["id"],
                  severity=cve["severity"],
                  fix_state=cve["fix_state"],
                  component=component)
        cves.append(cve)
    return set(cves)


def _init_tracking_table(scan: Dict) -> Dict[CVE, datetime]:
    """
    Initializes the tracking table with a scan.
    """
    cves = _extract_cves(scan)
    return {c: scan["scan_start"] for c in cves}


def _get_remediated_cves(observed: Set[CVE], tracking_table: Dict[CVE, datetime]) -> Set[CVE]:
    """
    Determines the remediated CVEs as the set difference between the currently
    tracked CVEs and the CVEs that are observed in the current scan.

    The CVEs in this difference were once observed but are no longer. These
    CVEs are considered 'remediated'.
    """
    tracking = set(tracking_table.keys())
    return tracking - observed


def _get_new_cves(observed: Set[CVE], tracking_table: Dict[CVE, datetime]) -> Set[CVE]:
    """
    Determines new, not-seen-before CVEs as the set difference between the CVEs
    that are observed in the current scan and the CVEs being tracked.

    The CVEs in this difference were not observed in the past but are observed now.
    These CVEs are considered 'new'.
    """
    tracking = set(tracking_table.keys())
    return observed - tracking


def _collect_image_remediations(scans: Iterable) -> List[Remediation]:
    """
    Finds the remediations in the scans of a single image.
    All scans must come from the same image. Scans must be provided
    in order by scan time.

    Args:
        scans (Iterable): The scans to search for remediations in.
    
    Returns:
        The list of remediations as a `List[Remediation]`.
    """
    tracking_table = None
    cves_at_start = []
    prev_scan = None
    remediations = []

    for s in scans:
        _validate_scan(s, prev_scan)

        if tracking_table is None:
            cves_at_start = _extract_cves(s)
            tracking_table = _init_tracking_table(s)
            continue
        
        # Get the CVEs of the current scan
        observed = _extract_cves(s)

        # Calculate remediations and store in a running list
        # Delete remediated CVEs from the tracking table
        remediated_cves = _get_remediated_cves(observed, tracking_table)
        for cve in remediated_cves:
            first_seen_at = tracking_table[cve]
            if cve in cves_at_start:
                first_seen_at = None
            r = Remediation(cve=cve,
                            first_seen_at=first_seen_at,
                            remediated_at=s["scan_start"])
            remediations.append(r)
            del tracking_table[cve]
        
        # Of the remaining CVEs, update the tacking table]
        # with newly discovered CVEs
        new_cves = _get_new_cves(observed, tracking_table)
        for cve in new_cves:
            tracking_table[cve] = s["scan_start"]
        prev_scan = s

    # Handle remaining unremediated CVEs
    if (tracking_table is not None):
        for cve, first_seen_at in tracking_table.items():
            if cve in cves_at_start:
                first_seen_at = None
            r = Remediation(cve=cve,
                            first_seen_at=first_seen_at,
                            remediated_at=None)
            remediations.append(r)

    return remediations


def _image_handler(image: dict, client: MongoClient) -> pd.DataFrame:
    """
    Collects the remediations from an image's scans.
    """
    query = {
        "registry": image["registry"],
        "repository": image["repository"],
        "tag": image["tag"],
    }

    collection = client["gallery"]["cves"]
    scans = collection.find(query).sort([("scan_start", ASCENDING)])
    remediations = _collect_image_remediations(scans)
    return RemediationTable.from_remediations(image, remediations)


def fetch_remediations() -> RemediationTable:
    """
    Fetches all scans from gallery and computes remediations.

    Returns:
        A `RemediationTable` of the remediations found.
    """
    images = fetch_images()

    # Having some issues with Mongo and multiprocess requests
    # Use sync fetch for now
    # with mp.Pool(mp.cpu_count()) as pool:
    #     rtables = list(tqdm(pool.imap_unordered(_image_handler, images),
    #                     desc="Collecting remediations",
    #                     total=len(images)))
    rtables= []
    with MongoClient(os.environ["MONGO_URI"]) as client:
        for img in tqdm(images, desc="Collecting remediations"):
            rtables.append(_image_handler(img, client))
    return concat(rtables)


def fetch_chainguard_remediations() -> RemediationTable:
    """
    Fetches all Chainguard images scans from gallery and computes remediations.

    Returns:
        A `RemediationTable` of the remediations found.
    """
    images = fetch_chainguard_images()

    with mp.Pool(mp.cpu_count()) as pool:
        rtables = list(tqdm(pool.imap_unordered(_image_handler, images),
                        desc=f"Collecting remediations",
                        total=len(images)))
    
    return concat(rtables)