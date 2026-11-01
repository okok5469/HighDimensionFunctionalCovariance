# Task4 smoke results

Completeness: True. All rates use the explicitly reported valid subset.
Missing records and failed methods remain separate from non-rejections.
Null rows are physical distributions identified by null_group_id; shared nulls are reused once.
95% binomial intervals: exact Clopper-Pearson. Calibration: one-sided 95% upper bound <= 0.08.
This is the predeclared calibration tolerance; it does not establish exact 5% size.
Formal labels use Bonferroni over all locked alternative/comparator declarations.
Conservative size or appreciable null-rate differences require separate interpretation.

Smoke execution validates the pipeline only; it supports no scientific conclusion.

All physical null and alternative rows (shared nulls appear only once per method):

| Scenario | Method | tau | n/p | Rejections | planned/completed/valid/failed/missing | Rate | MCSE | 95% CI | Common valid |
|---|---|---:|---|---:|---|---:|---:|---|---:|
| 9efcb5617725a8720ea8 | ours | 0.0 | 200/20 | 0 | 1/1/1/0/0 | 0.0 | 0.0 | [0.0, 0.975] | 1 |
| 9efcb5617725a8720ea8 | xue_s5 | 0.0 | 200/20 | 0 | 1/1/1/0/0 | 0.0 | 0.0 | [0.0, 0.975] | 1 |
| 9efcb5617725a8720ea8 | xue_s11 | 0.0 | 200/20 | 0 | 1/1/1/0/0 | 0.0 | 0.0 | [0.0, 0.975] | 1 |
| 9efcb5617725a8720ea8 | xue_s21 | 0.0 | 200/20 | 0 | 1/1/1/0/0 | 0.0 | 0.0 | [0.0, 0.975] | 1 |

Null calibration (one physical result per null_group_id and shape):

| Null group | n/p | Method | Rate | One-sided 95% upper | Upper <= 0.08 | Conservative |
|---|---|---|---:|---:|---|---|
| spectrum_flat_b0 | 200/20 | ours | 0.0 | 0.95 | False | False |
| spectrum_flat_b0 | 200/20 | xue_s5 | 0.0 | 0.95 | False | False |
| spectrum_flat_b0 | 200/20 | xue_s11 | 0.0 | 0.95 | False | False |
| spectrum_flat_b0 | 200/20 | xue_s21 | 0.0 | 0.95 | False | False |

Paired comparisons:

| Scenario | Comparator | Difference | 95% CI | Adjusted CI | Label |
|---|---|---:|---|---|---|

Scientific interpretation awaits complete independent confirmation.

## Signal geometry and statistic summaries

| Scenario | peak | weighted energy norm | rho | min white eigenvalue | method | T median | critical median |
|---|---:|---:|---:|---:|---|---:|---:|
| 9efcb5617725a8720ea8 | 0.0 | 0.0 | 0.0 | 1.0 | ours | 4.862134979332045 | None |
| 9efcb5617725a8720ea8 | 0.0 | 0.0 | 0.0 | 1.0 | xue_s5 | -3.3409842326527963 | 2.716219070555093 |
| 9efcb5617725a8720ea8 | 0.0 | 0.0 | 0.0 | 1.0 | xue_s11 | -4.703466999641277 | 2.716219070555093 |
| 9efcb5617725a8720ea8 | 0.0 | 0.0 | 0.0 | 1.0 | xue_s21 | 1.0789655600812345 | 2.716219070555093 |

Energy is a grid-weighted Frobenius norm; two peaks increase energy by sqrt(2) at equal tau. It is not equal energy to the single peak.
Independent confirmation is required to separate high point-estimate power and closeness from formal noninferiority or advantage.
