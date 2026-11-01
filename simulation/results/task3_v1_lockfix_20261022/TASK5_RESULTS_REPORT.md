# Task5 unified study

Pilot and confirmation are independent; legacy/task3/task4 data are excluded.
Fixed B500, alpha=.05, all channel pairs and double-time coordinates. Smoke B3 is workflow validation only.
Level band [.03,.07]: point estimates for pilot; two-sided exact 95% intervals for confirmation.
Each level interval is pointwise, not a simultaneous or combined calibration/power guarantee.
Paired intervals use Bonferroni over every locked H1 pair, including comparisons with calibration warnings.
Near-nominal/nominal rejection-probability differences are distinct; unresolved is not a technical failure.

## smoke

Complete: True; completed 5 / planned 5.

| Model | n | p | tau | Method | Reject / valid | Rate | 95% interval | Level status |
|---|---:|---:|---:|---|---:|---:|---|---|
| m1_fourier5_peak1 | 12 | 4 | 0.3 | ours | 0 / 1 | 0.0 | [0.0, 0.975] | not_applicable |
| m1_fourier5_peak1 | 12 | 4 | 0.3 | xue_s5 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| m1_fourier5_peak1 | 12 | 4 | 0.3 | xue_s11 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| m1_fourier5_peak1 | 12 | 4 | 0.3 | xue_s21 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| m2_brownian_peak1 | 12 | 4 | 0.3 | ours | 0 / 1 | 0.0 | [0.0, 0.975] | not_applicable |
| m2_brownian_peak1 | 12 | 4 | 0.3 | xue_s5 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| m2_brownian_peak1 | 12 | 4 | 0.3 | xue_s11 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| m2_brownian_peak1 | 12 | 4 | 0.3 | xue_s21 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| coherent_all | 12 | 4 | 0.3 | ours | 0 / 1 | 0.0 | [0.0, 0.975] | not_applicable |
| coherent_all | 12 | 4 | 0.3 | xue_s5 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| coherent_all | 12 | 4 | 0.3 | xue_s11 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| coherent_all | 12 | 4 | 0.3 | xue_s21 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| local_fejer | 12 | 4 | 0.3 | ours | 0 / 1 | 0.0 | [0.0, 0.975] | not_applicable |
| local_fejer | 12 | 4 | 0.3 | xue_s5 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| local_fejer | 12 | 4 | 0.3 | xue_s11 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| local_fejer | 12 | 4 | 0.3 | xue_s21 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| spectrum_fast_b4 | 12 | 4 | 0.3 | ours | 0 / 1 | 0.0 | [0.0, 0.975] | not_applicable |
| spectrum_fast_b4 | 12 | 4 | 0.3 | xue_s5 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| spectrum_fast_b4 | 12 | 4 | 0.3 | xue_s11 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |
| spectrum_fast_b4 | 12 | 4 | 0.3 | xue_s21 | 1 / 1 | 1.0 | [0.025000000000000022, 1.0] | not_applicable |

### Model findings

- coherent_all (n=12,p=4): ours H0=missing; tau=0.3: 0.0%; high-power point estimates at none.
- local_fejer (n=12,p=4): ours H0=missing; tau=0.3: 0.0%; high-power point estimates at none.
- m1_fourier5_peak1 (n=12,p=4): ours H0=missing; tau=0.3: 0.0%; high-power point estimates at none.
- m2_brownian_peak1 (n=12,p=4): ours H0=missing; tau=0.3: 0.0%; high-power point estimates at none.
- spectrum_fast_b4 (n=12,p=4): ours H0=missing; tau=0.3: 0.0%; high-power point estimates at none.
These are exploratory/workflow findings; the research target remains unconfirmed.
High power is an estimated rejection probability, not a guarantee. Comparative claims additionally require the locked paired intervals and both method-specific level states.
## pilot

Complete: True; completed 9300 / planned 9300.

