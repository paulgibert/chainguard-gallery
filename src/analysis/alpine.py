"""
Functions for detecting if a Chainguard image is
alpine-based. These images should be omitted from
the analysis.
"""

# Standard lib
from typing import List, Dict, Tuple

# 3rd party
from gryft.scanning.image import Image
from gryft.scanning.scanner import ImageScanner

# Local


def print_error(e: Exception):
    print(e)


def list_cgr_alpine(images: List[Dict]) -> List[Image]:
    images = [Image(img["registry"], img["repository"], img["tag"]) for img in images
              if img["registry"] == "cgr.dev"]
    snapshots = ImageScanner().scan(images, error_cb=print_error)
    return [snap.image for snap in snapshots
            if (snap.distro == "alpine")
            and (snap.image.registry == "cgr.dev")]
    