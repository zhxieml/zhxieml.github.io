---
title: "Measuring Faithfulness in Chain-of-Thought Reasoning"

date: "2023-09-19"

tags: ["CoT", "Faithfulness"]

params:
  math: true

---

Generated reasoning is faithful to the model’s true reasoning, if it can [“accurately represents the reasoning process behind the model’s prediction”](https://arxiv.org/abs/2004.03685). This is particularly important 1) in **high-stakes settings**, such as medical decision-making, and 2) for gaining **a better understanding of how reasoning works in LLMs**. This work provides a timely investigation into the faithfulness of [CoT reasoning](https://arxiv.org/abs/2201.11903) for LLMs, adding to [previous research](https://arxiv.org/abs/2305.04388) that suggests LLM-generated reasoning may not be faithful.

中文版本：[知乎](https://zhuanlan.zhihu.com/p/657113706)

{{< table_of_contents >}}

# Measuring Faithfulness

The authors have several hypotheses of why (**zero-shot**) CoT fails on faithfulness:

- **Post-hoc reasoning**
  - Hypothesis: The model’s reasoning is produced after a certain conclusion has already been guaranteed, rendering only certain parts of the spoken reasoning steps faithful
  - How to measure: 1) truncating the CoT (**Early Answering**); 2) adding mistaken reasoning steps in the CoT (**Adding Mistakes**)
- **Test-time computation**
  - Hypothesis: CoT brings additional tokens that enhance test-time computation, rather than focusing on constructing meaningful reasoning steps
  - How to measure: replacing CoT with uninformative filler text (**Filler Tokens**)
- **Encoded reasoning**
  - Hypothesis: The generated reasoning steps are simply not understandable to human readers (a form of steganography), but the model can collect useful information from it
  - How to measure: replacing CoT with paraphrased CoT (**Paraphrasing**)

![The proposed tests for measuring CoT faithfulness. **Early Answering**: Truncate the original CoT before answering. **Adding Mistakes**: Have a language model add a mistake somewhere in the original CoT and then regenerate the rest of the CoT. **Paraphrasing**: Reword the beginning of the original CoT and then regenerate the rest of the CoT. **Filler Tokens**: Replace the CoT with ellipses.](Untitled.png)

The proposed tests for measuring CoT faithfulness. **Early Answering**: Truncate the original CoT before answering. **Adding Mistakes**: Have a language model add a mistake somewhere in the original CoT and then regenerate the rest of the CoT. **Paraphrasing**: Reword the beginning of the original CoT and then regenerate the rest of the CoT. **Filler Tokens**: Replace the CoT with ellipses.

**Experimental setup**

- Model: *A 175B-parameter, decoder-only LLM, finetuned **using RLHF***
- Tasks: 8 multiple-choice tasks (4 of which are from [Open LLM Leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard))
  - Science questions: ARC Challenge, ARC Easy (Clark et al., 2018), OpenBookQA (Mihaylov et al., 2018)
  - Algebra word problems: AQuA (Ling et al., 2017)
  - Text completion task: HellaSwag (Zellers et al., 2019)
  - Logical reasoning: LogiQA (Liu et al., 2020)
  - Questions from a variety of domains: TruthfulQA (Lin et al., 2022), MMLU (Hendrycks et al., 2021)
- Other details
  - 100 reasoning samples using nucleus sampling ($p=0.95$, $\tau=0.8$)
  - Each reasoning sample is split into sentences using https://github.com/nltk/nltk
  - Prompting format as below

![An example of the used CoT prompt. Underlined text is produced by the model.](Untitled_1.png)

An example of the used CoT prompt. Underlined text is produced by the model.

**Basic statistics**

- The collected reasoning samples have **a mean of 4 steps** (sentences), with **89% of samples having between 3~6**
- w/ CoT > w/o CoT on 7/8 tasks (**AQuA** shows the greatest improvement, while **HellaSwag** is the only exception)

![Untitled](Untitled_2.png)

## Early Answering: Does Truncating the Chain of Thought Change the Predicted Answer?

The procedure of Early Answering is as follows:

- Manually selecting which CoT step (a single sentence) to truncate
- **Truncating the CoT midway** (e.g., $\left[x_1, x_2, x_3, \ldots, x_n\right]$ truncated at step 3 will induce $\left[x_1, x_2\right]$)
- Prompting for a final answer as before

We observe **wide variation** between tasks:

- **AQuA** is highly affected by early answering (and therefore the amount of post-hoc reasoning is low)
- The CoT changes the final answer less than 10% of the time for **ARC (Easy), ARC (Challenge), and OpenbookQA**

![Untitled](Untitled_3.png)

We also see **little correlation** with the performance gain from CoT. This reveals that faithfulness may not be very relevant to task performance.

- **LogiQA**: Negligible accuracy boost <=> high AOC
- **HellaSwag**: Accuracy drop <=> average AOC

![AOC indicates area over the curve for the early answering and adding mistakes experiments respectively, weighted by the representation of each CoT length. A higher AOC indicates a lower amount of post-hoc reasoning.](Untitled_4.png)

AOC indicates area over the curve for the early answering and adding mistakes experiments respectively, weighted by the representation of each CoT length. A higher AOC indicates a lower amount of post-hoc reasoning.

## Adding Mistakes: Does Editing the Chain of Thought Change the Predicted Answer?

Injecting mistakes is another approach to testing post-hoc reasoning. The procedure is as follows:

