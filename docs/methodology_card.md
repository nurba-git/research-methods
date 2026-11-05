# Methodology Passport Card

## 1. Project information

| Field | Value |
|---|-------|
| **Title** | The Effectiveness of Artificial Intelligence-Based Adaptive Platforms on Student Academic Performance in Higher Education |
| **Authors** | Nurali Seifulla (nurali.seifulla@narxoz.kz) and Nurbakyt Sagidulla (nurbakyt.sagidulla@narxoz.kz), Narxoz University |
| **GitHub repository** | <https://github.com/nurba-git/research-methods> |
| **Course / deliverable** | Research Methods — Task 2 (Methodology Card & Repository), revised |

## 2. Research type and design

**Research type: quantitative, confirmatory, experimental.** The research question asks whether one
learning condition *causes* a larger, measurable change in test scores than another. That calls for
numerical outcomes, a pre-specified hypothesis test and a design that supports causal inference, so
a qualitative or mixed-methods approach is not chosen for the primary question.

**Design: two-arm, parallel-group randomized controlled trial (RCT).** The design is fixed; it is not
left open between an RCT and a quasi-experiment.

| Design element | Decision |
|---|--------|
| Unit of randomization | Individual student |
| Arms | **Baseline:** traditional learning in the university LMS · **Treatment:** the same course module delivered through an AI-adaptive platform |
| Allocation | 1:1, stratified by pre-test tercile (low / middle / high), computer-generated sequence with fixed seed, concealed from instructors until enrolment closes |
| Duration | Week 0 pre-test → 8 weekly learning sessions → Week 9 post-test |
| Warm-up | Sessions 1–2 are onboarding and cold-start calibration of the adaptive model. They are logged but excluded from session-level metrics |
| Blinding | Students cannot be blinded; post-tests are scored automatically or by a marker blind to arm |
| Planned sample | N = 140 (70 per arm). 64 per arm detect d = 0.5 at α = 0.05 (two-sided), power = 0.80; +10% for attrition |
| Analysis population | Complete cases (randomized and post-tested); attrition reported per arm |

## 3. Research question

**RQ1 (causal).** How does learning with an AI-based adaptive platform affect university students'
academic score gain and time on task, compared with traditional learning on equivalent material?

*RQ2 from Task 1 (which algorithm parameters predict learning difficulties best) is deferred to a
later technical study; the current experiment does not manipulate algorithm parameters.*

## 4. Hypotheses

- **H₀ (null):** The mean score gain (post-test − pre-test) of the adaptive arm equals that of the
  traditional arm: μ(adaptive) − μ(traditional) = 0.
- **H₁ (alternative):** The mean score gain differs between arms: μ(adaptive) − μ(traditional) ≠ 0
  (expected direction: adaptive > traditional).

**Decision rule:** reject H₀ if the two-sided Welch t-test gives p < 0.05 **and** the 95% bootstrap
CI of the mean difference excludes 0. Effect size is reported as Hedges' g. An ANCOVA
(post-test ~ arm + pre-test) is run as a pre-specified sensitivity analysis.

## 5. Variable matrix

| Category | Variable | Operational definition | Unit / levels |
|----|----|-------|----|
| **Independent** | Learning approach | Arm assigned by randomization | `traditional` (baseline), `adaptive` |
| **Dependent — primary** | Score gain | Post-test score − pre-test score on parallel test forms | points (−100 … 100) |
| **Dependent — secondary** | Time on task | Mean minutes per weekly session (evaluation sessions 3–8) | minutes |
| **Dependent — secondary** | Session quiz score | Weekly quiz score | % correct |
| **Controlled** | Baseline knowledge | Same pre-test; stratified randomization; pre-test as ANCOVA covariate | points |
| **Controlled** | Content and assessment | Same learning objectives, same item bank, same scoring rubric in both arms | – |
| **Controlled** | Schedule and environment | Same course, semester, session length and LMS access conditions | – |
| **Controlled** | Analysis environment | Python 3.11.11, pinned packages (`requirements.txt`), Docker image, seed = 42 | – |
| **Recorded covariates** | Study programme, prior experience with AI platforms | Collected only with consent | categorical |

## 6. Metrics and baseline

### Primary metric
**Difference in mean score gain**, Δ = mean gain(adaptive) − mean gain(traditional), in points, with
a 95% bootstrap CI (10 000 resamples) and Hedges' g.

### Secondary metrics
- Difference in mean time on task (minutes; negative = adaptive faster).
- Weekly quiz score trajectory per arm (learning curve), sessions 3–8.

### Guardrail metrics

| Guardrail | Threshold | Why |
|----|-----|-----|
| Platform error rate | ≤ 2% of evaluation sessions with `status = error` | A broken platform would bias the comparison |
| Platform response latency | p95 ≤ 1000 ms in evaluation sessions | Slow feedback harms the learning experience |
| Attrition | ≤ 15% per arm, and similar between arms | Differential drop-out breaks randomization |
| Data validity | Scores in 0–100, times > 0; invalid rows reported, never silently dropped | Measurement integrity |

### Baseline (control group)
Traditional learning: the same module, readings, exercises and weekly quizzes delivered as static
pages in the university LMS, in a fixed order, with no algorithmic adaptation. The adaptive arm
receives the same item bank, but the platform chooses item order and difficulty from each student's
predicted mastery.

## 7. Procedure and reproducibility

1. Obtain ethics approval and informed consent; pseudonymise student IDs.
2. Week 0: administer the pre-test; randomize within pre-test terciles.
3. Weeks 1–8: one learning session per week; the platform logs one JSON line per session.
4. Week 9: administer the post-test.
5. Pre-register the primary outcome, test and decision rule before unblinding.
6. Run `src/process_data.py` and `src/visualize.py` (or the notebook) with the versioned
   `configs/config.yaml`; outputs go to `data/processed/` and `reports/figures/`.

## 8. Threats to validity

| Threat | Type | Mitigation |
|----|---|-------|
| Selection bias | Internal | Individual randomization, stratified by pre-test |
| Novelty / cold-start effect | Internal | Sessions 1–2 treated as warm-up; outcome measured at Week 9 |
| Contamination between arms | Internal | Separate course shells; students asked not to share platform access |
| Instructor or content differences | Internal | Identical objectives, item bank and rubric in both arms |
| Differential attrition | Internal | Attrition guardrail; report per arm; sensitivity analysis |
| Test practice effect | Construct | Parallel pre- and post-test forms |
| Small or single-site sample | External / statistical | A-priori power analysis; report CIs; replicate in other courses |
| Synthetic demonstration data | Status | The repository currently runs on simulated data; no empirical claim is made |

## 9. Repository status

The repository contains a tested, containerised pipeline. `src/benchmark.py` runs a smoke test on a
10-row sample. The Task 3 analysis (`src/process_data.py`, `src/visualize.py`,
`notebooks/01_data_analysis.ipynb`) currently runs on a **simulated** session log generated by
`src/simulate_data.py` with seed 42. It will be re-run unchanged on the real log once collected.
