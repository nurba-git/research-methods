"""Generate a SIMULATED raw session log in the format the real platform will produce.

No real students were measured. This file exists so that the Task 3 pipeline
(process_data.py -> visualize.py -> notebook) can be developed and tested
before the real Week 7-8 log is available. Replace data/raw/test_run.jsonl with
the real export and re-run the pipeline; nothing else needs to change.

Usage (from the repository root):
    python src/simulate_data.py --config configs/config.yaml
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parent.parent

# Assumed effect sizes for the simulation (not findings):
TRUE_GAIN = {"traditional": 12.0, "adaptive": 15.5}   # mean post - pre, points
GAIN_SD = 7.0
TIME_MEDIAN = {"traditional": 62.0, "adaptive": 54.0}  # minutes per session (evaluation)
LATENCY_MEDIAN = {"traditional": 180.0, "adaptive": 320.0}  # ms, evaluation sessions
ERROR_P = {"traditional": {"warmup": 0.010, "evaluation": 0.005},
           "adaptive": {"warmup": 0.060, "evaluation": 0.010}}


def stratified_assignment(pretest: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """1:1 allocation within pre-test terciles."""
    groups = np.empty(len(pretest), dtype=object)
    terciles = np.quantile(pretest, [1 / 3, 2 / 3])
    stratum = np.digitize(pretest, terciles)
    for s in np.unique(stratum):
        idx = np.flatnonzero(stratum == s)
        rng.shuffle(idx)
        labels = np.array(["traditional", "adaptive"] * (len(idx) // 2 + 1))[: len(idx)]
        rng.shuffle(labels)
        groups[idx] = labels
    return groups


def simulate(cfg: dict) -> list[dict]:
    sim, an = cfg["simulation"], cfg["analysis"]
    rng = np.random.default_rng(cfg["experiment"]["random_seed"])
    n, n_sessions, warmup = sim["n_students"], sim["n_sessions"], an["warmup_sessions"]

    pretest = np.clip(np.round(rng.normal(55, 11, n)), 15, 90)
    groups = stratified_assignment(pretest, rng)
    ability = (pretest - 55) / 11  # standardised prior knowledge
    records = []

    for i in range(n):
        sid, g = f"S{i + 1:03d}", groups[i]
        gain = rng.normal(TRUE_GAIN[g] + 1.5 * ability[i], GAIN_SD)
        post = float(np.clip(np.round(pretest[i] + gain), 0, 100))
        dropped = rng.random() < sim["dropout_rate"]
        last_session = int(rng.integers(3, n_sessions)) if dropped else n_sessions

        records.append({"event": "pretest", "student_id": sid, "group": g, "week": 0,
                        "score": float(pretest[i])})
        for s in range(1, last_session + 1):
            phase = "warmup" if s <= warmup else "evaluation"
            run_id = f"{sid}-s{s:02d}"
            if rng.random() < ERROR_P[g][phase]:
                records.append({"event": "session", "run_id": run_id, "student_id": sid,
                                "group": g, "session": s, "phase": phase, "status": "error",
                                "quiz_score_pct": None, "time_on_task_min": None,
                                "response_latency_ms": None})
                continue
            progress = (s - 1) / (n_sessions - 1)
            # Learning curve: adaptive starts lower (mis-calibrated cold start), then climbs faster.
            if g == "adaptive":
                mean_quiz = pretest[i] + (TRUE_GAIN[g] + 2) * progress - (6 if s <= warmup else 0)
            else:
                mean_quiz = pretest[i] + TRUE_GAIN[g] * progress
            quiz = float(np.clip(np.round(rng.normal(mean_quiz + 8, 8), 1), 0, 100))
            t_med = TIME_MEDIAN[g] * (1.15 if s <= warmup else 1.0)
            minutes = float(np.round(rng.lognormal(np.log(t_med), 0.18), 1))
            lat_med = LATENCY_MEDIAN[g] * ((3.0 if s == 1 else 1.8) if (s <= warmup and g == "adaptive") else 1.0)
            latency = float(np.round(rng.lognormal(np.log(lat_med), 0.45), 1))
            records.append({"event": "session", "run_id": run_id, "student_id": sid,
                            "group": g, "session": s, "phase": phase, "status": "ok",
                            "quiz_score_pct": quiz, "time_on_task_min": minutes,
                            "response_latency_ms": latency})
        if not dropped:
            records.append({"event": "posttest", "student_id": sid, "group": g,
                            "week": n_sessions + 1, "score": post})
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    out = ROOT / cfg["analysis"]["raw_jsonl"]
    out.parent.mkdir(parents=True, exist_ok=True)
    records = simulate(cfg)
    with out.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps({**rec, "simulated": True}) + "\n")
    print(f"Wrote {len(records)} simulated records to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