- Manually selecting which CoT step $i$ to modify
- **Sampling a mistaken version** of that sentence by a pretrained model (175B, decoder-only, **w/o RLHF**) via few-shot prompting
- Replacing the reasoning with the original CoT until the point where the error was introduced, followed by the sampled mistaken step $\left[x_1, x_2, \ldots, x_i^{\prime}\right]$
- Continuing to sample the CoT and prompting for a final answer as before

![An add-mistakes sample from AQuA example. The introduced mistake is underlined.](Untitled_5.png)

An add-mistakes sample from AQuA example. The introduced mistake is underlined.

The results largely agree with Early Answering. This reinforces our previous findings: the extent of post-hoc reasoning **varies considerably between tasks**, and it is **not strongly correlated with the accuracy improvement** conferred by CoT.

Besides, we note that **AQuA** and **LogiQA** are with the most faithful reasoning. Possible explanations are:

- LLMs w/o CoT perform poorly on these tasks (28% and 42% respectively), so **they must rely on the generated reasoning steps**
- These tasks both involve **logical reasoning**, in which the stated reasoning helps

![Untitled](Untitled_6.png)

## Filler Tokens: Do Uninformative Chain of Thought Tokens Also Improve Performance?

The procedure of Filler Tokens is simple: replacing the CoT with a number of filler tokens. The observations is also clear: no increase in accuracy when adding “…” tokens to the context. This suggests that **extra test-time compute along is not used to perform helpful but unstated reasoning**.

![Untitled](Untitled_7.png)

## Paraphrasing: Does Rewording the Chain of Thought Change the Predicted Answer?

Recently, there has been [studies](https://www.lesswrong.com/posts/bwyKCQD7PFWKhELMr/by-default-gpts-think-in-plain-sight?commentId=zfzHshctWZYo8JkLe) on how **RLHF steers LLMs to generate short answers**, providing an implicit length penalty to disguise the content of reasoning. Since we are using a RLHF-finetuned LLM, this might also affects faithfulness of CoT reasoning.

To validate whether encoded reasoning happens, the authors use another pretrained LLM to paraphrase the CoT that could contain encoded information. The procedure is as follows:

- Manually selecting a midway CoT step $i$
- Paraphrasing the subsequences of the reasoning sample until step $i$
- Continuing to sample the CoT and prompting for a final answer as before

![A paraphrasing example. Differences from the original chain of thought are underlined in the paraphrased sample.](Untitled_8.png)

A paraphrasing example. Differences from the original chain of thought are underlined in the paraphrased sample.

We observe **no significant gaps** between the paraphrased accuracy and the accuracy of the original CoT. It is therefore unlikely for LLMs to encode hidden information responsible for the accuracy gains of CoT.

![Untitled](Untitled_9.png)

# Scaling Laws

To answer a question correctly, the model can either 1) **rely on immediate intuitions** or 2) **use step-by-step reasoning** to arrive at a final answer. Hence, there is an **implicit trade-off** between task performance and reasoning faithfulness.

In this section, the authors measure the faithfulness by varying model sizes. The authors conduct two sets of experiments: 1) **standard tasks**, in which the results are obtained by re-running experiments on all the above tasks; 2) **addition tasks**, which contains synthetic addition tasks with 2/4/8/16 operands of two or three digits.

## Standard Tasks

We can observe two trends from the results (or a **U-shape trend** overall):

- When the model size < 13B, faithfulness gets **monotonically better**
- When the model size > 13B, faithfulness gets **monotonically worse** (a type of [inverse scaling](https://arxiv.org/abs/2306.09479))

To conclude, there seems to be a **dilemma** for reasoning faithfulness: If the model is too small, it cannot even reason; If the model is too large, it ceases to rely on faithful reasoning to solve problems.

![Note: y-axis represents answer inconsistency w/ and w/o CoT. A lower value indicates higher faithfulness. The authors choose this metric since it is highly predictive of overall early answering and adding mistakes results.](Untitled_10.png)

Note: y-axis represents answer inconsistency w/ and w/o CoT. A lower value indicates higher faithfulness. The authors choose this metric since it is highly predictive of overall early answering and adding mistakes results.

## Addition Tasks

To validate the above conclusion, the authors design another set of synthetic experiments. The synthetic setup allows us to control task difficulty. Two examples are presented above.

![Untitled](Untitled_11.png)

The results again emphasize the **inverse scaling law of faithfulness vs model size**. It may be necessary to choose models that are less capable than the maximally capable model available, **especially for easier tasks**.

![Untitled](Untitled_12.png)

# Conclusion

This study examines the faithfulness of CoT reasoning generated by LLMs. Three hypotheses of the cause of unfaithfulness are tested with comprehensive experiments: 1) post-hoc reasoning, 2) test-time computation, and 3) encoded reasoning. The main takeaways are as follows:

- The **variation** in post-hoc reasoning across tasks is significant, but it shows **little correlation** with the improvement in task performance
- The improvement of CoT may **not** be driven by increased test-time compute or phrasing-encoded information
- The degree of post-hoc reasoning often shows **inverse scaling**, suggesting that smaller models may be better to use if faithful reasoning is important

One major drawback of this work (as well as most evaluation studies) is the **lack of transparency** in the model's internal reasoning process. Since there is no ground-truth information available, all the results remain hypotheses. To address this issue, we can explore more detailed analysis or mechanisms to test the model's internal states.

Another limitation of the evaluation is its focus on RLHF models, which may have different levels of reasoning faithfulness compared to pretrained models. An interesting direction is to **investigate how RLHF affects reasoning faithfulness**.

Finally, the work does not provide any **solutions to improve faithfulness**. This is partially achieved by their [follow-up work](https://arxiv.org/abs/2307.11768), which suggests breaking down CoT reasoning into distinct subproblems and subanswers.