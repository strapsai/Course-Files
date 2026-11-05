#!/usr/bin/env python3
"""Export Course Boundary polygons as latitude,longitude,altitude CSV files."""

import argparse
import csv
import math
from pathlib import Path
import re
import sys


def boundary_points(source):
    """Read a single-ring WKT polygon, keeping the original coordinate precision."""
    with source.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        columns = {name.strip().lower(): name for name in reader.fieldnames or []}
        if not {"name", "wkt"} <= columns.keys():
            raise ValueError("input must contain Name and WKT columns")
        boundaries = [
            row for row in reader
            if (row.get(columns["name"]) or "").strip() == "Course Boundary"
        ]
    if len(boundaries) != 1:
        raise ValueError(
            f"expected one Course Boundary row; found {len(boundaries)}"
        )

    polygon = boundaries[0].get(columns["wkt"]) or ""
    match = re.fullmatch(
        r"\s*POLYGON\s*\(\s*\(([^()]*)\)\s*\)\s*", polygon, re.IGNORECASE
    )
    if not match:
        raise ValueError("Course Boundary must be a single-ring WKT POLYGON")

    points = []
    for coordinate in match.group(1).split(","):
        values = coordinate.split()
        if len(values) != 2:
            raise ValueError(f"expected longitude latitude: {coordinate!r}")
        longitude, latitude = values
        if not all(math.isfinite(float(value)) for value in values):
            raise ValueError(f"invalid coordinate: {coordinate!r}")
        points.append((latitude, longitude, 0))
    return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files", nargs="+", type=Path,
        help="input course CSV files; writes <input-stem>-boundary.csv beside each",
    )
    args = parser.parse_args()
    failed = False
    for source in args.files:
        output = source.with_name(f"{source.stem}-boundary.csv")
        try:
            points = boundary_points(source)
            with output.open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["latitude", "longitude", "altitude"])
                writer.writerows(points)
        except (OSError, ValueError, csv.Error) as error:
            print(f"{source}: {error}", file=sys.stderr)
            failed = True
            continue
        print(f"{output}: {len(points)} points")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