| Model | n | p | tau | Method | Reject / valid | Rate | 95% interval | Level status |
|---|---:|---:|---:|---|---:|---:|---|---|
| m1_fourier5_peak1 | 200 | 20 | 0.0 | ours | 15 / 500 | 0.03 | [0.016885984203873244, 0.04899822570881894] | exploratory_point_in_band |
| m1_fourier5_peak1 | 200 | 20 | 0.0 | xue_s5 | 40 / 500 | 0.08 | [0.057766119928834334, 0.10734546435635234] | exploratory_point_high |
| m1_fourier5_peak1 | 200 | 20 | 0.0 | xue_s11 | 37 / 500 | 0.074 | [0.052635108548995245, 0.10055887474646992] | exploratory_point_high |
| m1_fourier5_peak1 | 200 | 20 | 0.0 | xue_s21 | 46 / 500 | 0.092 | [0.06814330415665441, 0.12080703261074258] | exploratory_point_high |
| m1_fourier5_peak1 | 400 | 20 | 0.0 | ours | 19 / 500 | 0.038 | [0.02303077080624761, 0.05870729046322855] | exploratory_point_in_band |
| m1_fourier5_peak1 | 400 | 20 | 0.0 | xue_s5 | 31 / 500 | 0.062 | [0.042511061296385495, 0.08685259747910139] | exploratory_point_in_band |
| m1_fourier5_peak1 | 400 | 20 | 0.0 | xue_s11 | 42 / 500 | 0.084 | [0.061209058608347675, 0.11184830124541209] | exploratory_point_high |
| m1_fourier5_peak1 | 400 | 20 | 0.0 | xue_s21 | 30 / 500 | 0.06 | [0.0408441817627769, 0.08454855370760007] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 20 | 0.0 | ours | 26 / 500 | 0.052 | [0.03424569808276791, 0.07526637103062216] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 20 | 0.0 | xue_s5 | 25 / 500 | 0.05 | [0.03261518014933006, 0.07292762165047896] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 20 | 0.0 | xue_s11 | 24 / 500 | 0.048 | [0.0309931687935054, 0.07058079625732981] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 20 | 0.0 | xue_s21 | 27 / 500 | 0.054 | [0.03588425972193367, 0.07759746849493715] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 50 | 0.0 | ours | 19 / 500 | 0.038 | [0.02303077080624761, 0.05870729046322855] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 50 | 0.0 | xue_s5 | 28 / 500 | 0.056 | [0.037530444475022205, 0.0799213006043601] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 50 | 0.0 | xue_s11 | 26 / 500 | 0.052 | [0.03424569808276791, 0.07526637103062216] | exploratory_point_in_band |
| m1_fourier5_peak1 | 800 | 50 | 0.0 | xue_s21 | 25 / 500 | 0.05 | [0.03261518014933006, 0.07292762165047896] | exploratory_point_in_band |
| m2_brownian_peak1 | 200 | 20 | 0.0 | ours | 15 / 500 | 0.03 | [0.016885984203873244, 0.04899822570881894] | exploratory_point_in_band |
| m2_brownian_peak1 | 200 | 20 | 0.0 | xue_s5 | 43 / 500 | 0.086 | [0.06293676656618728, 0.11409366934605583] | exploratory_point_high |
| m2_brownian_peak1 | 200 | 20 | 0.0 | xue_s11 | 69 / 500 | 0.138 | [0.10898386246231191, 0.17137465675598662] | exploratory_point_high |
| m2_brownian_peak1 | 200 | 20 | 0.0 | xue_s21 | 98 / 500 | 0.196 | [0.16208875205626733, 0.23355207265707037] | exploratory_point_high |
| m2_brownian_peak1 | 400 | 20 | 0.0 | ours | 24 / 500 | 0.048 | [0.0309931687935054, 0.07058079625732981] | exploratory_point_in_band |
| m2_brownian_peak1 | 400 | 20 | 0.0 | xue_s5 | 22 / 500 | 0.044 | [0.027776767285571772, 0.06586100032359485] | exploratory_point_in_band |
| m2_brownian_peak1 | 400 | 20 | 0.0 | xue_s11 | 29 / 500 | 0.058 | [0.039183868797187785, 0.08223822089383528] | exploratory_point_in_band |
| m2_brownian_peak1 | 400 | 20 | 0.0 | xue_s21 | 24 / 500 | 0.048 | [0.0309931687935054, 0.07058079625732981] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 20 | 0.0 | ours | 19 / 500 | 0.038 | [0.02303077080624761, 0.05870729046322855] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 20 | 0.0 | xue_s5 | 22 / 500 | 0.044 | [0.027776767285571772, 0.06586100032359485] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 20 | 0.0 | xue_s11 | 23 / 500 | 0.046 | [0.02938017539240277, 0.0682254278812379] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 20 | 0.0 | xue_s21 | 26 / 500 | 0.052 | [0.03424569808276791, 0.07526637103062216] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 50 | 0.0 | ours | 16 / 500 | 0.032 | [0.01839918532363991, 0.05144676829164562] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 50 | 0.0 | xue_s5 | 31 / 500 | 0.062 | [0.042511061296385495, 0.08685259747910139] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 50 | 0.0 | xue_s11 | 26 / 500 | 0.052 | [0.03424569808276791, 0.07526637103062216] | exploratory_point_in_band |
| m2_brownian_peak1 | 800 | 50 | 0.0 | xue_s21 | 25 / 500 | 0.05 | [0.03261518014933006, 0.07292762165047896] | exploratory_point_in_band |
| spectrum_flat_b0 | 200 | 20 | 0.0 | ours | 17 / 500 | 0.034 | [0.01992860004620631, 0.0538803507360769] | exploratory_point_in_band |
| spectrum_flat_b0 | 200 | 20 | 0.0 | xue_s5 | 52 / 500 | 0.104 | [0.07865193527463435, 0.13414074842248078] | exploratory_point_high |
| spectrum_flat_b0 | 200 | 20 | 0.0 | xue_s11 | 52 / 500 | 0.104 | [0.07865193527463435, 0.13414074842248078] | exploratory_point_high |
| spectrum_flat_b0 | 200 | 20 | 0.0 | xue_s21 | 51 / 500 | 0.102 | [0.07689229322668847, 0.1319264605647195] | exploratory_point_high |
| spectrum_flat_b0 | 400 | 20 | 0.0 | ours | 20 / 500 | 0.04 | [0.024601312085545394, 0.06110260938824469] | exploratory_point_in_band |
| spectrum_flat_b0 | 400 | 20 | 0.0 | xue_s5 | 41 / 500 | 0.082 | [0.05948546373558823, 0.10959894311096288] | exploratory_point_high |
| spectrum_flat_b0 | 400 | 20 | 0.0 | xue_s11 | 37 / 500 | 0.074 | [0.052635108548995245, 0.10055887474646992] | exploratory_point_high |
| spectrum_flat_b0 | 400 | 20 | 0.0 | xue_s21 | 29 / 500 | 0.058 | [0.039183868797187785, 0.08223822089383528] | exploratory_point_in_band |
| spectrum_flat_b0 | 800 | 20 | 0.0 | ours | 26 / 500 | 0.052 | [0.03424569808276791, 0.07526637103062216] | exploratory_point_in_band |
| spectrum_flat_b0 | 800 | 20 | 0.0 | xue_s5 | 38 / 500 | 0.076 | [0.05434078124391167, 0.10282558211499361] | exploratory_point_high |
| spectrum_flat_b0 | 800 | 20 | 0.0 | xue_s11 | 26 / 500 | 0.052 | [0.03424569808276791, 0.07526637103062216] | exploratory_point_in_band |
| spectrum_flat_b0 | 800 | 20 | 0.0 | xue_s21 | 28 / 500 | 0.056 | [0.037530444475022205, 0.0799213006043601] | exploratory_point_in_band |
| spectrum_flat_b0 | 800 | 50 | 0.0 | ours | 29 / 500 | 0.058 | [0.039183868797187785, 0.08223822089383528] | exploratory_point_in_band |
| spectrum_flat_b0 | 800 | 50 | 0.0 | xue_s5 | 19 / 500 | 0.038 | [0.02303077080624761, 0.05870729046322855] | exploratory_point_in_band |
| spectrum_flat_b0 | 800 | 50 | 0.0 | xue_s11 | 15 / 500 | 0.03 | [0.016885984203873244, 0.04899822570881894] | exploratory_point_in_band |
| spectrum_flat_b0 | 800 | 50 | 0.0 | xue_s21 | 23 / 500 | 0.046 | [0.02938017539240277, 0.0682254278812379] | exploratory_point_in_band |
| spectrum_fast_b4 | 800 | 20 | 0.0 | ours | 18 / 500 | 0.036 | [0.021472856586093284, 0.05630017620179107] | exploratory_point_in_band |
| spectrum_fast_b4 | 800 | 20 | 0.0 | xue_s5 | 35 / 500 | 0.07 | [0.04923864472037879, 0.09601109159263317] | exploratory_point_in_band |
| spectrum_fast_b4 | 800 | 20 | 0.0 | xue_s11 | 20 / 500 | 0.04 | [0.024601312085545394, 0.06110260938824469] | exploratory_point_in_band |
| spectrum_fast_b4 | 800 | 20 | 0.0 | xue_s21 | 26 / 500 | 0.052 | [0.03424569808276791, 0.07526637103062216] | exploratory_point_in_band |
| m1_fourier5_peak1 | 200 | 20 | 0.15 | ours | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.15 | xue_s5 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.15 | xue_s11 | 8 / 50 | 0.16 | [0.0717007671832862, 0.2911263065951108] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.15 | xue_s21 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.3 | ours | 32 / 50 | 0.64 | [0.49193135228560125, 0.7708429331794127] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.3 | xue_s5 | 45 / 50 | 0.9 | [0.7818646335657977, 0.9667249064109775] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.3 | xue_s11 | 35 / 50 | 0.7 | [0.5539176743388217, 0.821382154335853] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.3 | xue_s21 | 31 / 50 | 0.62 | [0.47174916305285525, 0.7534989222001378] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 200 | 20 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.15 | ours | 13 / 50 | 0.26 | [0.14630058439655452, 0.40344767872806564] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.15 | xue_s5 | 21 / 50 | 0.42 | [0.28188224112369753, 0.5679395649344342] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.15 | xue_s11 | 21 / 50 | 0.42 | [0.28188224112369753, 0.5679395649344342] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.15 | xue_s21 | 12 / 50 | 0.24 | [0.13060991619745732, 0.3816907481040382] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.3 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.3 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 400 | 20 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | ours | 32 / 50 | 0.64 | [0.49193135228560125, 0.7708429331794127] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s5 | 49 / 50 | 0.98 | [0.8935304542885001, 0.9994937720169592] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s11 | 49 / 50 | 0.98 | [0.8935304542885001, 0.9994937720169592] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s21 | 47 / 50 | 0.94 | [0.8345180533962271, 0.9874514121646659] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.15 | ours | 25 / 50 | 0.5 | [0.3552729971299086, 0.6447270028700913] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.15 | xue_s5 | 48 / 50 | 0.96 | [0.8628623743960326, 0.9951185665738356] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.15 | xue_s11 | 46 / 50 | 0.92 | [0.8076572164040372, 0.9777720363450703] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.15 | xue_s21 | 39 / 50 | 0.78 | [0.6403881114342106, 0.8847341739621514] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.3 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.3 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 50 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.15 | ours | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.15 | xue_s5 | 9 / 50 | 0.18 | [0.08576207810966366, 0.31436941128565027] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.15 | xue_s11 | 6 / 50 | 0.12 | [0.04533532077366386, 0.24310131670556254] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.15 | xue_s21 | 10 / 50 | 0.2 | [0.10030223747257107, 0.33718310838348775] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.3 | ours | 31 / 50 | 0.62 | [0.47174916305285525, 0.7534989222001378] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.3 | xue_s5 | 48 / 50 | 0.96 | [0.8628623743960326, 0.9951185665738356] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.3 | xue_s21 | 49 / 50 | 0.98 | [0.8935304542885001, 0.9994937720169592] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 200 | 20 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.15 | ours | 9 / 50 | 0.18 | [0.08576207810966366, 0.31436941128565027] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.15 | xue_s5 | 27 / 50 | 0.54 | [0.39324197611692235, 0.6818508214313913] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.15 | xue_s11 | 24 / 50 | 0.48 | [0.33660509160345997, 0.6258480549209058] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.15 | xue_s21 | 18 / 50 | 0.36 | [0.22915706682058734, 0.5080686477143987] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.3 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.3 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 400 | 20 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.15 | ours | 34 / 50 | 0.68 | [0.5330061598852693, 0.8047958053371607] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s5 | 49 / 50 | 0.98 | [0.8935304542885001, 0.9994937720169592] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.15 | ours | 24 / 50 | 0.48 | [0.33660509160345997, 0.6258480549209058] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.15 | xue_s5 | 47 / 50 | 0.94 | [0.8345180533962271, 0.9874514121646659] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.15 | xue_s11 | 48 / 50 | 0.96 | [0.8628623743960326, 0.9951185665738356] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.15 | xue_s21 | 44 / 50 | 0.88 | [0.7568986832944374, 0.9546646792263361] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.3 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.3 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 50 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 200 | 20 | 0.15 | ours | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| coherent_all | 200 | 20 | 0.15 | xue_s5 | 6 / 50 | 0.12 | [0.04533532077366386, 0.24310131670556254] | not_applicable |
| coherent_all | 200 | 20 | 0.15 | xue_s11 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 200 | 20 | 0.15 | xue_s21 | 7 / 50 | 0.14 | [0.05819170034037211, 0.2673960024970084] | not_applicable |
| coherent_all | 200 | 20 | 0.3 | ours | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 200 | 20 | 0.3 | xue_s5 | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| coherent_all | 200 | 20 | 0.3 | xue_s11 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| coherent_all | 200 | 20 | 0.3 | xue_s21 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 200 | 20 | 0.45 | ours | 37 / 50 | 0.74 | [0.5965523212719344, 0.8536994156034454] | not_applicable |
| coherent_all | 200 | 20 | 0.45 | xue_s5 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| coherent_all | 200 | 20 | 0.45 | xue_s11 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 200 | 20 | 0.45 | xue_s21 | 6 / 50 | 0.12 | [0.04533532077366386, 0.24310131670556254] | not_applicable |
| coherent_all | 200 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 200 | 20 | 0.6 | xue_s5 | 8 / 50 | 0.16 | [0.0717007671832862, 0.2911263065951108] | not_applicable |
| coherent_all | 200 | 20 | 0.6 | xue_s11 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 200 | 20 | 0.6 | xue_s21 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 400 | 20 | 0.15 | ours | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| coherent_all | 400 | 20 | 0.15 | xue_s5 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 400 | 20 | 0.15 | xue_s11 | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| coherent_all | 400 | 20 | 0.15 | xue_s21 | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | ours | 34 / 50 | 0.68 | [0.5330061598852693, 0.8047958053371607] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | xue_s5 | 7 / 50 | 0.14 | [0.05819170034037211, 0.2673960024970084] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | xue_s11 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | xue_s21 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 400 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 400 | 20 | 0.45 | xue_s5 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 400 | 20 | 0.45 | xue_s11 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 400 | 20 | 0.45 | xue_s21 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | xue_s5 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | xue_s11 | 0 / 50 | 0.0 | [0.0, 0.07112173646419764] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | xue_s21 | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| coherent_all | 800 | 20 | 0.15 | ours | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 800 | 20 | 0.15 | xue_s5 | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| coherent_all | 800 | 20 | 0.15 | xue_s11 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| coherent_all | 800 | 20 | 0.15 | xue_s21 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | xue_s5 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | xue_s11 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | xue_s21 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 800 | 20 | 0.45 | xue_s5 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 800 | 20 | 0.45 | xue_s11 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 20 | 0.45 | xue_s21 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | xue_s5 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | xue_s11 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | xue_s21 | 6 / 50 | 0.12 | [0.04533532077366386, 0.24310131670556254] | not_applicable |
| coherent_all | 800 | 50 | 0.15 | ours | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 50 | 0.15 | xue_s5 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 50 | 0.15 | xue_s11 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| coherent_all | 800 | 50 | 0.15 | xue_s21 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | xue_s5 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | xue_s11 | 0 / 50 | 0.0 | [0.0, 0.07112173646419764] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | xue_s21 | 0 / 50 | 0.0 | [0.0, 0.07112173646419764] | not_applicable |
| coherent_all | 800 | 50 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 800 | 50 | 0.45 | xue_s5 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| coherent_all | 800 | 50 | 0.45 | xue_s11 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 50 | 0.45 | xue_s21 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | xue_s5 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | xue_s11 | 5 / 50 | 0.1 | [0.033275093589022475, 0.21813536643420225] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | xue_s21 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| local_fejer | 800 | 20 | 0.15 | ours | 7 / 50 | 0.14 | [0.05819170034037211, 0.2673960024970084] | not_applicable |
| local_fejer | 800 | 20 | 0.15 | xue_s5 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| local_fejer | 800 | 20 | 0.15 | xue_s11 | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| local_fejer | 800 | 20 | 0.15 | xue_s21 | 2 / 50 | 0.04 | [0.004881433426164383, 0.1371376256039674] | not_applicable |
| local_fejer | 800 | 20 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| local_fejer | 800 | 20 | 0.3 | xue_s5 | 3 / 50 | 0.06 | [0.012548587835334064, 0.16548194660377288] | not_applicable |
| local_fejer | 800 | 20 | 0.3 | xue_s11 | 1 / 50 | 0.02 | [0.0005062279830408294, 0.1064695457114999] | not_applicable |
| local_fejer | 800 | 20 | 0.3 | xue_s21 | 4 / 50 | 0.08 | [0.022227963654929767, 0.19234278359596277] | not_applicable |
| local_fejer | 800 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| local_fejer | 800 | 20 | 0.45 | xue_s5 | 29 / 50 | 0.58 | [0.4320604350655658, 0.7181177588763025] | not_applicable |
| local_fejer | 800 | 20 | 0.45 | xue_s11 | 22 / 50 | 0.44 | [0.2999072209275437, 0.5874558770583268] | not_applicable |
| local_fejer | 800 | 20 | 0.45 | xue_s21 | 13 / 50 | 0.26 | [0.14630058439655452, 0.40344767872806564] | not_applicable |
| local_fejer | 800 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| local_fejer | 800 | 20 | 0.6 | xue_s5 | 47 / 50 | 0.94 | [0.8345180533962271, 0.9874514121646659] | not_applicable |
| local_fejer | 800 | 20 | 0.6 | xue_s11 | 47 / 50 | 0.94 | [0.8345180533962271, 0.9874514121646659] | not_applicable |
| local_fejer | 800 | 20 | 0.6 | xue_s21 | 42 / 50 | 0.84 | [0.7088736934048891, 0.9282992328167138] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.15 | ours | 38 / 50 | 0.76 | [0.6183092518959619, 0.8693900838025427] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.15 | xue_s5 | 47 / 50 | 0.94 | [0.8345180533962271, 0.9874514121646659] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.15 | xue_s11 | 48 / 50 | 0.96 | [0.8628623743960326, 0.9951185665738356] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.15 | xue_s21 | 48 / 50 | 0.96 | [0.8628623743960326, 0.9951185665738356] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.3 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.3 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.3 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.3 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.45 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.45 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.45 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.45 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.6 | ours | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.6 | xue_s5 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.6 | xue_s11 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |
| spectrum_fast_b4 | 800 | 20 | 0.6 | xue_s21 | 50 / 50 | 1.0 | [0.9288782635358024, 1.0] | not_applicable |

