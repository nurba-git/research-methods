"""Data processing and statistical aggregation for the adaptive-learning RCT.

Pipeline: raw JSONL log -> warm-up filtering -> guardrail checks ->
per-student outcomes -> descriptive statistics with bootstrap 95% CIs ->
inferential tests -> CSV/JSON files in data/processed/.

Usage (from the repository root):
    python src/process_data.py --config configs/config.yaml
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
GROUP_ORDER = ["traditional", "adaptive"]


# --------------------------------------------------------------------------- I/O
def load_config(path: str | Path = "configs/config.yaml") -> dict:
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_raw(path: str | Path) -> pd.DataFrame:
    """Read the JSONL log (one JSON object per line)."""
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    return pd.read_json(path, lines=True)


# ------------------------------------------------------------- filtering / checks
def split_sessions(raw: pd.DataFrame, warmup_sessions: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (all sessions, evaluation sessions). Sessions 1..warmup are dropped from the latter."""
    sessions = raw[raw["event"] == "session"].copy()
    sessions["session"] = sessions["session"].astype(int)
    expected_phase = np.where(sessions["session"] <= warmup_sessions, "warmup", "evaluation")
    mismatch = (sessions["phase"] != expected_phase).sum()
    if mismatch:
        raise ValueError(f"{mismatch} sessions have a phase label inconsistent with warmup_sessions")
    return sessions, sessions[sessions["phase"] == "evaluation"].copy()


def validity_report(raw: pd.DataFrame) -> dict:
    """Count invalid values; never drop them silently."""
    tests = raw[raw["event"].isin(["pretest", "posttest"])]
    ok = raw[(raw["event"] == "session") & (raw["status"] == "ok")]
    return {
        "test_scores_out_of_range": int((~tests["score"].between(0, 100)).sum()),
        "quiz_scores_out_of_range": int((~ok["quiz_score_pct"].between(0, 100)).sum()),
        "non_positive_times": int((ok["time_on_task_min"] <= 0).sum()),
        "non_positive_latencies": int((ok["response_latency_ms"] <= 0).sum()),
    }


