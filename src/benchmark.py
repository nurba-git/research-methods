"""Task 2 smoke test: descriptive between-group comparison on the 10-row sample.

Usage (from the repository root):
    python src/benchmark.py --config configs/config.yaml

Writes results/summary.json and results/condition_metrics.csv.
The sample is synthetic; the numbers only show that the pipeline runs.
"""
import argparse
import csv
import json
from pathlib import Path
from statistics import mean, stdev

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping.")
    return config


def as_number(row: dict, key: str, row_number: int) -> float:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: missing or invalid value for '{key}'.") from exc


def read_records(input_path: Path, cfg: dict) -> list[dict]:
    cols, val, groups = cfg["columns"], cfg["validation"], cfg["groups"]
    allowed = {groups["baseline"], groups["treatment"]}
    records = []
    with input_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = [cols[k] for k in ("student_id", "group", "pretest", "posttest", "learning_time")]
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        for row_number, row in enumerate(reader, start=2):
            sid = (row.get(cols["student_id"]) or "").strip()
            group = (row.get(cols["group"]) or "").strip()
            if not sid:
                raise ValueError(f"Row {row_number}: student_id cannot be empty.")
            if group not in allowed:
                raise ValueError(f"Row {row_number}: group must be one of {sorted(allowed)}.")
            pre = as_number(row, cols["pretest"], row_number)
            post = as_number(row, cols["posttest"], row_number)
            minutes = as_number(row, cols["learning_time"], row_number)
            for label, score in (("pre-test", pre), ("post-test", post)):
                if not val["min_score"] <= score <= val["max_score"]:
                    raise ValueError(f"Row {row_number}: {label} score outside configured range.")
            if minutes <= val["min_time"]:
                raise ValueError(f"Row {row_number}: learning time must be > {val['min_time']}.")
            records.append({"student_id": sid, "group": group, "pretest_score": pre,
                            "posttest_score": post, "score_gain": post - pre,
                            "learning_time_min": minutes})
    if not records:
        raise ValueError(f"No data rows found in {input_path}")
    return records


def describe(values: list[float]) -> dict:
    return {"n": len(values), "mean": round(mean(values), 3),
            "sd": round(stdev(values), 3) if len(values) > 1 else None}


def run(config_path: Path) -> dict:
    cfg = load_config(config_path)
    base, treat = cfg["groups"]["baseline"], cfg["groups"]["treatment"]
    input_path = ROOT / cfg["sample"]["input_csv"]
    output_dir = ROOT / cfg["sample"]["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    records = read_records(input_path, cfg)
    by_group = {g: [r for r in records if r["group"] == g] for g in (base, treat)}
    for g, rows in by_group.items():
        if not rows:
            raise ValueError(f"No rows for group '{g}'.")

    summary = {"experiment": cfg["experiment"]["name"],
               "data_note": "Synthetic smoke-test sample; not real student evidence.",
               "n_records": len(records)}
    for metric in ("score_gain", "learning_time_min"):
        stats = {g: describe([r[metric] for r in rows]) for g, rows in by_group.items()}
        stats["difference_treatment_minus_baseline"] = round(
            stats[treat]["mean"] - stats[base]["mean"], 3)
        summary[metric] = stats

    metrics_path = output_dir / "condition_metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Experiment completed successfully.")
    print(f"Valid records: {len(records)}")
    for metric, unit in (("score_gain", "points"), ("learning_time_min", "min")):
        s = summary[metric]
        print(f"{metric}: {base} {s[base]['mean']} ± {s[base]['sd']} {unit} | "
              f"{treat} {s[treat]['mean']} ± {s[treat]['sd']} {unit} | "
              f"diff {s['difference_treatment_minus_baseline']}")
    print(f"Outputs: {metrics_path.relative_to(ROOT)} and {summary_path.relative_to(ROOT)}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml", help="Path to YAML config")
    args = parser.parse_args()
    run(Path(args.config))


if __name__ == "__main__":
    main()
