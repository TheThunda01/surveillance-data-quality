"""Render saved public-audit denominators and window sensitivity, without fetching data."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path


def table(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def load_context(directory: Path):
    weekly = defaultdict(list)
    identities = set()
    for raw in table(directory / "weekly_audit.csv"):
        key = (raw["pathogen"], raw["week_end"])
        if key in identities:
            raise ValueError("Duplicate series-week in saved audit")
        identities.add(key)
        status = raw["status"]
        if status not in {"usable", "invalid", "suppressed", "unavailable", "absent_from_extract"}:
            raise ValueError("Unknown observation status")
        tests = int(raw["tests"]) if status == "usable" else None
        detections = int(raw["detections"]) if status == "usable" else None
        if status == "usable" and not 0 <= detections <= tests:
            raise ValueError("Usable counts must satisfy 0 <= detections <= tests")
        weekly[raw["pathogen"]].append({"week": date.fromisoformat(raw["week_end"]),
            "status": status, "tests": tests, "detections": detections})
    if not weekly:
        raise ValueError("No series in weekly audit")
    for rows in weekly.values():
        rows.sort(key=lambda row: row["week"])
        if any((b["week"] - a["week"]).days != 7 for a, b in zip(rows, rows[1:])):
            raise ValueError("Weekly table must retain explicit missing-week slots")

    windows = defaultdict(list)
    seen = set()
    inferred_as_of = None
    for raw in table(directory / "trailing_window_sensitivity.csv"):
        name = raw["pathogen"]
        days = int(raw["exclude_weeks_newer_than_days"])
        if name not in weekly or (name, days) in seen or days < 0:
            raise ValueError("Unknown series or duplicate/negative exclusion window")
        seen.add((name, days))
        cutoff = date.fromisoformat(raw["latest_eligible_week_end"])
        as_of = cutoff + timedelta(days=days)
        if inferred_as_of is None:
            inferred_as_of = as_of
        elif as_of != inferred_as_of:
            raise ValueError("Exclusion days and cutoff must imply one common analysis date")
        selected = [r for r in weekly[name] if r["week"] <= cutoff]
        if days == 0 and len(selected) != len(weekly[name]):
            raise ValueError("Zero-day baseline must cover the full weekly table")
        usable = [r for r in selected if r["status"] == "usable"]
        tests = sum(r["tests"] for r in usable)
        detections = sum(r["detections"] for r in usable)
        baseline = [r for r in weekly[name] if r["status"] == "usable"]
        total_tests = sum(r["tests"] for r in baseline)
        total_detections = sum(r["detections"] for r in baseline)
        for field, expected in (("eligible_expected_weeks", len(selected)), ("usable_weeks", len(usable)),
                                ("tests", tests), ("detections", detections)):
            if int(raw[field]) != expected:
                raise ValueError(f"Window {field} disagrees with weekly audit")
        percentage = 100 * detections / tests if tests else None
        retained = tests / total_tests if total_tests else None
        delta = percentage - 100 * total_detections / total_tests if tests and total_tests else None
        for field, expected in (("pooled_percent_positive", percentage),
                                ("retained_test_denominator_fraction", retained),
                                ("change_from_all_weeks_pp", delta)):
            if expected is None:
                if raw[field] != "":
                    raise ValueError("Undefined denominator must remain blank")
            elif not raw[field] or not math.isfinite(float(raw[field])) or not math.isclose(float(raw[field]), expected, abs_tol=1e-9, rel_tol=0):
                raise ValueError(f"Window {field} disagrees with count-derived value")
        windows[name].append({"days": days, "delta_pp": delta, "retained": retained})
    if set(windows) != set(weekly):
        raise ValueError("Every series needs a sensitivity table")
    for values in windows.values():
        values.sort(key=lambda item: item["days"])
    return dict(weekly), dict(windows)


def render(directory: Path, output: Path):
    weekly, windows = load_context(directory)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.fonttype": "none", "svg.hashsalt": "denominator-context-v1"})
    fig, axes = plt.subplots(len(weekly), 2, figsize=(11, 2.6 * len(weekly) + 1),
                             squeeze=False, layout="constrained")
    palette = ["#176b87", "#8c4b16", "#506b35"]
    max_tests = max((r["tests"] for rows in weekly.values() for r in rows if r["tests"] is not None), default=0)
    deltas = [p["delta_pp"] for points in windows.values() for p in points if p["delta_pp"] is not None]
    shared_limits = (min([0] + deltas) - .035, max([0] + deltas) + .055)
    for index, (name, rows) in enumerate(weekly.items()):
        left, right = axes[index]
        color = palette[index % len(palette)]
        left.plot([r["week"] for r in rows], [r["tests"] for r in rows], color=color, linewidth=1.8)
        unavailable = sum(r["status"] != "usable" for r in rows)
        left.set(title=f"{name}: weekly test denominator", ylabel="Reported tests", ylim=(0, max(1, max_tests * 1.06)))
        left.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        left.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        left.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
        if unavailable:
            left.text(.02, .05, f"{unavailable} unusable slots shown as gaps", transform=left.transAxes)
        points = windows[name]
        right.plot([p["days"] for p in points], [p["delta_pp"] for p in points], "o-", color=color)
        right.axhline(0, color="#8b949b", linewidth=.8)
        right.set(title="Window change; labels show % of tests retained", ylabel="Positivity change (percentage points)",
                  xlabel="Exclude weeks newer than this many days", xticks=[p["days"] for p in points], ylim=shared_limits)
        right.margins(x=.1, y=.35)
        for point in points:
            if point["delta_pp"] is not None:
                right.annotate(f'{100 * point["retained"]:.1f}%',
                               (point["days"], point["delta_pp"]), xytext=(0, 10),
                               textcoords="offset points", ha="center", fontsize=8)
        for axis in (left, right):
            axis.spines[["top", "right"]].set_visible(False)
            axis.grid(axis="y", alpha=.18)
    fig.suptitle("Read positivity together with its test denominator", weight="bold", fontsize=17)
    fig.supxlabel("One pinned CDC NREVSS release • separate denominators for each category\nWindow sensitivity is not reporting-vintage reconstruction or population prevalence.", fontsize=10)
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ("svg", "png"):
        fig.savefig(output / f"denominator-context.{suffix}", dpi=160,
                    metadata={"Date": None} if suffix == "svg" else None)
    plt.close(fig)
    record = {"schema_version": 1, "matplotlib_version": matplotlib.__version__,
              "sources": [{"name": name, "sha256": hashlib.sha256((directory / name).read_bytes()).hexdigest()}
                          for name in ("weekly_audit.csv", "trailing_window_sensitivity.csv")],
              "series": {name: {"weeks": len(rows), "usable_weeks": sum(r["status"] == "usable" for r in rows),
                                "windows": len(windows[name])} for name, rows in weekly.items()},
              "scope": "Saved count-derived summaries; no new download or inference."}
    (output / "provenance.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("results_public"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        render(args.input_dir, args.output_dir)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"Invalid audit tables: {exc}\n")


if __name__ == "__main__":
    main()