### Model findings

- coherent_all (n=200,p=20): ours H0=exploratory_point_in_band; tau=0.15: 4.0%, tau=0.3: 8.0%, tau=0.45: 74.0%, tau=0.6: 100.0%; high-power point estimates at [0.6].
- coherent_all (n=400,p=20): ours H0=exploratory_point_in_band; tau=0.15: 4.0%, tau=0.3: 68.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.45, 0.6].
- coherent_all (n=800,p=20): ours H0=exploratory_point_in_band; tau=0.15: 10.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- coherent_all (n=800,p=50): ours H0=exploratory_point_in_band; tau=0.15: 6.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- local_fejer (n=800,p=20): ours H0=exploratory_point_in_band; tau=0.15: 14.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- m1_fourier5_peak1 (n=200,p=20): ours H0=exploratory_point_in_band; tau=0.15: 6.0%, tau=0.3: 64.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.45, 0.6].
- m1_fourier5_peak1 (n=400,p=20): ours H0=exploratory_point_in_band; tau=0.15: 26.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- m1_fourier5_peak1 (n=800,p=20): ours H0=exploratory_point_in_band; tau=0.15: 64.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- m1_fourier5_peak1 (n=800,p=50): ours H0=exploratory_point_in_band; tau=0.15: 50.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- m2_brownian_peak1 (n=200,p=20): ours H0=exploratory_point_in_band; tau=0.15: 8.0%, tau=0.3: 62.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.45, 0.6].
- m2_brownian_peak1 (n=400,p=20): ours H0=exploratory_point_in_band; tau=0.15: 18.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- m2_brownian_peak1 (n=800,p=20): ours H0=exploratory_point_in_band; tau=0.15: 68.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- m2_brownian_peak1 (n=800,p=50): ours H0=exploratory_point_in_band; tau=0.15: 48.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- spectrum_fast_b4 (n=800,p=20): ours H0=exploratory_point_in_band; tau=0.15: 76.0%, tau=0.3: 100.0%, tau=0.45: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.45, 0.6].
- coherent_all tau=0.15 sample-size trend (descriptive point estimates): n=200: 4.0%, n=400: 4.0%, n=800: 10.0%.
- coherent_all tau=0.15 channel-dimension trend (descriptive point estimates): p=20: 10.0%, p=50: 6.0%.
- coherent_all tau=0.3 sample-size trend (descriptive point estimates): n=200: 8.0%, n=400: 68.0%, n=800: 100.0%.
- coherent_all tau=0.3 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- coherent_all tau=0.45 sample-size trend (descriptive point estimates): n=200: 74.0%, n=400: 100.0%, n=800: 100.0%.
- coherent_all tau=0.45 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- coherent_all tau=0.6 sample-size trend (descriptive point estimates): n=200: 100.0%, n=400: 100.0%, n=800: 100.0%.
- coherent_all tau=0.6 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- m1_fourier5_peak1 tau=0.15 sample-size trend (descriptive point estimates): n=200: 6.0%, n=400: 26.0%, n=800: 64.0%.
- m1_fourier5_peak1 tau=0.15 channel-dimension trend (descriptive point estimates): p=20: 64.0%, p=50: 50.0%.
- m1_fourier5_peak1 tau=0.3 sample-size trend (descriptive point estimates): n=200: 64.0%, n=400: 100.0%, n=800: 100.0%.
- m1_fourier5_peak1 tau=0.3 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- m1_fourier5_peak1 tau=0.45 sample-size trend (descriptive point estimates): n=200: 100.0%, n=400: 100.0%, n=800: 100.0%.
- m1_fourier5_peak1 tau=0.45 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- m1_fourier5_peak1 tau=0.6 sample-size trend (descriptive point estimates): n=200: 100.0%, n=400: 100.0%, n=800: 100.0%.
- m1_fourier5_peak1 tau=0.6 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- m2_brownian_peak1 tau=0.15 sample-size trend (descriptive point estimates): n=200: 8.0%, n=400: 18.0%, n=800: 68.0%.
- m2_brownian_peak1 tau=0.15 channel-dimension trend (descriptive point estimates): p=20: 68.0%, p=50: 48.0%.
- m2_brownian_peak1 tau=0.3 sample-size trend (descriptive point estimates): n=200: 62.0%, n=400: 100.0%, n=800: 100.0%.
- m2_brownian_peak1 tau=0.3 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- m2_brownian_peak1 tau=0.45 sample-size trend (descriptive point estimates): n=200: 100.0%, n=400: 100.0%, n=800: 100.0%.
- m2_brownian_peak1 tau=0.45 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
- m2_brownian_peak1 tau=0.6 sample-size trend (descriptive point estimates): n=200: 100.0%, n=400: 100.0%, n=800: 100.0%.
- m2_brownian_peak1 tau=0.6 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
These are exploratory/workflow findings; the research target remains unconfirmed.
High power is an estimated rejection probability, not a guarantee. Comparative claims additionally require the locked paired intervals and both method-specific level states.
## confirm