def wilson_ci(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (np.nan, np.nan)
    z = stats.norm.ppf(0.5 + level / 2)
    p = k / n
    centre = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return (centre - half, centre + half)


def guardrails(raw: pd.DataFrame, sessions: pd.DataFrame, eval_sessions: pd.DataFrame,
               cfg: dict) -> pd.DataFrame:
    """Error rate, p95 latency and attrition per arm, with pass/fail flags."""
    g = cfg["guardrails"]
    rows = []
    for group in GROUP_ORDER:
        for phase, frame in (("warmup", sessions[sessions["phase"] == "warmup"]),
                             ("evaluation", eval_sessions)):
            f = frame[frame["group"] == group]
            k, n = int((f["status"] == "error").sum()), len(f)
            lo, hi = wilson_ci(k, n)
            rows.append({"group": group, "guardrail": f"error_rate_{phase}", "value": k / n,
                         "ci_low": lo, "ci_high": hi, "n": n,
                         "threshold": g["max_error_rate"] if phase == "evaluation" else np.nan})
        lat = eval_sessions.loc[(eval_sessions["group"] == group) &
                                (eval_sessions["status"] == "ok"), "response_latency_ms"]
        rows.append({"group": group, "guardrail": "p95_latency_ms_evaluation",
                     "value": float(np.percentile(lat, 95)), "ci_low": np.nan, "ci_high": np.nan,
                     "n": len(lat), "threshold": g["max_p95_latency_ms"]})
        randomized = raw[(raw["event"] == "pretest") & (raw["group"] == group)]["student_id"].nunique()
        posttested = raw[(raw["event"] == "posttest") & (raw["group"] == group)]["student_id"].nunique()
        lo, hi = wilson_ci(randomized - posttested, randomized)
        rows.append({"group": group, "guardrail": "attrition", "value": 1 - posttested / randomized,
                     "ci_low": lo, "ci_high": hi, "n": randomized, "threshold": g["max_attrition"]})
    out = pd.DataFrame(rows)
    out["passed"] = np.where(out["threshold"].isna(), pd.NA, out["value"] <= out["threshold"])
    return out


# --------------------------------------------------------------- per-student data
def student_outcomes(raw: pd.DataFrame, eval_sessions: pd.DataFrame) -> pd.DataFrame:
    """One row per student who completed both tests (complete-case population)."""
    pre = raw[raw["event"] == "pretest"].set_index("student_id")[["group", "score"]]
    post = raw[raw["event"] == "posttest"].set_index("student_id")["score"]
    ok = eval_sessions[eval_sessions["status"] == "ok"]
    per_student = ok.groupby("student_id").agg(
        time_on_task_min=("time_on_task_min", "mean"),
        quiz_score_pct=("quiz_score_pct", "mean"),
        n_eval_sessions=("session", "count"))
    df = pre.rename(columns={"score": "pretest_score"}).join(post.rename("posttest_score"), how="inner")
    df["score_gain"] = df["posttest_score"] - df["pretest_score"]
    df = df.join(per_student, how="left").reset_index()
    df["group"] = pd.Categorical(df["group"], GROUP_ORDER, ordered=True)
    return df.sort_values(["group", "student_id"]).reset_index(drop=True)


# ----------------------------------------------------------------- statistics
def bootstrap_ci(x: np.ndarray, stat=np.mean, n_boot: int = 10_000, level: float = 0.95,
                 rng: np.random.Generator | None = None) -> tuple[float, float]:
    """Percentile bootstrap CI for a one-sample statistic."""
    rng = rng or np.random.default_rng(42)
    x = np.asarray(x, dtype=float)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    boots = stat(x[idx], axis=1)
    alpha = (1 - level) / 2
    return float(np.quantile(boots, alpha)), float(np.quantile(boots, 1 - alpha))


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, n_boot: int = 10_000, level: float = 0.95,
                      rng: np.random.Generator | None = None) -> tuple[float, float]:
    """Percentile bootstrap CI for mean(b) - mean(a), resampling each arm independently."""
    rng = rng or np.random.default_rng(42)
    a, b = np.asarray(a, float), np.asarray(b, float)
    ma = a[rng.integers(0, len(a), (n_boot, len(a)))].mean(axis=1)
    mb = b[rng.integers(0, len(b), (n_boot, len(b)))].mean(axis=1)
    alpha = (1 - level) / 2
    return float(np.quantile(mb - ma, alpha)), float(np.quantile(mb - ma, 1 - alpha))


def hedges_g(a: np.ndarray, b: np.ndarray) -> float:
    """Bias-corrected standardized mean difference, (mean(b) - mean(a)) / pooled SD."""
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1)) / (na + nb - 2))
    j = 1 - 3 / (4 * (na + nb) - 9)
    return float(j * (np.mean(b) - np.mean(a)) / sp)


def describe(x: np.ndarray, n_boot: int, level: float, rng: np.random.Generator) -> dict:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    lo, hi = bootstrap_ci(x, np.mean, n_boot, level, rng)
    mlo, mhi = bootstrap_ci(x, np.median, n_boot, level, rng)
    return {"n": len(x), "mean": x.mean(), "sd": x.std(ddof=1),
            "mean_ci_low": lo, "mean_ci_high": hi,
            "median": np.median(x), "median_ci_low": mlo, "median_ci_high": mhi,
            "p25": np.percentile(x, 25), "p75": np.percentile(x, 75),
            "p95": np.percentile(x, 95), "p99": np.percentile(x, 99)}


