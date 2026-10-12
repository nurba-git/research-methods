# Methodology Passport Card

## 1. Project information

- **Title:** The Effectiveness of Artificial Intelligence-Based Adaptive Platforms on Student Academic Performance in Higher Education
- **Authors:** Nurali and Nurbakyt
- **GitHub repository:** `https://github.com/nurba-git/research-methods.git` *(replace with the actual public repository URL after publishing)*

## 2. Research type and justification

**Primary approach: Quantitative comparative study.** The research question concerns measurable differences in academic score gain and time spent learning. A real implementation may use a randomized controlled or quasi-experimental design, depending on access to students and institutional constraints. The repository currently demonstrates only the data-processing pipeline on synthetic data; it is not a completed student experiment.

## 3. Research question

How does the use of an AI-based adaptive learning platform affect students' academic performance and the time required to master course material compared with traditional learning?

## 4. Hypotheses

- **H0 (null hypothesis):** There is no statistically significant difference in mean academic score gain between students using the adaptive-learning platform and students using the traditional-learning approach.
- **H1 (alternative hypothesis):** Students using the adaptive-learning platform have a higher mean academic score gain than students using the traditional-learning approach.

The hypothesis should be tested using real observations and a pre-specified statistical analysis. The sample script does not perform significance testing.

## 5. Variable matrix

| Category | Variable | Operational definition / handling |
|---|---|---|
| Independent | Learning approach | Traditional learning (baseline) vs. AI-adaptive learning |
| Primary dependent | Academic score gain | Post-test score minus pre-test score, measured in points from 0 to 100 |
| Secondary dependent | Learning time | Minutes spent completing the equivalent learning task |
| Guardrail | Data validity | Scores must be within 0–100; time values must be positive; invalid data must be reported rather than silently ignored |
| Controlled | Baseline knowledge | Measure using the same pre-test; use randomization or statistical adjustment |
| Controlled | Learning content and assessment | Same learning objectives, equivalent tasks, same scoring rubric |
| Controlled | Duration and environment | Same scheduled time, course period, and access conditions where feasible |
| Recorded covariates | Prior GPA, study program, prior AI-platform experience | Record only when justified, consented, and permitted by ethics/privacy rules |

**Algorithm parameters (for a later technical extension):** adaptation threshold, recommendation strategy, and update frequency may be varied only if the study actually implements and logs these settings. They are not manipulated by the current prototype.

## 6. Selected metrics and baseline

### Primary metric

**Mean score gain (points):**

`score_gain = posttest_score - pretest_score`

Compare the mean gain under adaptive learning with the mean gain under traditional learning. For a paired design, calculate the per-student difference in gains and use a suitable paired statistical test with confidence intervals.

### Secondary metric

**Mean learning time (minutes):** average task completion time for each condition; report `adaptive mean - traditional mean`. Negative values indicate less time in the adaptive condition.

### Guardrail metrics

- All test scores are between 0 and 100.
- Learning time is greater than zero.
- Report sample size and missing observations.
- For a real platform, also monitor system availability, serious errors, privacy incidents, and accessibility problems.

### Baseline / control group

Traditional learning using equivalent course material and assessment is the baseline. The adaptive condition uses the same learning objectives and assessment, with the platform adapting learning content or sequence to student progress.

## 7. Experimental design and reproducibility

1. Recruit an adequately sized student sample after institutional approval and informed consent.
2. Measure baseline knowledge using a pre-test.
3. Assign students randomly to conditions where feasible; otherwise document the quasi-experimental assignment process.
4. Keep content, assessment criteria, and study duration comparable across conditions.
5. Collect anonymized pre-test, post-test, and time measurements.
6. Pre-register the primary outcome and statistical analysis; report effect sizes and confidence intervals, not only p-values.
7. Run the repository pipeline with a versioned configuration and preserve the data dictionary and analysis outputs.

## 8. Limitations and validity threats

- **Selection bias:** students who choose to use an AI platform may differ from other students. Mitigation: random assignment where feasible, or adjust for baseline differences.
- **Novelty effect:** short-term engagement may not persist. Mitigation: measure outcomes across a sufficiently long period.
- **Instructor/content differences:** unequal teaching materials can confound results. Mitigation: standardize content and assessment.
- **Small sample:** results may be imprecise. Mitigation: justify sample size and report uncertainty.
- **External validity:** one course or university may not represent all higher education settings. Mitigation: replicate across courses and institutions.
- **Synthetic demonstration data:** the included sample is only for pipeline testing and cannot support substantive claims.

## 9. Repository status

The code currently performs descriptive calculations on a synthetic sample and exports results to CSV and JSON. It does not connect to a live AI platform, measure GPA, or perform inferential statistics. These are future study tasks, not completed findings.