Complete: True; completed 9500 / planned 9500.

| Model | n | p | tau | Method | Reject / valid | Rate | 95% interval | Level status |
|---|---:|---:|---:|---|---:|---:|---|---|
| m1_fourier5_peak1 | 800 | 20 | 0.0 | ours | 46 / 1000 | 0.046 | [0.0338714985476779, 0.06088355271374263] | near_nominal |
| m1_fourier5_peak1 | 800 | 20 | 0.0 | xue_s5 | 68 / 1000 | 0.068 | [0.05318809976040196, 0.08541305019143103] | unresolved |
| m1_fourier5_peak1 | 800 | 20 | 0.0 | xue_s11 | 56 / 1000 | 0.056 | [0.04257554968661718, 0.07210774628325271] | unresolved |
| m1_fourier5_peak1 | 800 | 20 | 0.0 | xue_s21 | 57 / 1000 | 0.057 | [0.043453581936958585, 0.07322272946066224] | unresolved |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | ours | 211 / 300 | 0.7033333333333334 | [0.6481450388832328, 0.7544533500276751] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s5 | 297 / 300 | 0.99 | [0.9710554887443074, 0.9979329927649077] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s11 | 293 / 300 | 0.9766666666666667 | [0.9525174349702181, 0.9905684979382053] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s21 | 271 / 300 | 0.9033333333333333 | [0.864125090171869, 0.934301425384413] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s5 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s11 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s21 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s5 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s11 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s21 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.0 | ours | 48 / 1000 | 0.048 | [0.035600265342883276, 0.06314011540150924] | near_nominal |
| m2_brownian_peak1 | 800 | 20 | 0.0 | xue_s5 | 50 / 1000 | 0.05 | [0.0373353976046618, 0.06539048791549364] | near_nominal |
| m2_brownian_peak1 | 800 | 20 | 0.0 | xue_s11 | 54 / 1000 | 0.054 | [0.040823351125630736, 0.06987400557706737] | near_nominal |
| m2_brownian_peak1 | 800 | 20 | 0.0 | xue_s21 | 48 / 1000 | 0.048 | [0.035600265342883276, 0.06314011540150924] | near_nominal |
| m2_brownian_peak1 | 800 | 20 | 0.15 | ours | 208 / 300 | 0.6933333333333334 | [0.6377610406115359, 0.7450388510010117] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s5 | 293 / 300 | 0.9766666666666667 | [0.9525174349702181, 0.9905684979382053] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s11 | 295 / 300 | 0.9833333333333333 | [0.9615362550350036, 0.9945667946848947] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s21 | 296 / 300 | 0.9866666666666667 | [0.9662151037380822, 0.9963554859479334] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s5 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s11 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s21 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s5 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s11 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s21 | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| coherent_all | 800 | 20 | 0.0 | ours | 29 / 1000 | 0.029 | [0.019505937324384624, 0.041384719116401916] | unresolved |
| coherent_all | 800 | 20 | 0.0 | xue_s5 | 54 / 1000 | 0.054 | [0.040823351125630736, 0.06987400557706737] | near_nominal |
| coherent_all | 800 | 20 | 0.0 | xue_s11 | 58 / 1000 | 0.058 | [0.0443328602528207, 0.0743364953823516] | unresolved |
| coherent_all | 800 | 20 | 0.0 | xue_s21 | 44 / 1000 | 0.044 | [0.032149497010871414, 0.058620419206330925] | near_nominal |
| coherent_all | 800 | 20 | 0.15 | ours | 33 / 300 | 0.11 | [0.07693896352761474, 0.15100322157472484] | not_applicable |
| coherent_all | 800 | 20 | 0.15 | xue_s5 | 14 / 300 | 0.04666666666666667 | [0.02574464946723095, 0.0770598381063587] | not_applicable |
| coherent_all | 800 | 20 | 0.15 | xue_s11 | 18 / 300 | 0.06 | [0.0359438744151388, 0.09317029607198862] | not_applicable |
| coherent_all | 800 | 20 | 0.15 | xue_s21 | 16 / 300 | 0.05333333333333334 | [0.030788319773478064, 0.08516676490951426] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | xue_s5 | 13 / 300 | 0.043333333333333335 | [0.02327184100468237, 0.0729614642202821] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | xue_s11 | 18 / 300 | 0.06 | [0.0359438744151388, 0.09317029607198862] | not_applicable |
| coherent_all | 800 | 20 | 0.3 | xue_s21 | 14 / 300 | 0.04666666666666667 | [0.02574464946723095, 0.0770598381063587] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | xue_s5 | 18 / 300 | 0.06 | [0.0359438744151388, 0.09317029607198862] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | xue_s11 | 23 / 300 | 0.07666666666666666 | [0.04921878387567445, 0.11281811536048231] | not_applicable |
| coherent_all | 800 | 20 | 0.6 | xue_s21 | 23 / 300 | 0.07666666666666666 | [0.04921878387567445, 0.11281811536048231] | not_applicable |
| coherent_all | 400 | 20 | 0.0 | ours | 41 / 1000 | 0.041 | [0.02958016853403611, 0.05521245931529931] | unresolved |
| coherent_all | 400 | 20 | 0.0 | xue_s5 | 50 / 1000 | 0.05 | [0.0373353976046618, 0.06539048791549364] | near_nominal |
| coherent_all | 400 | 20 | 0.0 | xue_s11 | 74 / 1000 | 0.074 | [0.05854944426065268, 0.09201173601424907] | unresolved |
| coherent_all | 400 | 20 | 0.0 | xue_s21 | 58 / 1000 | 0.058 | [0.0443328602528207, 0.0743364953823516] | unresolved |
| coherent_all | 400 | 20 | 0.15 | ours | 13 / 300 | 0.043333333333333335 | [0.02327184100468237, 0.0729614642202821] | not_applicable |
| coherent_all | 400 | 20 | 0.15 | xue_s5 | 24 / 300 | 0.08 | [0.05192863933660696, 0.11669591648491236] | not_applicable |
| coherent_all | 400 | 20 | 0.15 | xue_s11 | 27 / 300 | 0.09 | [0.06014952983765152, 0.12824250877329826] | not_applicable |
| coherent_all | 400 | 20 | 0.15 | xue_s21 | 25 / 300 | 0.08333333333333333 | [0.05465427587840893, 0.12055873687593488] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | ours | 213 / 300 | 0.71 | [0.6550839107544896, 0.76071332550029] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | xue_s5 | 13 / 300 | 0.043333333333333335 | [0.02327184100468237, 0.0729614642202821] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | xue_s11 | 19 / 300 | 0.06333333333333334 | [0.03855801982837607, 0.0971381966071201] | not_applicable |
| coherent_all | 400 | 20 | 0.3 | xue_s21 | 21 / 300 | 0.07 | [0.0438503447554294, 0.1050139995500499] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | xue_s5 | 18 / 300 | 0.06 | [0.0359438744151388, 0.09317029607198862] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | xue_s11 | 13 / 300 | 0.043333333333333335 | [0.02327184100468237, 0.0729614642202821] | not_applicable |
| coherent_all | 400 | 20 | 0.6 | xue_s21 | 10 / 300 | 0.03333333333333333 | [0.016098167562619323, 0.0604453222012656] | not_applicable |
| coherent_all | 800 | 50 | 0.0 | ours | 42 / 1000 | 0.042 | [0.03043470626314002, 0.05635029157574476] | near_nominal |
| coherent_all | 800 | 50 | 0.0 | xue_s5 | 55 / 1000 | 0.055 | [0.04169879507953598, 0.07099151554205749] | unresolved |
| coherent_all | 800 | 50 | 0.0 | xue_s11 | 44 / 1000 | 0.044 | [0.032149497010871414, 0.058620419206330925] | near_nominal |
| coherent_all | 800 | 50 | 0.0 | xue_s21 | 39 / 1000 | 0.039 | [0.027877148795336416, 0.05293093578544508] | unresolved |
| coherent_all | 800 | 50 | 0.15 | ours | 26 / 300 | 0.08666666666666667 | [0.05739483254705113, 0.12440736286509173] | not_applicable |
| coherent_all | 800 | 50 | 0.15 | xue_s5 | 14 / 300 | 0.04666666666666667 | [0.02574464946723095, 0.0770598381063587] | not_applicable |
| coherent_all | 800 | 50 | 0.15 | xue_s11 | 9 / 300 | 0.03 | [0.013807819555525978, 0.056183548241615776] | not_applicable |
| coherent_all | 800 | 50 | 0.15 | xue_s21 | 13 / 300 | 0.043333333333333335 | [0.02327184100468237, 0.0729614642202821] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | ours | 299 / 300 | 0.9966666666666667 | [0.9815687479519322, 0.9999156108676822] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | xue_s5 | 14 / 300 | 0.04666666666666667 | [0.02574464946723095, 0.0770598381063587] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | xue_s11 | 15 / 300 | 0.05 | [0.028251201968496384, 0.08112735717076422] | not_applicable |
| coherent_all | 800 | 50 | 0.3 | xue_s21 | 11 / 300 | 0.03666666666666667 | [0.018443460812459775, 0.0646585181962982] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | ours | 300 / 300 | 1.0 | [0.9877790253057065, 1.0] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | xue_s5 | 15 / 300 | 0.05 | [0.028251201968496384, 0.08112735717076422] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | xue_s11 | 15 / 300 | 0.05 | [0.028251201968496384, 0.08112735717076422] | not_applicable |
| coherent_all | 800 | 50 | 0.6 | xue_s21 | 16 / 300 | 0.05333333333333334 | [0.030788319773478064, 0.08516676490951426] | not_applicable |

