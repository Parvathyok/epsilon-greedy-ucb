# Methodology

## Reward model

Ten actions; independent Bernoulli rewards. Well-separated probabilities:

```text
[0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.70]
```

Closely matched probabilities:

```text
[0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.50]
```

The reversal scenario uses the first vector through round 5,000 and its reverse from round 5,001. Policies receive no reset or change notification.

## Rules

- Initialize each action once in ascending order. This also applies to the baselines.
- ε-greedy explores uniformly among all ten actions with probability ε, including the greedy action.
- Greedy and UCB score ties are broken uniformly at random.
- UCB1 uses `Q + sqrt(2 * ln(t) / N)` before round t.
- The primary estimator is the incremental sample mean.
- An additional reversal diagnostic uses ε = 0.10 with a constant update rate α = 0.10 from initialization onward.

Main policy order: uniform random, greedy, ε-greedy at 0.10, UCB1; append constant-step ε-greedy for the reversal.

## Random streams

Python 3.12.14, NumPy 2.3.5; NumPy `default_rng(SeedSequence(...))`.

For scenario seed s, environment stream: `[s, 0]`. Policy j (zero based) stream: `[s, j+1]`. Every round, the environment draws a matrix of shape `(runs, 10)`. All policies use that matrix as potential rewards, and receive only the chosen column of their own run. The complete source fixes the random-call order.

Main runs: 500, horizon: 10,000. Seeds: 20261111 (well-separated), 20261112 (closely matched), 20261113 (reversal).

Sensitivity runs: 300, horizon: 5,000. Seeds: 20262111 (well-separated), 20262112 (closely matched). Policy order: ε = .01, .05, .10, .20; decay `min(1, 1/sqrt(t))`; UCB c = .25, .50, 1, sqrt(2), 2.

## Evaluation

Pseudo-regret sums `best_mean - chosen_mean`. For changing rewards, both means are evaluated at the current time. Reward is the actual observed total divided by the horizon. Optimal selection is measured over all rounds and over the last min(1000, horizon) rounds.

Intervals: mean ± 1.96 × sample standard deviation / sqrt(run count). They describe Monte Carlo variation for a fixed scenario. Primary paired differences subtract regrets within runs before calculating their interval. Learning-curve bands are pointwise. Sensitivity comparisons are exploratory, without multiple-comparison correction or a separate tuning holdout.

## Limits

The experiment uses synthetic fixed vectors, one action count, two stationary gap profiles and one abrupt change. It does not represent all nonstationary processes, real users, costs, contexts or delays. A smaller UCB coefficient is a different policy and is not covered by the stated UCB1 coefficient-specific guarantee.