def metrics_summary(students: pd.DataFrame, eval_sessions: pd.DataFrame, cfg: dict,
                    rng: np.random.Generator) -> pd.DataFrame:
    """Long table: one row per (metric, group) with mean, SD, median, percentiles, 95% CIs."""
    n_boot, level = cfg["analysis"]["n_bootstrap"], cfg["analysis"]["ci_level"]
    ok = eval_sessions[eval_sessions["status"] == "ok"]
    specs = [  # (metric, unit, level of analysis, frame, column)
        ("score_gain", "points", "student", students, "score_gain"),
        ("posttest_score", "points", "student", students, "posttest_score"),
        ("pretest_score", "points", "student", students, "pretest_score"),
        ("time_on_task", "min/session", "student", students, "time_on_task_min"),
        ("quiz_score", "%", "session", ok, "quiz_score_pct"),
        ("response_latency", "ms", "session", ok, "response_latency_ms"),
    ]
    rows = []
    for metric, unit, unit_level, frame, col in specs:
        for group in GROUP_ORDER:
            vals = frame.loc[frame["group"] == group, col].to_numpy()
            rows.append({"metric": metric, "unit": unit, "level": unit_level, "group": group,
                         **describe(vals, n_boot, level, rng)})
    return pd.DataFrame(rows)


