"""
Performs a test scan over a set of provided images.
"""

# Standard lib
import argparse

# 3rd party
import pandas as pd
from gryft.scanning.image import Image
from gryft.scanning.scanner import ImageScanner


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("images",
                        help="The path to the images CSV file")
    return parser.parse_args()


def handle_error(e):
    print(f"ERROR: {str(e)}")


def main():
    args = parse_args()
    df = pd.read_csv(args.images)
    
    images = []
    for _, row in df.iterrows():
        img = Image(registry=row["registry"],
                      repository=row["repository"],
                      tag=row["tag"])
        images.append(img)

    reports = ImageScanner().scan(images, nprocs=4, error_cb=handle_error)
    print(f"Generated {len(reports)} reports")


if __name__ == "__main__":
    main()