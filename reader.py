# Copyright (C) 2026 Yusuke Notomi
# SPDX-License-Identifier: 0BSD

"""Read data files without importing AMADEUS or interpreting scientific units."""
from __future__ import annotations

import csv
from pathlib import Path

import yaml


def read_config(path: Path) -> dict:
    with Path(path).open(encoding="utf-8-sig") as stream:
        value = yaml.safe_load(stream)
    if not isinstance(value, dict):
        raise ValueError("The configuration must be a YAML mapping.")
    return value


def read_results(path: Path, preview_limit: int = 20) -> dict:
    if preview_limit < 0:
        raise ValueError("preview_limit must be nonnegative.")
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream)
        first_row = next(rows, None)
        if first_row is None:
            raise ValueError("The CSV file is empty.")
        count = 0
        preview = []
        for row in rows:
            count += 1
            if len(preview) < preview_limit:
                preview.append(row)
    return {"first_row": first_row, "records_after_first_row": count, "preview": preview}
