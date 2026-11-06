#!/usr/bin/env python3
"""Copy gate location CSVs with only lat,lon,gate,darpa_id columns."""

import argparse
import csv
from pathlib import Path
import re
import sys


def convert_locations(source):
    match = re.fullmatch(r"gate-(\d+)-locations\.csv", source.name)
    if not match:
        raise ValueError("expected a filename like gate-2-locations.csv")
    gate = match.group(1)
    columns = ["lat", "lon", "darpa_id"]
    with source.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing = set(columns) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        rows = [{**{key: row[key] for key in columns}, "gate": gate} for row in reader]

    output = source.with_name(f"{source.stem}-converted.csv")
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["lat", "lon", "gate", "darpa_id"])
        writer.writeheader()
        writer.writerows(rows)
    return output, len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths", nargs="*", type=Path, default=[Path(".")],
        help="input files or directories to search recursively (default: current directory)",
    )
    args = parser.parse_args()
    sources = set()
    for path in args.paths:
        if path.is_dir():
            sources.update(path.rglob("*-locations.csv"))
        elif path.is_file():
            sources.add(path)
        else:
            parser.error(f"no such file or directory: {path}")

    failed = False
    for source in sorted(sources):
        try:
            output, count = convert_locations(source)
        except (OSError, ValueError, csv.Error) as error:
            print(f"{source}: {error}", file=sys.stderr)
            failed = True
            continue
        print(f"{output}: {count} locations")
    if not sources:
        print("No *-locations.csv files found.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
