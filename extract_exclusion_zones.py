#!/usr/bin/env python3
"""Combine Exclusion Zone polygons from course CSVs into latitude,longitude,name."""

import argparse
import csv
import math
from pathlib import Path
import re
import sys


def exclusion_points(source):
    """Return points for matching rows, preserving names and coordinate precision."""
    points = []
    with source.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        columns = {name.strip().lower(): name for name in reader.fieldnames or []}
        # Ignore empty files and exports that contain no source geometry.
        if not {"name", "wkt"} <= columns.keys():
            return points
        for row in reader:
            name = row.get(columns["name"]) or ""
            if "Exclusion Zone" not in name:
                continue
            polygon = row.get(columns["wkt"]) or ""
            match = re.fullmatch(
                r"\s*POLYGON\s*\(\s*\(([^()]*)\)\s*\)\s*",
                polygon, re.IGNORECASE,
            )
            if not match:
                raise ValueError(f"{name!r}: expected a single-ring WKT POLYGON")
            for coordinate in match.group(1).split(","):
                values = coordinate.split()
                if len(values) != 2:
                    raise ValueError(
                        f"{name!r}: expected longitude latitude: {coordinate!r}"
                    )
                longitude, latitude = values
                if not all(math.isfinite(float(value)) for value in values):
                    raise ValueError(f"{name!r}: invalid coordinate: {coordinate!r}")
                points.append((latitude, longitude, name))
    return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory", nargs="?", type=Path, default=Path("."),
        help="directory to search recursively for CSV files (default: current directory)",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("exclusion-zones.csv"),
        help="combined output CSV (default: exclusion-zones.csv in current directory)",
    )
    args = parser.parse_args()
    if not args.directory.is_dir():
        parser.error(f"not a directory: {args.directory}")

    points = []
    try:
        for source in sorted(args.directory.rglob("*.csv")):
            if source.resolve() == args.output.resolve():
                continue
            try:
                points.extend(exclusion_points(source))
            except (OSError, ValueError, csv.Error) as error:
                raise ValueError(f"{source}: {error}") from error
        # Read and validate all inputs before replacing the previous export.
        with args.output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["latitude", "longitude", "name"])
            writer.writerows(points)
    except (OSError, ValueError, csv.Error) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"{args.output}: {len(points)} points")
    return 0


if __name__ == "__main__":
    sys.exit(main())