### Model findings

- coherent_all (n=400,p=20): ours H0=unresolved; tau=0.15: 4.3%, tau=0.3: 71.0%, tau=0.6: 100.0%; high-power point estimates at [0.6].
- coherent_all (n=800,p=20): ours H0=unresolved; tau=0.15: 11.0%, tau=0.3: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.6].
- coherent_all (n=800,p=50): ours H0=near_nominal; tau=0.15: 8.7%, tau=0.3: 99.7%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.6].
- m1_fourier5_peak1 (n=800,p=20): ours H0=near_nominal; tau=0.15: 70.3%, tau=0.3: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.6].
- m2_brownian_peak1 (n=800,p=20): ours H0=near_nominal; tau=0.15: 69.3%, tau=0.3: 100.0%, tau=0.6: 100.0%; high-power point estimates at [0.3, 0.6].
- coherent_all tau=0.15 sample-size trend (descriptive point estimates): n=400: 4.3%, n=800: 11.0%.
- coherent_all tau=0.15 channel-dimension trend (descriptive point estimates): p=20: 11.0%, p=50: 8.7%.
- coherent_all tau=0.3 sample-size trend (descriptive point estimates): n=400: 71.0%, n=800: 100.0%.
- coherent_all tau=0.3 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 99.7%.
- coherent_all tau=0.6 sample-size trend (descriptive point estimates): n=400: 100.0%, n=800: 100.0%.
- coherent_all tau=0.6 channel-dimension trend (descriptive point estimates): p=20: 100.0%, p=50: 100.0%.
Units with working level band and high power point estimates: coherent_all(n=800,p=50), m1_fourier5_peak1(n=800,p=20), m2_brownian_peak1(n=800,p=20).
High power is an estimated rejection probability, not a guarantee. Comparative claims additionally require the locked paired intervals and both method-specific level states.

