---
title: "Preference Fine-Tuning of LLMs Should Leverage Suboptimal, On-Policy Data"
description: "Notes on on-policy sampling, sample reuse, and negative gradients in preference fine-tuning."
summary: "On-policy sampling and negative gradients improve preference fine-tuning. Notes on the experiments and mode-seeking objectives."
date: "2024-05-09"
layout: research
tags: ["RLHF"]
params:
  math: true
---

> TL;DR: 1) on-policy sampling + 2) negative gradients → mode-seeking objectives → better efficiency

{{< research-figure src="Untitled.png" alt="Overview of on-policy sampling, negative gradients, and three preference-data configurations" caption="On-policy sampling and negative gradients under different reward and preference-data configurations." wide=true >}}

{{< research-contents >}}

## Characterizing preference fine-tuning methods

Recall that the objective of typical preference fine-tuning procedures is:

$$
\max _{\pi_\theta} \mathbb{E}_{\boldsymbol{x} \sim \mathcal{D}_{\text {pref }}, \boldsymbol{y} \sim \pi_\theta(\cdot \mid x)}\left[r^*(\boldsymbol{x}, \boldsymbol{y})\right]-\beta \mathbb{D}_{\mathrm{KL}}\left[\pi_\theta(\cdot \mid \boldsymbol{x}) \| \pi_{\text {ref }}(\cdot \mid \boldsymbol{x})\right]
$$

Since access to ground-truth rewards is not scalable, most approaches use a surrogate reward model $r_\phi$. **Reward modeling is not the focus of this work.**

Existing approaches mainly differentiate in these aspects:

1. **on-policy sampling**: an explicit sampling of new responses from the policy (e.g., PPO, REINFORCE) or purely learning from offline data (e.g., RWR, DPO, IPO)
2. **on-policy sample reuse**: for only those approaches that perform on-policy sampling, whether the approach makes more than one gradient update on a given prompt-response$(x,y)$ pair (e.g., exactly 1 update for REINFORCE, ≥ 1 for PPO, online RWR)
3. **negative gradient**: whether the approach explicitly minimizes a loss that attempts to “pushdown” likelihood on certain responses by multiplying the gradient of their likelihood with a negative coefficient (e.g., contrastive methods such as DPO; RL methods REINFORCE, PPO)

{{< research-interactive src="Untitled_1.png" data="methods" alt="Comparison of fine-tuning methods by on-policy sampling, sample reuse, and negative gradients" caption="A comparison of the three ingredients across preference fine-tuning methods." >}}

## Experiments

To systematically analyze the behavior of fine-tuning methods, a generic algorithmic framework is introduced:

{{< research-figure src="Untitled_2.png" alt="Pseudocode for a unified fine-tuning algorithm" caption="The unified fine-tuning framework used to vary sampling, sample reuse, and the learning objective." >}}

Notes:

1. To study **on-policy sampling**, we can vary the total number of samples $B$ used at each training iteration
2. For **sample reuse**, we can vary the number of gradient steps $T$ performed at each training iteration
3. **Negative gradient** depends on the specific fine-tuning method

### Setup

**Datasets and tasks**

1. Didactic bandit: simple bandit problem with controllable ground-truth reward function and combinatorial response space
2. Synthetic LLM: used to study the impact of coverage conditions and geometric relationships on different fine-tuning algorithms
3. Full-Scale LLM: real experiments on AlpacaFarm and UltraFeedback

**Coverage conditions and geometric relationships**

In synthetic LLM tasks, coverage conditions and geometric relationships are considered:

1. the geometric alignment between the ground-truth reward function $r^*$ and the reference policy $\pi_\mathrm{ref}$.
2. the coverage of the preference data used to train the surrogate reward model $r_\phi$ relative to the reference policy $\pi_\mathrm{ref}$.

{{< research-interactive src="Untitled_3.png" data="coverage" alt="Synthetic conditions defined by reward alignment and preference-data coverage" caption="Synthetic task configurations, defined by reward alignment and preference-data coverage." >}}

### Observation 1: On-policy sampling generally improves performance and efficiency

Sampling more frequently (smaller $B$) shows clear performance improvements.

{{< research-interactive src="Untitled_4.png" data="sampling" alt="AlpacaFarm performance under different sampling batch sizes" caption="Performance on AlpacaFarm with varying batch sizes." wide=true >}}

The improvement is more noticeable when the optimal policy is far away from the reference policy.

{{< research-interactive src="Untitled_5.png" data="bandit-setup" alt="Setup of the didactic bandit problem" caption="Didactic bandit problem." >}}

{{< research-interactive src="Untitled_6.png" data="bandit" alt="Effects of on-policy sampling in bandit problems" caption="On-policy sampling on bandit problems." wide=true >}}

### Observation 2: sample reuse can enable leveraging off-policy data

For PPO, some sample reuse can improve sample efficiency, but excessive sample reuse can hurt performance.

{{< research-interactive src="Untitled_7.png" data="reuse" alt="PPO and best-of-N performance with different amounts of sample reuse" caption="PPO and best-of-N respond differently to sample reuse." wide=true >}}

### Observation 3: negative gradient enables faster convergence

{{< research-interactive src="Untitled_8.png" data="negative" alt="Negative-gradient ablations on AlpacaFarm and UltraFeedback" caption="Negative gradients in AlpacaFarm (left) and UltraFeedback (right)." wide=true >}}

{{< research-interactive src="Untitled_9.png" data="likelihood" alt="Likelihoods of preferred and dispreferred responses with and without negative gradients" caption="Negative gradients increase the gap between the likelihoods of preferred and dispreferred responses." wide=true >}}

### Observation 4: on-policy sampling and negative gradients are complementary

{{< research-interactive src="Untitled_10.png" data="complementary" alt="Fine-tuning results across min-length, skew-length, and mode-length tasks" caption="Online DPO performs best when the optimal and reference policies are far apart (min length and skew length). The algorithms perform similarly when the two policies are close (mode length)." wide=true >}}

## Theoretical intuition: mode-seeking vs mode-covering

Main arguments:

1. on-policy algorithms are mode-seeking as they optimize the regularized reverse-KL objective
2. if the negative responses are chosen appropriately, then the contrastive update accelerates the rate of increase of probability mass on the preferred responses and exhibits mode-seeking behavior

{{< research-interactive src="Untitled_11.png" data="kl" alt="Categorical toy distributions comparing forward and reverse KL updates" caption="An example contrasting mode-seeking (reverse KL) and mode-covering (forward KL) objectives." >}}

Paper: [Tajwar et al. (2024)](https://arxiv.org/abs/2404.14367).