def session_curve(sessions: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> pd.DataFrame:
    """Per (group, session): mean quiz score and median latency with bootstrap 95% CIs.
    Includes warm-up sessions (flagged) so the cold-start spike can be shown in plots."""
    n_boot, level = cfg["analysis"]["n_bootstrap"], cfg["analysis"]["ci_level"]
    ok = sessions[sessions["status"] == "ok"]
    rows = []
    for (group, s), f in ok.groupby(["group", "session"], sort=True):
        q, lat, t = (f[c].to_numpy() for c in ("quiz_score_pct", "response_latency_ms", "time_on_task_min"))
        qlo, qhi = bootstrap_ci(q, np.mean, n_boot, level, rng)
        llo, lhi = bootstrap_ci(lat, np.median, n_boot, level, rng)
        tlo, thi = bootstrap_ci(t, np.mean, n_boot, level, rng)
        rows.append({"group": group, "session": s, "phase": f["phase"].iloc[0], "n": len(f),
                     "quiz_mean": q.mean(), "quiz_ci_low": qlo, "quiz_ci_high": qhi,
                     "latency_median": np.median(lat), "latency_ci_low": llo, "latency_ci_high": lhi,
                     "latency_p95": np.percentile(lat, 95), "latency_p99": np.percentile(lat, 99),
                     "time_mean": t.mean(), "time_ci_low": tlo, "time_ci_high": thi})
    return pd.DataFrame(rows).round(3)  # same precision as the saved CSV used by visualize.py


def inferential_tests(students: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> dict:
    """Primary test (Welch t on gain), bootstrap CI of the difference, Hedges' g, ANCOVA."""
    n_boot, level = cfg["analysis"]["n_bootstrap"], cfg["analysis"]["ci_level"]
    a = students.loc[students["group"] == "traditional", "score_gain"].to_numpy(float)
    b = students.loc[students["group"] == "adaptive", "score_gain"].to_numpy(float)
    welch = stats.ttest_ind(b, a, equal_var=False)
    mw = stats.mannwhitneyu(b, a, alternative="two-sided")
    lo, hi = bootstrap_diff_ci(a, b, n_boot, level, rng)

    # ANCOVA: posttest = b0 + b1*adaptive + b2*pretest (OLS, classical SEs)
    X = np.column_stack([np.ones(len(students)),
                         (students["group"] == "adaptive").astype(float),
                         students["pretest_score"].astype(float)])
    y = students["posttest_score"].to_numpy(float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = len(y) - X.shape[1]
    se = np.sqrt(np.diag(resid @ resid / dof * np.linalg.inv(X.T @ X)))
    t_arm = beta[1] / se[1]
    tcrit = stats.t.ppf(0.5 + level / 2, dof)

    t_time = stats.ttest_ind(
        students.loc[students["group"] == "adaptive", "time_on_task_min"],
        students.loc[students["group"] == "traditional", "time_on_task_min"], equal_var=False)
    return {
        "n_traditional": int(len(a)), "n_adaptive": int(len(b)),
        "primary": {
            "metric": "score_gain (points)",
            "mean_difference_adaptive_minus_traditional": float(b.mean() - a.mean()),
            "bootstrap_95ci": [lo, hi],
            "welch_t": float(welch.statistic), "welch_df": float(welch.df),
            "welch_p_two_sided": float(welch.pvalue),
            "hedges_g": hedges_g(a, b),
            "mann_whitney_p_two_sided": float(mw.pvalue),
            "reject_h0": bool(welch.pvalue < 0.05 and (lo > 0 or hi < 0)),
        },
        "sensitivity_ancova": {
            "model": "posttest ~ arm + pretest",
            "adjusted_arm_effect": float(beta[1]),
            "ci95": [float(beta[1] - tcrit * se[1]), float(beta[1] + tcrit * se[1])],
            "t": float(t_arm), "df": int(dof),
            "p_two_sided": float(2 * stats.t.sf(abs(t_arm), dof)),
            "pretest_slope": float(beta[2]),
        },
        "secondary_time_on_task": {
            "mean_difference_adaptive_minus_traditional_min": float(
                students.loc[students["group"] == "adaptive", "time_on_task_min"].mean()
                - students.loc[students["group"] == "traditional", "time_on_task_min"].mean()),
            "welch_t": float(t_time.statistic), "welch_p_two_sided": float(t_time.pvalue),
        },
    }


# ------------------------------------------------------------------- pipeline
def run(config_path: str | Path = "configs/config.yaml") -> dict:
    cfg = load_config(config_path)
    seed = cfg["experiment"]["random_seed"]
    np.random.seed(seed)                      # legacy global seed, for any third-party sampling
    rng = lambda: np.random.default_rng(seed)  # noqa: E731 - fresh, identical stream per step
    an = cfg["analysis"]
    out_dir = ROOT / an["processed_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = load_raw(an["raw_jsonl"])
    sessions, eval_sessions = split_sessions(raw, an["warmup_sessions"])
    validity = validity_report(raw)
    if any(validity.values()):
        raise ValueError(f"Invalid values in raw log: {validity}")
    guard = guardrails(raw, sessions, eval_sessions, cfg)
    students = student_outcomes(raw, eval_sessions)
    summary = metrics_summary(students, eval_sessions, cfg, rng())
    curve = session_curve(sessions, cfg, rng())
    tests = inferential_tests(students, cfg, rng())

    summary.round(3).to_csv(out_dir / "metrics_summary.csv", index=False)
    students.round(3).to_csv(out_dir / "student_outcomes.csv", index=False)
    curve.round(3).to_csv(out_dir / "session_curve.csv", index=False)
    guard.round(4).to_csv(out_dir / "guardrails.csv", index=False)
    (out_dir / "inferential_tests.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")

    print(f"Raw records: {len(raw)} | sessions: {len(sessions)} "
          f"(warm-up dropped: {len(sessions) - len(eval_sessions)}) | students analysed: {len(students)}")
    p = tests["primary"]
    print(f"Score gain difference (adaptive - traditional): {p['mean_difference_adaptive_minus_traditional']:.2f} "
          f"points, 95% CI [{p['bootstrap_95ci'][0]:.2f}, {p['bootstrap_95ci'][1]:.2f}], "
          f"Welch p = {p['welch_p_two_sided']:.4f}, Hedges g = {p['hedges_g']:.2f}")
    print(f"Outputs written to {out_dir.relative_to(ROOT)}/")
    return {"raw": raw, "sessions": sessions, "eval_sessions": eval_sessions, "students": students,
            "summary": summary, "curve": curve, "guardrails": guard, "tests": tests,
            "validity": validity, "config": cfg}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml")
    run(parser.parse_args().config)


if __name__ == "__main__":
    main()
