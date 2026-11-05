# Evaluating AI-Based Adaptive Learning in Higher Education

**Authors:** Nurali and Nurbakyt  
**Project type:** Reproducible quantitative benchmark prototype  
**License:** MIT

## Overview

This repository contains a small, reproducible analysis pipeline for comparing traditional learning with an AI-based adaptive learning approach. The prototype calculates score gains and learning time differences from a small CSV sample, then writes machine-readable results.

**Important:** `data/sample/student_results.csv` contains synthetic demonstration data. It is not real student evidence and cannot establish that adaptive learning improves university GPA. Replace it with ethically collected, appropriately anonymized data before drawing research conclusions.

## Research question

How does the use of an AI-based adaptive learning platform affect students' academic performance and the time required to master course material compared with traditional learning?

## Hypotheses

- **H0:** There is no statistically significant difference in academic score gain between the adaptive-learning condition and the traditional-learning condition.
- **H1:** The adaptive-learning condition produces a higher academic score gain than the traditional-learning condition.

A future empirical study should pre-register its analysis, recruit an adequately powered sample, and use an appropriate statistical test. This starter script reports descriptive comparisons only.

## Variables

| Type | Variable | Operational definition |
|---|---|---|
| Independent | Learning approach | Traditional vs. adaptive condition |
| Dependent (primary) | Score gain | Post-test score minus pre-test score, in points |
| Dependent (secondary) | Learning time | Minutes required to complete the learning task |
| Guardrail | Missing/invalid values | Invalid rows are rejected; the script fails clearly if no valid rows remain |
| Controlled (planned real study) | Baseline knowledge | Measure with a pre-test and account for it in analysis |
| Controlled (planned real study) | Content, task duration, assessment | Use equivalent materials and the same scoring rubric |
| Controlled (planned real study) | Course, semester, instructor | Keep constant where feasible or record and adjust analytically |

## Metrics and baseline

- **Primary metric:** Mean score gain in points for each condition and the difference `adaptive - traditional`.
- **Secondary metric:** Mean learning time in minutes for each condition and the difference `adaptive - traditional`.
- **Baseline/control:** Traditional learning condition.
- **Guardrails:** Valid numeric scores in the 0–100 range; positive learning times; no silent dropping of invalid data.

## Repository structure

```text
ai_adaptive_learning_research/
├── configs/config.yaml
├── data/sample/student_results.csv
├── docs/methodology_card.md
├── results/                 # generated outputs; not committed
├── src/benchmark.py
├── .dockerignore
├── .gitignore
├── Dockerfile
├── LICENSE
├── requirements.txt
└── README.md
```

## System requirements

- Python 3.11
- Docker (optional; only needed for container execution)
- Windows, macOS, or Linux
- No GPU is required for this descriptive prototype

## Quickstart (local Python)

Run these commands from the repository root:

```bash
python -m pip install -r requirements.txt
python src/benchmark.py --config configs/config.yaml
```

The script creates `results/summary.json` and `results/condition_metrics.csv`.

## Quickstart (Docker)

```bash
docker build -t adaptive-learning-benchmark .
docker run --rm -v "${PWD}/results:/app/results" adaptive-learning-benchmark
```

On Windows PowerShell, `${PWD}` is supported in current PowerShell versions. If the mounted path causes trouble, run the local Python commands instead.

## Expected output

The exact values are computed from the sample CSV. The output includes:

- number of valid sample records;
- mean score gain for each learning condition;
- difference in mean score gain (`adaptive - traditional`);
- mean learning time for each condition;
- difference in mean time (`adaptive - traditional`).

These are descriptive results from synthetic sample data, not findings about real students.

## Reproducibility

- The configuration file is version-controlled.
- The sample dataset is small and included in the repository.
- The Python dependency is pinned in `requirements.txt`.
- The script reads the same CSV and config on each run and overwrites the generated outputs.
- For a real study, document data provenance, ethics approval/consent, exclusion criteria, randomization, sample-size rationale, and statistical analysis.

## Citation

```bibtex
@misc{nurali_nurbakyt_adaptive_learning_2026,
  title        = {Evaluating AI-Based Adaptive Learning in Higher Education},
  author       = {Nurali and Nurbakyt},
  year         = {2026},
  howpublished = {GitHub repository},
  note         = {Reproducible benchmark prototype}
}
```

## License

This project is released under the MIT License. See `LICENSE`.
