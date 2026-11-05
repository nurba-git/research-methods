"""Descriptive benchmark for a synthetic adaptive-learning sample."""
import argparse
import csv
import json
from pathlib import Path
from statistics import mean

import yaml


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


def run(config_path: Path) -> dict:
    config = load_config(config_path)
    root = config_path.resolve().parent.parent
    exp = config["experiment"]
    columns = config["columns"]
    validation = config["validation"]

    input_path = root / exp["input_csv"]
    output_dir = root / exp["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    with input_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = [
            columns["student_id"], columns["pretest"],
            columns["traditional_posttest"], columns["adaptive_posttest"],
            columns["traditional_time"], columns["adaptive_time"],
        ]
        missing_columns = [name for name in required if name not in (reader.fieldnames or [])]
        if missing_columns:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")

        for row_number, row in enumerate(reader, start=2):
            student_id = (row.get(columns["student_id"]) or "").strip()
            if not student_id:
                raise ValueError(f"Row {row_number}: student_id cannot be empty.")
            pre = as_number(row, columns["pretest"], row_number)
            trad_post = as_number(row, columns["traditional_posttest"], row_number)
            adapt_post = as_number(row, columns["adaptive_posttest"], row_number)
            trad_time = as_number(row, columns["traditional_time"], row_number)
            adapt_time = as_number(row, columns["adaptive_time"], row_number)

            for label, score in [
                ("pre-test", pre), ("traditional post-test", trad_post),
                ("adaptive post-test", adapt_post),
            ]:
                if not validation["min_score"] <= score <= validation["max_score"]:
                    raise ValueError(f"Row {row_number}: {label} score must be in the configured score range.")
            if trad_time <= validation["min_time"] or adapt_time <= validation["min_time"]:
                raise ValueError(f"Row {row_number}: learning times must be greater than {validation['min_time']}.")

            records.append({
                "student_id": student_id,
                "pretest_score": pre,
                "traditional_score_gain": trad_post - pre,
                "adaptive_score_gain": adapt_post - pre,
                "traditional_time_min": trad_time,
                "adaptive_time_min": adapt_time,
            })

    if not records:
        raise ValueError(f"No data rows found in {input_path}")

    traditional_gains = [r["traditional_score_gain"] for r in records]
    adaptive_gains = [r["adaptive_score_gain"] for r in records]
    traditional_times = [r["traditional_time_min"] for r in records]
    adaptive_times = [r["adaptive_time_min"] for r in records]

    summary = {
        "experiment": exp["name"],
        "data_note": "Synthetic demonstration data only; not real student evidence.",
        "n_records": len(records),
        "primary_metric": {
            "name": "mean_score_gain_points",
            "traditional_mean": round(mean(traditional_gains), 3),
            "adaptive_mean": round(mean(adaptive_gains), 3),
            "difference_adaptive_minus_traditional": round(mean(adaptive_gains) - mean(traditional_gains), 3),
        },
        "secondary_metric": {
            "name": "mean_learning_time_minutes",
            "traditional_mean": round(mean(traditional_times), 3),
            "adaptive_mean": round(mean(adaptive_times), 3),
            "difference_adaptive_minus_traditional": round(mean(adaptive_times) - mean(traditional_times), 3),
        },
    }

    metrics_path = output_dir / "condition_metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "student_id", "pretest_score", "traditional_score_gain",
            "adaptive_score_gain", "traditional_time_min", "adaptive_time_min",
        ])
        writer.writeheader()
        writer.writerows(records)

    summary_path = output_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print("Experiment completed successfully.")
    print(f"Valid records: {len(records)}")
    print(f"Mean score gain — traditional: {summary['primary_metric']['traditional_mean']}")
    print(f"Mean score gain — adaptive: {summary['primary_metric']['adaptive_mean']}")
    print(f"Gain difference (adaptive - traditional): {summary['primary_metric']['difference_adaptive_minus_traditional']}")
    print(f"Mean time — traditional: {summary['secondary_metric']['traditional_mean']} min")
    print(f"Mean time — adaptive: {summary['secondary_metric']['adaptive_mean']} min")
    print(f"Outputs: {metrics_path.relative_to(root)} and {summary_path.relative_to(root)}")
    print("Reminder: sample data are synthetic and must not be presented as empirical findings.")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml", help="Path to experiment YAML configuration")
    args = parser.parse_args()
    run(Path(args.config))


if __name__ == "__main__":
    main()