## All fixed paired comparisons

| Phase | Model | n | p | tau | Comparator | Difference | Adjusted interval | Ours / comparator level | Label | Interpretation |
|---|---|---:|---:|---:|---|---:|---|---|---|---|
| smoke | m1_fourier5_peak1 | 12 | 4 | 0.3 | xue_s5 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | m1_fourier5_peak1 | 12 | 4 | 0.3 | xue_s11 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | m1_fourier5_peak1 | 12 | 4 | 0.3 | xue_s21 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | m2_brownian_peak1 | 12 | 4 | 0.3 | xue_s5 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | m2_brownian_peak1 | 12 | 4 | 0.3 | xue_s11 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | m2_brownian_peak1 | 12 | 4 | 0.3 | xue_s21 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | coherent_all | 12 | 4 | 0.3 | xue_s5 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | coherent_all | 12 | 4 | 0.3 | xue_s11 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | coherent_all | 12 | 4 | 0.3 | xue_s21 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | local_fejer | 12 | 4 | 0.3 | xue_s5 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | local_fejer | 12 | 4 | 0.3 | xue_s11 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | local_fejer | 12 | 4 | 0.3 | xue_s21 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | spectrum_fast_b4 | 12 | 4 | 0.3 | xue_s5 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | spectrum_fast_b4 | 12 | 4 | 0.3 | xue_s11 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| smoke | spectrum_fast_b4 | 12 | 4 | 0.3 | xue_s21 | -1.0 | [-1.0, 0.9983333333333333] | missing / missing | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.15 | xue_s5 | -0.02 | [-0.2850450331015264, 0.25118157339596403] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.15 | xue_s11 | -0.1 | [-0.39620460386717987, 0.2320751700580532] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.15 | xue_s21 | 0.0 | [-0.2837031285203296, 0.2837031285203296] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.3 | xue_s5 | -0.26 | [-0.5756372106250767, 0.15270415170464585] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.3 | xue_s11 | -0.06 | [-0.47660679133550743, 0.3795776878340572] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.3 | xue_s21 | 0.02 | [-0.41320174036817525, 0.4455442910019365] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 200 | 20 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.15 | xue_s5 | -0.16 | [-0.5087181556196052, 0.24967913105076636] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.15 | xue_s11 | -0.16 | [-0.5087181556196052, 0.24967913105076636] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.15 | xue_s21 | 0.02 | [-0.36825652479432935, 0.400592848095825] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.3 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.3 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.3 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 400 | 20 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s5 | -0.34 | [-0.6153473437472663, 0.0477602205901512] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s11 | -0.34 | [-0.6153473437472663, 0.0477602205901512] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s21 | -0.3 | [-0.6150999145515295, 0.127391187781092] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.15 | xue_s5 | -0.46 | [-0.7406769228577302, -0.01036238352405755] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.15 | xue_s11 | -0.42 | [-0.7236691730907279, 0.041519465793242366] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.15 | xue_s21 | -0.28 | [-0.6444533397103845, 0.19129827769647015] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.3 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.3 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.3 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m1_fourier5_peak1 | 800 | 50 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.15 | xue_s5 | -0.1 | [-0.39620460386717987, 0.2320751700580532] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.15 | xue_s11 | -0.04 | [-0.3151433567567838, 0.24835582340163626] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.15 | xue_s21 | -0.12 | [-0.4210411560149327, 0.22457539890431033] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.3 | xue_s5 | -0.34 | [-0.6153473437472663, 0.0477602205901512] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.3 | xue_s11 | -0.38 | [-0.6531082890047828, 0.02072238352515368] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.3 | xue_s21 | -0.36 | [-0.6531068008552886, 0.06412533655219035] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 200 | 20 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.15 | xue_s5 | -0.36 | [-0.6711383873759702, 0.08622479343098122] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.15 | xue_s11 | -0.3 | [-0.6150999145515295, 0.127391187781092] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.15 | xue_s21 | -0.18 | [-0.530146306273618, 0.2387469733763105] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.3 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.3 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.3 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 400 | 20 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s5 | -0.3 | [-0.5758846398208135, 0.07307318451370504] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s11 | -0.32 | [-0.5958372337505988, 0.060641236823048006] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s21 | -0.32 | [-0.5958372337505988, 0.060641236823048006] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.15 | xue_s5 | -0.46 | [-0.7239166022864647, -0.03811150139769845] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.15 | xue_s11 | -0.48 | [-0.7406784110072244, -0.05376533655109422] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.15 | xue_s21 | -0.4 | [-0.671385816571707, 0.006593826240040401] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.3 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.3 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.3 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | m2_brownian_peak1 | 800 | 50 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.15 | xue_s5 | -0.08 | [-0.3704051770521141, 0.2386342023828076] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.15 | xue_s11 | -0.04 | [-0.3151433567567838, 0.24835582340163626] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.15 | xue_s21 | -0.1 | [-0.39620460386717987, 0.2320751700580532] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.3 | xue_s5 | 0.04 | [-0.24835582340163626, 0.3151433567567838] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.3 | xue_s11 | 0.06 | [-0.2121278092377321, 0.31538929780302644] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.3 | xue_s21 | 0.0 | [-0.3109757021812592, 0.3109757021812592] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.45 | xue_s5 | 0.72 | [0.2713920334875655, 0.9118937900347783] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.45 | xue_s11 | 0.64 | [0.1513918590765035, 0.8872538676453543] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.45 | xue_s21 | 0.62 | [0.11887030395213793, 0.8859119630641574] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.6 | xue_s5 | 0.84 | [0.4055714748073735, 0.9718044917314126] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.6 | xue_s11 | 0.9 | [0.48314422586476974, 0.9913450507056017] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 200 | 20 | 0.6 | xue_s21 | 0.9 | [0.48314422586476974, 0.9913450507056017] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.15 | xue_s5 | -0.04 | [-0.3151433567567838, 0.24835582340163626] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.15 | xue_s11 | 0.0 | [-0.25252347797716085, 0.25252347797716085] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.15 | xue_s21 | 0.0 | [-0.25252347797716085, 0.25252347797716085] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.3 | xue_s5 | 0.54 | [0.04332172113102961, 0.8318645524811498] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.3 | xue_s11 | 0.58 | [0.13758504488523693, 0.8189335443607614] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.3 | xue_s21 | 0.58 | [0.09412080382231941, 0.84733501434746] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.45 | xue_s5 | 0.92 | [0.5114692740655225, 0.9955849162287385] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.45 | xue_s11 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.45 | xue_s21 | 0.92 | [0.5114692740655225, 0.9955849162287385] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.6 | xue_s5 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.6 | xue_s11 | 1.0 | [0.653720120036086, 1.0] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 400 | 20 | 0.6 | xue_s21 | 0.96 | [0.5740891528451453, 0.9997525708042632] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.15 | xue_s5 | 0.06 | [-0.2121278092377321, 0.31538929780302644] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.15 | xue_s11 | 0.08 | [-0.16872485621069544, 0.3153907859525207] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.15 | xue_s21 | 0.04 | [-0.2766375130028651, 0.3421265003763397] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.3 | xue_s5 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.3 | xue_s11 | 0.98 | [0.6103171670090495, 0.9999985118505058] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.3 | xue_s21 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.45 | xue_s5 | 0.9 | [0.48314422586476974, 0.9913450507056017] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.45 | xue_s11 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.45 | xue_s21 | 0.92 | [0.5114692740655225, 0.9955849162287385] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.6 | xue_s5 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.6 | xue_s11 | 0.9 | [0.48314422586476974, 0.9913450507056017] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 20 | 0.6 | xue_s21 | 0.88 | [0.45620745377019206, 0.9858632952099099] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.15 | xue_s5 | 0.0 | [-0.2837031285203296, 0.2837031285203296] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.15 | xue_s11 | -0.02 | [-0.2850450331015264, 0.25118157339596403] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.15 | xue_s21 | 0.04 | [-0.2149535592320599, 0.28529097414776905] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.3 | xue_s5 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.3 | xue_s11 | 1.0 | [0.653720120036086, 1.0] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.3 | xue_s21 | 1.0 | [0.653720120036086, 1.0] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.45 | xue_s5 | 0.98 | [0.6103171670090495, 0.9999985118505058] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.45 | xue_s11 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.45 | xue_s21 | 0.98 | [0.6103171670090495, 0.9999985118505058] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.6 | xue_s5 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.6 | xue_s11 | 0.9 | [0.48314422586476974, 0.9913450507056017] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | coherent_all | 800 | 50 | 0.6 | xue_s21 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.15 | xue_s5 | 0.06 | [-0.27115575750717313, 0.3690632724709173] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.15 | xue_s11 | 0.1 | [-0.20240618821890347, 0.37065111809835677] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.15 | xue_s21 | 0.1 | [-0.20240618821890347, 0.37065111809835677] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.3 | xue_s5 | 0.94 | [0.5415675977207799, 0.9984106662230663] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.3 | xue_s11 | 0.98 | [0.6103171670090495, 0.9999985118505058] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.3 | xue_s21 | 0.92 | [0.5114692740655225, 0.9955849162287385] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.45 | xue_s5 | 0.42 | [0.007926515657281724, 0.6892750151328062] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.45 | xue_s11 | 0.56 | [0.12007665063197626, 0.8040296666051113] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.45 | xue_s21 | 0.74 | [0.2922986699731635, 0.9233561874237899] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.6 | xue_s5 | 0.06 | [-0.17155060620502322, 0.2852924622972633] | exploratory_point_in_band / exploratory_point_high | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.6 | xue_s11 | 0.06 | [-0.17155060620502322, 0.2852924622972633] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | local_fejer | 800 | 20 | 0.6 | xue_s21 | 0.16 | [-0.14494443171336951, 0.4212885852106696] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.15 | xue_s5 | -0.18 | [-0.46854865404093327, 0.1709419736223247] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.15 | xue_s11 | -0.2 | [-0.4685501421904275, 0.12753902059528802] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.15 | xue_s21 | -0.2 | [-0.4911437222391111, 0.16119449118674137] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.3 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.3 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.3 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.45 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.45 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.45 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.6 | xue_s5 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.6 | xue_s11 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| pilot | spectrum_fast_b4 | 800 | 20 | 0.6 | xue_s21 | 0.0 | [-0.17313993998195693, 0.17313993998195693] | exploratory_point_in_band / exploratory_point_in_band | exploratory_only | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s5 | -0.2866666666666667 | [-0.3870663733134631, -0.16974954062668293] | near_nominal / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s11 | -0.2733333333333333 | [-0.3763401272297945, -0.15415242261695886] | near_nominal / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.15 | xue_s21 | -0.2 | [-0.3233696271646883, -0.06493867597643944] | near_nominal / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s5 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / unresolved | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s11 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / unresolved | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.3 | xue_s21 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / unresolved | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s5 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / unresolved | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s11 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / unresolved | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | m1_fourier5_peak1 | 800 | 20 | 0.6 | xue_s21 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / unresolved | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s5 | -0.2833333333333333 | [-0.3799745900229494, -0.17187009658418984] | near_nominal / near_nominal | insufficient_evidence | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s11 | -0.29 | [-0.39060405933130743, -0.17269152370532825] | near_nominal / near_nominal | insufficient_evidence | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.15 | xue_s21 | -0.29333333333333333 | [-0.3906049853854292, -0.18067856619614178] | near_nominal / near_nominal | insufficient_evidence | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s5 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / near_nominal | rejection_probability_noninferior | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s11 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / near_nominal | rejection_probability_noninferior | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.3 | xue_s21 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / near_nominal | rejection_probability_noninferior | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s5 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / near_nominal | rejection_probability_noninferior | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s11 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / near_nominal | rejection_probability_noninferior | within_working_calibration_band |
| confirm | m2_brownian_peak1 | 800 | 20 | 0.6 | xue_s21 | 0.0 | [-0.026926471132856872, 0.026926471132856872] | near_nominal / near_nominal | rejection_probability_noninferior | within_working_calibration_band |
| confirm | coherent_all | 800 | 20 | 0.15 | xue_s5 | 0.06333333333333334 | [-0.03980725434456066, 0.16254994077613316] | unresolved / near_nominal | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.15 | xue_s11 | 0.05 | [-0.056201678015516066, 0.15313388811191858] | unresolved / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.15 | xue_s21 | 0.056666666666666664 | [-0.049219756950490745, 0.15907119294094918] | unresolved / near_nominal | rejection_probability_noninferior | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.3 | xue_s5 | 0.9566666666666667 | [0.8738969674268996, 0.9864641859197173] | unresolved / near_nominal | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.3 | xue_s11 | 0.94 | [0.8512960205226038, 0.9767950472095251] | unresolved / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.3 | xue_s21 | 0.9533333333333334 | [0.8692805935872645, 0.9846307931323769] | unresolved / near_nominal | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.6 | xue_s5 | 0.94 | [0.8512960205226038, 0.9767950472095251] | unresolved / near_nominal | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.6 | xue_s11 | 0.9233333333333333 | [0.8296516439022369, 0.9661300726642394] | unresolved / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 20 | 0.6 | xue_s21 | 0.9233333333333333 | [0.8296516439022369, 0.9661300726642394] | unresolved / near_nominal | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.15 | xue_s5 | -0.03666666666666667 | [-0.12909738422690456, 0.05809086080635449] | unresolved / near_nominal | insufficient_evidence | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.15 | xue_s11 | -0.04666666666666667 | [-0.1418196748153449, 0.05141787959162608] | unresolved / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.15 | xue_s21 | -0.04 | [-0.13834092698016093, 0.06083038219755617] | unresolved / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.3 | xue_s5 | 0.6666666666666666 | [0.5298676992328957, 0.7652560925398019] | unresolved / near_nominal | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.3 | xue_s11 | 0.6466666666666666 | [0.49774477776818377, 0.7587830809666959] | unresolved / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.3 | xue_s21 | 0.64 | [0.48936970682730047, 0.7542409736738576] | unresolved / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.6 | xue_s5 | 0.94 | [0.8512960205226038, 0.9767950472095251] | unresolved / near_nominal | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.6 | xue_s11 | 0.9566666666666667 | [0.8738969674268996, 0.9864641859197173] | unresolved / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 400 | 20 | 0.6 | xue_s21 | 0.9666666666666667 | [0.8881198988264383, 0.9915733093711009] | unresolved / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 50 | 0.15 | xue_s5 | 0.04 | [-0.06083038219755617, 0.13834092698016093] | near_nominal / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 50 | 0.15 | xue_s11 | 0.056666666666666664 | [-0.0367292962865467, 0.1464421239979053] | near_nominal / near_nominal | rejection_probability_noninferior | within_working_calibration_band |
| confirm | coherent_all | 800 | 50 | 0.15 | xue_s21 | 0.043333333333333335 | [-0.058553810542005286, 0.1425311522279911] | near_nominal / unresolved | insufficient_evidence | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 50 | 0.3 | xue_s5 | 0.95 | [0.8612935510964509, 0.9846298670782551] | near_nominal / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 50 | 0.3 | xue_s11 | 0.9466666666666667 | [0.8602003312276936, 0.9808046863596109] | near_nominal / near_nominal | rejection_probability_positive | within_working_calibration_band |
| confirm | coherent_all | 800 | 50 | 0.3 | xue_s21 | 0.96 | [0.8785711048342226, 0.9882371625732578] | near_nominal / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 50 | 0.6 | xue_s5 | 0.95 | [0.8647165749540968, 0.9827426818964847] | near_nominal / unresolved | rejection_probability_positive | nominal_rejection_probability_only |
| confirm | coherent_all | 800 | 50 | 0.6 | xue_s11 | 0.95 | [0.8647165749540968, 0.9827426818964847] | near_nominal / near_nominal | rejection_probability_positive | within_working_calibration_band |
| confirm | coherent_all | 800 | 50 | 0.6 | xue_s21 | 0.9466666666666667 | [0.8602003312276936, 0.9808046863596109] | near_nominal / unresolved | rejection_probability_positive | nominal_rejection_probability_only |

## Locked selection

Extension model: coherent_all. All three mandatory anchors retained.

## Evidence limits

M1 s5 omits the fifth latent basis; s11/s21 cover it. s21 covers q20 latent Fourier signals, but not rank63 Brownian or all measurement noise.
Coherent/local share the same flat H0 only within the same shape and phase; repeated references are not independent H0 evidence.
Only complete independent confirmation supports confirmatory rejection-probability labels. Calibration warnings restrict interpretation, not locked computation.
Without full confirmation, whether the research target is met remains unresolved; all failures and unfinished cells are retained.
