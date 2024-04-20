---
title: "An Emulator for Fine-tuning Large Language Models using Small Language Models"

date: "2024-02-05"

tags: ["Weak-to-strong Generalization"]

params:
  math: true

---

> TL;DR: we can transplant **>80%** instruction-following performance from small models to large models, **without actually tuning them**.
> 

![Untitled](Untitled.png)

{{< table_of_contents >}}

# Emulated finetuning (EFT)

The DPO authors provide a nice intuition for EFT, based on a **model-as-rm** perspective.

## A model-as-rm perspective

Recall that an RLHF-finetuned model optimizes the following objective:

$$
\pi_{\mathrm{ft}}=\pi^*\left(r, \pi_{\mathrm{ref}}\right)=\underset{\pi}{\arg \max } \underset{x \sim p(x), y \sim \pi(\cdot \mid x)}{\mathbb{E}}\left[r(x, y)-\beta \mathrm{KL}\left(\pi(\cdot \mid x) \| \pi_{\mathrm{ref}}(\cdot \mid x)\right)\right]
$$

The closed-form solution is given by

$$
\pi^*\left(r, \pi_{\mathrm{ref}}\right)(y \mid x)=\frac{1}{Z(x)} \pi_{\mathrm{ref}}(y \mid x) \exp \left(\frac{1}{\beta} r(x, y)\right)
$$

The main idea of this paper is as follows: *any finetuned models, regardless of whether they are RLHF-finetuned or not, can be regarded as solutions to the KL-constrained RL problem with respect to certain reward functions.*

$$
\pi_{\mathrm{ft}}(y \mid x)=\pi_{\mathrm{ref}}(y \mid x) \exp (\frac{1}{\beta} \underbrace{\beta \log \frac{\pi_{\mathrm{ft}}(y \mid x)}{\pi_{\mathrm{ref}}(y \mid x)}}_{\text{Implicit reward}})
$$

From this interpretation, we have the following insights:

1. Pretrained knowledge is represented in the base log probabilities, and it could dominant the result.
2. Every finetuned model can be seen as a reward model (also in [DPO](https://arxiv.org/abs/2305.18290)), and reward models are **transferable** across base models.

## EFT for scale decoupling

These insights provide a conceptual tool to consider **scale decoupling**, where a $M$-scaled reward function are distilled into a $N$-scaled base model.

$$
\pi_M^N(y \mid x)=\frac{1}{Z_M^N(x)} \pi_{\text {ref }}^N(y \mid x) \exp \left(r_\pi^M(x, y)\right) \propto \pi_{\text {ref }}^N(y \mid x) \frac{\pi^M(y \mid x)}{\pi_{\text {ref }}^M(y \mid x)}
$$

**Sampling from this distribution emulates finetuning.** When $N > M$ (up-scaling), we emulate the result of finetuning a large model; when $N < M$ (down-scaling), we emulate the result of finetuning a small model.

In this work, we mainly consider $N > M$ (up-scaling), which is a more practical scenario.

# Experiments

The core question is: *what capabilities change when independently scaling pretraining vs finetuning?*

Setups:

1. Datasets
    1. **Anthropic Helpful-Harmless**: everyday and conversational
    2. **ELI5**: factual questions about scientific or political topics
    3. **HumanEval**: code generation
2. Models
    1. **Llama1** series: (Llama1-base-7B/Llama1-base-65B | Vicuna-7B/Vicuna-33B)
    2. **Llama2** series: (Llama2-base-7B/Llama2-base-70B | Llama2-chat-7B/Llama2-chat-70B)
    3. **Falcon** series: (Falcon-base-7B/Falcon-base-180B, | Falcon-chat-7B/Falcon-chat-180B)
3. Evaluation
    1. Aspects: helpfulness, factuality, and harmlessness
    2. Measurement: GPT4 evaluation

## Observation 1: pretraining vs finetuning ⇒ factuality vs helpfulness

For independently scaling pretraining and finetuning, four models are compared:

|  | small pretraining | large pretraining |
| --- | --- | --- |
| small finetuning | lower bound | EFT up-scaled |
| large finetuning | EFT down-scaled | upper bound |

![Normalized improvements in factuality and helpfulness from emulated fine-tuning. These normalized improvements can be seen as **performance gap recovered (PGR)** according to the [weak-to-strong paper](https://arxiv.org/abs/2312.09390): PGR = (EFT scaled - lower bound) / (upper bound - lower bound).](Untitled_1.png)

Normalized improvements in factuality and helpfulness from emulated fine-tuning. These normalized improvements can be seen as **performance gap recovered (PGR)** according to the [weak-to-strong paper](https://arxiv.org/abs/2312.09390): PGR = (EFT scaled - lower bound) / (upper bound - lower bound).

We can observe that EFT down-scaling (top) almost matches the upper bound in helpfulness, whereas EFT up-scaling (bottom) matches the upper bound in factuality.

## Observation 2: EFT enables dynamic test-time reward interpolation

In addition to scaling, EFT provides a test-time method for controllable generation. Given the interpretation that any finetuned models are reward models, we can interpolate two models finetuned for different objectives to get a helpful-harmful frontier, without retraining.

$$
r_\lambda^M(x, y)=\lambda r_{\text {help }}^M(x, y)+(1-\lambda) \pi_{\text {safe }}^M
$$

![GPT-4-evaluated helpfulness and harmfulness on Anthropic-HH prompts.](Untitled_2.png)

GPT-4-evaluated helpfulness and harmfulness on Anthropic-HH prompts.

## Observation 3: speculative decoding speeds up EFT up-scaling

Recall that EFT up-scaling requires three models: 1) large pretrained, 2) small pretrained, and 3) small finetuned. This small-large combination naturally leads to the idea of [speculative decoding](https://arxiv.org/abs/2211.17192).

1. the small finetuned model proposes a block of tokens
2. the small and large pretrained models calculate the EFT conditionals (i.e., implicit rewards)
3. agreement check

![Identifying tokens where the up-scaled small policy has high TV distance with the small policy
alone.](Untitled_3.png)

Identifying tokens where the up-scaled small policy has high TV distance with the small policy
alone.

We observe 2.5x speed-ups for EFT-upscaling:

![Untitled](Untitled_4.png)

## Observation 4: up-scaling can be further amplified

Note that EFT up-scaling can be rewritten as: 

$$
\log \tilde{\pi}\left(y_t \mid x, y_{<t}\right)=\log \pi^{\mathrm{sm}}\left(y_t \mid x, y_{<t}\right)+\underbrace{\left(\log \pi_{\text {ref }}^{\lg }\left(y_t \mid x, y_{<t}\right)-\log \pi_{\text {ref }}^{\mathrm{sm}}\left(y_t \mid x, y_{<t}\right)\right)}_{\text {Up-scaling delta }}+Z
$$

This up-scaling delta biases generations that are preferred by the large model. Further amplifying this delta with a coefficient $\beta > 1$ improves code generation performance and increases factuality.

![Left: up-scaled Llama-2 on HumanEval; right: up-scaled Llama-2 on ELI5. ](Untitled_5.png)

Left: up-scaled Llama-2 on HumanEval; right: up-scaled Llama-2 on ELI5. 

## Observation 5: top-$p$ filtering stabilizes EFT up-scaling

Sampling from up-scaled logits can be noisy (i.e., w/ high variance). To mitigate the potential issues, top-$p$ sampling can be applied on top of EFT up-scaling.

![Top-$p$ mildly improves EFT up-scaling.](Untitled_6.png)

Top-$p$ mildly improves EFT up-scaling.

## More results (from [Liu et al., 2024](https://arxiv.org/abs/2401.08565))

While two papers present almost the same methodology, there are some complementary findings from that paper.

![Untitled](Untitled_7.png)

![Untitled](Untitled_8.png)

1. **A broader scope of benchmarks**: in addition to instruction-tuning, domain adaptation (for code generation) and task-specific finetuning (for QA and math tasks) are also considered.
2. **Some intriguing analysis**: which kinds of tokens are mostly influenced? They show that reasoning (in GSM8K) and style (in TruthfulQA) tokens are mostly influenced by transplanting finetuning to a base model.

# Doing it the reverse direction (from [Zhao et al., 2024](https://arxiv.org/abs/2401.17256))

![Untitled](Untitled_9.png)

# Some random thoughts about weak-to-strong generalization

![Weak-to-strong generalization](Untitled_10.png)

Weak-to-strong generalization

We observe > 80% PGRs in this paper, but in the [weak-to-strong paper](https://arxiv.org/abs/2312.09390) the PGRs are relatively low for tasks like reward modeling. Does it mean that EFT can solve the weak-to-strong problem?

1. **Task**: instruction finetuning is a harder task than the tasks considered in the weak-to-strong paper. For instruction finetuning 7B-chat is much worse than 70B-base. But for binary classification, weak models can perform quite well.
2. A**ssumption**: EFT requires 1) same tokenizer (share the same vocabulary) and 2) access to pre/post-finetuning weak models. The general weak-to-strong setting does not require these.