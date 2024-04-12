# Standard lib
from typing import Set, Dict, List, Iterable
from datetime import datetime
from dataclasses import dataclass

# 3rd party

# Local
from gryft.scanning.types import CVE, Component


@dataclass(frozen=True)
class Scan:
    scan_start: datetime
    cves: List[CVE]


@dataclass(frozen=True)
class Remediation:
    cve: CVE
    first_seen_at: datetime
    remediated_at: datetime


def _validate_scan(scan: Dict, prev_scan: Dict):
    if prev_scan is None:
        return
    if scan["scan_start"] <= prev_scan["scan_start"]:
        raise ValueError(f"A scan was provided out of order")
    for key in ["registry", "repository", "tag"]:
        if scan[key] != prev_scan[key]:
            raise ValueError(f"Scans from multiple images were provided")


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


def find_image_remediations(scans: Iterable,
                            include_preexisting: bool=False,
                            include_residual: bool=False) -> List[Remediation]:
    """
    Finds the remediations in the scans of a single image.
    All scans must come from the same image. Scans must be provided
    in order by scan time.
    """
    tracking_table = {}
    last_scan = None
    remediations = []

    for s in scans:
        _validate_scan(s, last_scan)

        # No need to init tracking table with a scan if not
        # tracking preexisting CVEs
        if tracking_table is None and include_preexisting:
            tracking_table = _init_tracking_table(s)
            continue
        
        # Get the CVEs of the current scan
        observed = _extract_cves(s)

        # Calculate remediations and store in a running list
        # Delete remediated CVEs from the tracking table
        remediated_cves = _get_remediated_cves(observed, tracking_table)
        for cve in remediated_cves:
            r = Remediation(cve, tracking_table[cve], s["scan_start"])
            remediations.append(r)
            del tracking_table[cve]
        
        # Of the remaining CVEs, update the tacking table]
        # with newly discovered CVEs
        new_cves = _get_new_cves(observed, tracking_table)
        for cve in new_cves:
            tracking_table[cve] = s["scan_start"]
        last_scan = s

    if (tracking_table is not None) and include_residual:
        #Consider all remaining CVEs in the table "remediated"
        for cve, first_seen_at in tracking_table.items():
            # TODO: Update this to label non remediated CVEs
            r = Remediation(cve, first_seen_at, last_scan["scan_start"])
            remediations.append(r)

    return remediations