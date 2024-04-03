"""
Lists MCR chiselled images.
"""

# Standard lib
from typing import List, Dict
import re

# 3rd party
from sh import ErrorReturnCode, crane


def has_arch(tag: str) -> bool:
    suffix = tag.split("-")[-1]
    return suffix in ["amd64", "arm32v7", "arm64v8"]


def is_chiseled_tag(tag: str) -> bool:
    """
    Criteria for valid tag:

    1) Contains "chiseled"
    2) Does not contain "preview"
    3) Starts with #.#- (ex: 8.1- ...)
    4) Is not architecture specific
    """
    if ("chiseled" in tag) and ("preview" not in tag):
        match = re.match("^\\d\.\\d\-", tag)
        return (match is not None) and (not has_arch(tag))
    return False


def print_image(image: Dict):
    publisher = "microsoft"
    registry = "mcr.microsoft.com"
    repository = image["repository"]
    tag = image["tag"]
    labels = ",".join(image["labels"])
    print(f"{publisher} {registry} {repository} {tag} {labels}")


def main() -> List[Dict]:
    registry = "mcr.microsoft.com"
    images = []

    for image in ["runtime", "runtime-deps", "aspnet"]:
        repository = f"dotnet/{image}"
        try:
            tags = crane("ls", f"{registry}/{repository}").split("\n")
            for tag in tags:
                if is_chiseled_tag(tag):
                    print_image({
                        "repository": repository,
                        "tag": tag,
                        "labels": ["chiselled", "mcr-dotnet"]
                    })
        except ErrorReturnCode:
            pass

        repository = f"dotnet/nightly/{image}"
        try:
            tags = crane("ls", f"{registry}/{repository}").split("\n")
            for tag in tags:
                if is_chiseled_tag(tag):
                    images.append({
                        "registry": "mcr.microsoft.com",
                        "repository": repository,
                        "tag": "tag",
                        "labels": ["chiseled", "mcr-dotnet"]
                    })
        except ErrorReturnCode:
            pass

    return images


if __name__ == "__main__":
    main()
