"""
Searches for and lists docker images.
See the Makefile for usage examples.
"""

# Standard lib
from typing import List, Dict, Tuple
import argparse
import re
import multiprocessing as mp

# 3rd party
import requests
from sh import ErrorReturnCode, crane
from yaspin import yaspin
from yaspin.spinners import Spinners
from tqdm import tqdm


def print_image(image: Dict):
    publisher = "docker"
    registry = "docker.io"
    repository = image["repository"]
    tag = image["tag"]
    labels = ",".join(image["labels"])
    print(f"{publisher} {registry} {repository} {tag} {labels}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("query",
                        help="The query to use when searching docker hub")
    parser.add_argument("--repository-prefix", "-p",
            required=False, default=None,
            help="Only list image repositories with this prefix")
    parser.add_argument("--image-filter", "-f",
            required=False, default=None,
            help="Only list image repositories with this filter. For example, \
            all docker official images have the `official` filter")
    parser.add_argument("--tags", "-t", required=False,
            default=None,
            help="Only list images with these tags. Tags should be spaced separated")
    return parser.parse_args()


def search_repositories(query: str, image_filter: str=None) -> List[str]:
    url = "https://hub.docker.com/api/content/v1/products/search"
    
    params = {
        "page_size": 25,
        "q": query
    }

    if image_filter:
        params["image_filter"] = image_filter

    headers = {
        "Accept": "application/json",
        "Search-Version": "v3"
    }

    repositories = []
    while url != "":
        r = requests.get(url, params=params, headers=headers)
        data = r.json()
        repositories += [d["name"] for d in data["summaries"]]
        url = data["next"]
    
    return repositories


def get_tags(repository: str) -> List[str]:
    try:
        return crane("ls", f"docker.io/{repository}").split("\n")
    except ErrorReturnCode:
        return []


def get_images_from_repository(inputs: Tuple[str, argparse.Namespace]) -> List[str]:
    repository, args = inputs
    images = []
    if args.repository_prefix:
        if re.match(f"^{args.repository_prefix}/", repository) is None:
            return []
    tags = get_tags(repository)
    if args.tags:
        for required_tag in args.tags.split(" "):
            if required_tag in tags:
                images.append(f"{repository}:{required_tag}")
    else:
        for t in tags:
            images.append(f"{repository}:{t}")
    return images


def flatten_list(l: List[List[str]]) -> List[str]:
    new_list = []
    for _l in l:
        new_list += _l
    return new_list


def main():
    args = parse_args()

    with yaspin(Spinners.line, text="Searching Docker"):
        repositories = search_repositories(args.query, args.image_filter)

    with mp.Pool(mp.cpu_count()) as pool:
        inputs = [(r, args) for r in repositories]
        images = list(tqdm(pool.imap_unordered(get_images_from_repository, inputs),
                desc=f"Collecting tags",
                total=len(repositories)))

    images = flatten_list(images)

    print() # Add an extra space between progress tracking UI and output
    for i in images:
        print(i)


if __name__ == "__main__":
    main()
