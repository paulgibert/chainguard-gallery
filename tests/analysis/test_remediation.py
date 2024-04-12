# Standard lib
from typing import Dict
from datetime import datetime, timedelta
import copy

# 3rd party
import pytest
from gryft.scanning.types import CVE, Component

# Local
import src.analysis.remediation as rem
from fixtures import (cve_001_python,
                      cve_001_python_dict,
                      cve_001_jre,
                      cve_001_jre_dict,
                      cve_001_none,
                      cve_001_none_dict,
                      small_scan,
                      empty_scan)


# _validate_scan

def test___validate_scan__valid(small_scan):
    prev_scan = copy.deepcopy(small_scan)
    prev_scan["scan_start"] -= timedelta(hours=1)
    rem._validate_scan(small_scan, prev_scan)


def test___validate_scan__out_of_order(small_scan):
    prev_scan = copy.deepcopy(small_scan)
    prev_scan["scan_start"] += timedelta(hours=1)
    with pytest.raises(ValueError):
        rem._validate_scan(small_scan, prev_scan)


@pytest.mark.parametrize("field", [
    "registry", "repository", "tag"])
def test___validate_scan__bad_field(field, small_scan):
    prev_scan = copy.deepcopy(small_scan)
    prev_scan["scan_start"] -= timedelta(hours=1)
    small_scan[field] = "different"
    with pytest.raises(ValueError):
        rem._validate_scan(small_scan, prev_scan)


# _extract_cves

def test___extract_cves(cve_001_python_dict, cve_001_jre_dict,
                        cve_001_python, cve_001_jre):
    cves = rem._extract_cves({"cves": [cve_001_python_dict, cve_001_jre_dict]})
    assert cves == {cve_001_python, cve_001_jre}


def test___extract_cves__no_comp(cve_001_none_dict, cve_001_none):
    cves = rem._extract_cves({"cves": [cve_001_none_dict]})
    assert cves == {cve_001_none}


# _init_tracking_table

def test___init_tracking_table(small_scan, cve_001_python):
    table = rem._init_tracking_table(small_scan)
    assert list(table.keys()) == [cve_001_python]


def test___init_tracking_table__len(small_scan):
    table = rem._init_tracking_table(small_scan)
    assert len(table.keys()) == 1


def test___init_tracking_table__empty_scan(empty_scan):
    table = rem._init_tracking_table(empty_scan)
    assert table == {}


# _get_remediated_cves

def test___get_remediated_cves(cve_001_python, cve_001_jre):
    tracking_table = {cve_001_python: datetime(2024, 1, 1, 0),
                      cve_001_jre: datetime(2024, 1, 2, 11)}
    observed = {cve_001_jre}
    rems = rem._get_remediated_cves(observed, tracking_table)
    assert list(rems)[0] == cve_001_python


def test___get_remediated_cves__no_rems(cve_001_python):
    tracking_table = {cve_001_python: datetime(2024, 1, 1, 0)}
    observed = {cve_001_python}
    rems = rem._get_remediated_cves(observed, tracking_table)
    assert len(rems) == 0


# _get_new_cves

def test___get_new_cves(cve_001_python, cve_001_jre):
    tracking_table = {cve_001_python: datetime(2024, 1, 1, 0)}
    observed = {cve_001_jre}
    new = rem._get_new_cves(observed, tracking_table)
    assert list(new)[0] == cve_001_jre


def test___get_new_cves__no_new():
    tracking_table = {cve_001_python: datetime(2024, 1, 1, 0)}
    observed = {cve_001_python}
    new = rem._get_new_cves(observed, tracking_table)
    assert len(new) == 0
