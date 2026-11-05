"""Publication-quality figures for the adaptive-learning RCT.

Rules followed for every figure:
  * axis titles carry physical units;
  * uncertainty is shown (bootstrap 95% CI bands or error bars);
  * colour-blind-safe palette (seaborn "colorblind") AND distinct markers/line styles,
    so the figures stay readable in black-and-white print;
  * each figure is saved as vector PDF and as 300-dpi PNG.

Usage (from the repository root, after src/process_data.py):
    python src/visualize.py --config configs/config.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

if "ipykernel" not in sys.modules:  # headless for CLI/Docker; keep inline plots in Jupyter
    matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

try:  # works both as `python src/visualize.py` and `from src import visualize`
    from process_data import GROUP_ORDER, ROOT, bootstrap_ci, load_config
except ImportError:  # pragma: no cover
    from src.process_data import GROUP_ORDER, ROOT, bootstrap_ci, load_config

PALETTE = dict(zip(GROUP_ORDER, sns.color_palette("colorblind", 2)))
STYLE = {"traditional": {"marker": "o", "linestyle": "--", "label": "Traditional (baseline)"},
         "adaptive": {"marker": "s", "linestyle": "-", "label": "AI-adaptive (treatment)"}}
DPI = 300


def set_style() -> None:
    sns.set_theme(context="paper", style="ticks", font_scale=1.1)
    plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42,   # embed TrueType text in PDF
                         "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.bbox": "tight", "figure.dpi": 110})


def save(fig: plt.Figure, out_dir: Path, name: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / f"{name}.pdf", out_dir / f"{name}.png"]
    fig.savefig(paths[0], metadata={"CreationDate": None})  # deterministic PDF bytes
    fig.savefig(paths[1], dpi=DPI, metadata={"Software": None})
    return paths


def _shade_warmup(ax: plt.Axes, warmup: int) -> None:
    ax.axvspan(0.5, warmup + 0.5, color="0.9", zorder=0)
    ax.text(0.6, 0.97, "warm-up\n(excluded)", transform=ax.get_xaxis_transform(),
            va="top", ha="left", fontsize=8, color="0.35")


def fig_score_vs_session(curve: pd.DataFrame, warmup: int) -> plt.Figure:
    """Fig. 1: mean weekly quiz score per session with 95% bootstrap CI bands."""
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    _shade_warmup(ax, warmup)
    for g in GROUP_ORDER:
        d = curve[curve["group"] == g]
        ax.fill_between(d["session"], d["quiz_ci_low"], d["quiz_ci_high"],
                        color=PALETTE[g], alpha=0.22, linewidth=0)
        ax.plot(d["session"], d["quiz_mean"], color=PALETTE[g], markersize=6,
                markerfacecolor="white" if g == "traditional" else PALETTE[g], **STYLE[g])
    ax.set_xlabel("Weekly learning session (index, 1 session = 1 week)")
    ax.set_ylabel("Mean quiz score (% correct)")
    ax.set_xticks(sorted(curve["session"].unique()))
    ax.set_title("Learning curve by arm (shaded band = 95% bootstrap CI of the mean)", fontsize=10)
    ax.legend(frameon=False, loc="lower right")
    return fig


def fig_gain_boxplot(students: pd.DataFrame, n_boot: int, rng: np.random.Generator) -> plt.Figure:
    """Fig. 2: distribution of score gain per arm (box + points) with mean and 95% CI."""
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    data = [students.loc[students["group"] == g, "score_gain"].to_numpy() for g in GROUP_ORDER]
    bp = ax.boxplot(data, positions=[0, 1], widths=0.45, patch_artist=True, showfliers=False,
                    medianprops={"color": "black", "linewidth": 1.6})
    for patch, g, hatch in zip(bp["boxes"], GROUP_ORDER, ["//", ""]):
        patch.set_facecolor((*PALETTE[g], 0.35))
        patch.set_edgecolor(PALETTE[g])
        patch.set_hatch(hatch)
    for i, (g, vals) in enumerate(zip(GROUP_ORDER, data)):
        jitter = rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals, s=12, alpha=0.55, color=PALETTE[g],
                   marker=STYLE[g]["marker"], edgecolor="none", zorder=3)
        lo, hi = bootstrap_ci(vals, np.mean, n_boot, rng=rng)
        m = vals.mean()
        ax.errorbar(i + 0.34, m, yerr=[[m - lo], [hi - m]], fmt="D", color="black",
                    capsize=4, markersize=6, zorder=4,
                    label="Mean ± 95% bootstrap CI" if i == 0 else None)
    ax.axhline(0, color="0.5", linewidth=0.8, linestyle=":")
    ax.set_xticks([0, 1], [f"{STYLE[g]['label']}\n(n = {len(d)})" for g, d in zip(GROUP_ORDER, data)])
    ax.set_ylabel("Score gain, post-test − pre-test (points)")
    ax.set_title("Distribution of score gain (box = median, IQR; whiskers = 1.5 IQR)", fontsize=10)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), fontsize=8.5)
    return fig


def fig_latency_vs_session(curve: pd.DataFrame, warmup: int, p95_limit: float) -> plt.Figure:
    """Fig. 3: platform response latency per session, log scale, median with 95% CI + p95."""
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    _shade_warmup(ax, warmup)
    for g in GROUP_ORDER:
        d = curve[curve["group"] == g]
        ax.fill_between(d["session"], d["latency_ci_low"], d["latency_ci_high"],
                        color=PALETTE[g], alpha=0.22, linewidth=0)
        ax.plot(d["session"], d["latency_median"], color=PALETTE[g], markersize=6,
                markerfacecolor="white" if g == "traditional" else PALETTE[g],
                **{**STYLE[g], "label": f"{STYLE[g]['label']}: median"})
        ax.plot(d["session"], d["latency_p95"], color=PALETTE[g], marker=STYLE[g]["marker"],
                linestyle=":", markersize=4, alpha=0.8, label=f"{STYLE[g]['label']}: p95")
    ax.axhline(p95_limit, color="black", linestyle="-.", linewidth=1)
    ax.text(curve["session"].max() + 0.4, p95_limit, f"p95 guardrail\n{p95_limit:.0f} ms",
            va="center", ha="left", fontsize=8)
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(matplotlib.ticker.FixedLocator([100, 200, 500, 1000, 2000]))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_ylim(100, 3000)
    ax.set_xlabel("Weekly learning session (index, 1 session = 1 week)")
    ax.set_ylabel("Platform response latency (ms, log scale)")
    ax.set_xticks(sorted(curve["session"].unique()))
    ax.set_title("Response latency (band = 95% bootstrap CI of the median)", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2)
    return fig


def run(config_path: str | Path = "configs/config.yaml") -> dict[str, plt.Figure]:
    cfg = load_config(config_path)
    seed, an = cfg["experiment"]["random_seed"], cfg["analysis"]
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    processed = ROOT / an["processed_dir"]
    out_dir = ROOT / an["figures_dir"]
    curve = pd.read_csv(processed / "session_curve.csv")
    students = pd.read_csv(processed / "student_outcomes.csv")

    set_style()
    figs = {
        "fig1_score_vs_session": fig_score_vs_session(curve, an["warmup_sessions"]),
        "fig2_distribution_boxplot": fig_gain_boxplot(students, an["n_bootstrap"], rng),
        "fig3_latency_vs_session": fig_latency_vs_session(
            curve, an["warmup_sessions"], cfg["guardrails"]["max_p95_latency_ms"]),
    }
    for name, fig in figs.items():
        paths = save(fig, out_dir, name)
        print("Saved", ", ".join(str(p.relative_to(ROOT)) for p in paths))
    return figs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/config.yaml")
    run(parser.parse_args().config)


if __name__ == "__main__":
    main()
