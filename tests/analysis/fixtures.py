# Stadnard lib
from typing import Dict
from datetime import datetime

# 3rd party
import pytest
from gryft.scanning.types import CVE, Component


@pytest.fixture
def cve_001_python() -> CVE:
    component = Component("python3.10", "3.10", "python")
    return CVE("CVE_001", "critical", "fixed", component)


@pytest.fixture
def cve_001_python_dict() -> Dict:
    return {
        "id": "CVE_001",
        "severity": "critical",
        "fix_state": "fixed",
        "component": {
            "name": "python3.10",
            "version": "3.10",
            "type_": "python"
        }
    }


@pytest.fixture
def cve_001_jre() -> CVE:
    component = Component("jre", "10.3", "java")
    return CVE("CVE_001", "critical", "fixed", component)


@pytest.fixture
def cve_001_jre_dict() -> Dict:
    return {
        "id": "CVE_001",
        "severity": "critical",
        "fix_state": "fixed",
        "component": {
            "name": "jre",
            "version": "10.3",
            "type_": "java"
        }
    }


@pytest.fixture
def cve_001_none() -> Dict:
    component = Component(None, None, None)
    return CVE("CVE_001", "critical", "fixed", component)


@pytest.fixture
def cve_001_none_dict() -> Dict:
    return {
        "id": "CVE_001",
        "severity": "critical",
        "fix_state": "fixed",
    }


@pytest.fixture
def small_scan(cve_001_python_dict) -> Dict:
    return {
        "scan_start": datetime(2024, 1, 1, 2),
        "registry": "cgr.dev",
        "repository": "chainguard/python",
        "tag": "latest",
        "cves": [cve_001_python_dict]
    }


@pytest.fixture
def empty_scan() -> Dict:
    return {
        "scan_start": datetime(2024, 1, 1, 2),
        "registry": "cgr.dev",
        "repository": "chainguard/python",
        "latest": "tag",
        "cves": []
    }
