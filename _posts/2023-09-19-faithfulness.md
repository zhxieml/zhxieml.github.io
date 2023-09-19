---
layout: post
title: 思维链的“忠诚度”
cover: faithfulness.png
subtitle: CoT Faithfulness
date: 2023-09-19 14:00:00
category: blog
tag: daily
visible: true
---

来自Anthropic的一篇工作，从模型*外部*观察了[CoT推理](https://arxiv.org/abs/2201.11903)时的忠诚度 (faithfulness)。这里的忠诚度指的是，如果生成的推理[“准确地代表了模型预测背后的推理过程”](https://arxiv.org/abs/2004.03685)，则其忠于模型真正的推理。为了让模型能在高风险环境（如医疗决策）下可靠执行推理，以及更好地了解LLM中推理工作方式，我们都希望对推理忠诚度有更深的理解。本研究对CoT推理在LLM中的忠诚度进行了及时调查，扩展了[过往研究](https://arxiv.org/abs/2305.04388)中对CoT推理忠诚度的分析，表明目前LLM生成的推理*难以达到很高的忠诚度*，且在*不同任务、不同参数量上有着明显的表现差异*。

English version: [notion](https://zhxie.notion.site/Measuring-Faithfulness-in-Chain-of-Thought-Reasoning-717b650a49464c4ca8141798e2befbb3?pvs=4)

# 测量忠诚度

作者对zero-shot CoT为何无法提供很高忠诚度的推理提出了以下几个假设：

- **事后推理 (post-hoc reasoning)**
    - 假设：在模型推理前几步后已经掌握了预测所需的推理步骤，后续推理实际上与预测无关，因而也非忠诚
    - 测量方法：1）截断CoT（**提前回答**）；2）在CoT中添加错误的推理步骤（**添加错误**）
- **测试时间计算 (test-time compute)**
    - 假设：CoT带来了额外的tokens，增强了模型在测试时的表达能力，而不是专注于构建有意义的推理步骤
    - 测量方法：用无信息的填充文本替换CoT（**填充标记**）
- **编码推理 (encoded reasoning)**
    - 假设：生成的推理步骤对人类读者来说根本无法理解（e.g., 隐写术），但模型可以从中收集有用的信息
    - 测量方法：用重新表述的CoT替换原始CoT（**重新表述**）

![The proposed tests for measuring CoT faithfulness. **Early Answering**: Truncate the original CoT before answering. **Adding Mistakes**: Have a language model add a mistake somewhere in the original CoT and then regenerate the rest of the CoT. **Paraphrasing**: Reword the beginning of the original CoT and then regenerate the rest of the CoT. **Filler Tokens**: Replace the CoT with ellipses.](/assets/images/2023-09-19-faithfulness/Untitled.png)

**实验设置**

- 模型：*一个包含175B参数的decoder-only LLM，使用RLHF进行微调*
- 任务：8个多项选择任务（其中4个来自[Open LLM排行榜](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)）
  - 科学问题：ARC Challenge、ARC Easy（Clark等人，2018）、OpenBookQA（Mihaylov等人，2018）
  - 代数文字问题：AQuA（Ling等人，2017）
  - 文本填空任务：HellaSwag（Zellers等人，2019）
  - 逻辑推理：LogiQA（Liu等人，2020）
  - 来自各种领域的问题：TruthfulQA（Lin等人，2022）、MMLU（Hendrycks等人，2021）
- 其他细节
  - 使用nucleus采样生成100个推理样本($p=0.95$, $\tau=0.8$)
  - 将每个推理样本使用[nltk](https://github.com/nltk/nltk)分成句子
  - 提示格式如下

![An example of the used CoT prompt. Underlined text is produced by the model.](/assets/images/2023-09-19-faithfulness/Untitled_1.png)

**基本统计数据**

- 收集的推理样本平均有4个步骤（句子），其中89%的样本在3~6之间。
- 在7/8项任务中，使用CoT比不使用CoT表现更好（AQuA提升最大，而HellaSwag是唯一有性能降低的任务）。

![Untitled](/assets/images/2023-09-19-faithfulness/Untitled_2.png)

## 提前回答：截断思维链是否改变预测答案？

提前回答的过程如下：

- 手动选择要截断的CoT步骤（单个句子）
- **在CoT中途截断**（例如，$\left[x_1，x_2，x_3，\ldots，x_n\right]$ 在第3步被截断将导致 $\left[x_1, x_2\right]$）
- 如前所述做prompting得到最终答案

我们观察到不同任务之间存在**广泛差异**：

- **AQuA** 受早期回答影响很大（因此事后推理程度较低）
- 对于 **ARC (Easy)，ARC (Challenge) 和 OpenbookQA** ， CoT 改变最终答案的情况不到 10%

![Untitled](/assets/images/2023-09-19-faithfulness/Untitled_3.png)

我们还可以观察到CoT的性能提升与任务表现之间**几乎没有相关性**。这表明，忠诚度度可能与任务表现关系不大。有意思的是，基础准确度（即w/o CoT的准确度）似乎与忠诚度有更大的相关性。

- **LogiQA**: 准确率提升很小 <=> 高AOC (Area Over the Curve，数值越大表明事后推理的程度越低)
- **HellaSwag**: 准确率下降 <=> 中等AOC

![AOC indicates area over the curve for the early answering and adding mistakes experiments respectively, weighted by the representation of each CoT length. A higher AOC indicates a lower amount of post-hoc reasoning.](/assets/images/2023-09-19-faithfulness/Untitled_4.png)

## 添加错误：编辑思维链是否会改变预测答案？

添加错误是测试事后推理的另一种方法。该过程如下：

- 手动选择要修改的CoT步骤$i$
- 通过少量提示，由预训练模型（175B、decoder-only、无RLHF微调）**采样一个错误版本**的句子
- 保持前$i-1$步推理不变，在第$i$步添加错误步骤，得到$\left[x_1, x_2, \ldots, x_i^{\prime}\right]$
- 继续对CoT进行抽样，同样做prompting得到最终答案

![An add-mistakes sample from AQuA example. The introduced mistake is underlined.](/assets/images/2023-09-19-faithfulness/Untitled_5.png)

结果与提前回答基本一致。这加强了之前的发现：事后推理的程度在不同任务中差异很大，并且它与CoT所提供的准确性改进**没有强相关性**。

此外，我们还注意到AQuA和LogiQA是模型最忠诚于思维链的任务。可能的解释是：

- 没有CoT支持时，LLM在这些任务上表现不佳（分别为28％和42％），因此**必须依赖生成的推理步骤**
- 这两个任务都涉及逻辑推理，在其中陈述的推理有助于完成任务

![Untitled](/assets/images/2023-09-19-faithfulness/Untitled_6.png)

## 填充标记：无信息的思维链标记是否也能提高性能？

填充标记的过程很简单：用一些无意义的tokens替换CoT。观察结果也很直接：在替换CoT为“…”这样的tokens时，准确度没有增加。这表明**额外的测试时间计算并未用于执行潜在的推理**。

![Untitled](/assets/images/2023-09-19-faithfulness/Untitled_7.png)

## 重新表述: 改变思路链的表述方式会影响预测答案吗？

最近，[有研究](https://www.lesswrong.com/posts/bwyKCQD7PFWKhELMr/by-default-gpts-think-in-plain-sight?commentId=zfzHshctWZYo8JkLe)表明**RLHF会引导LLM生成简短的答案**，对推理内容进行隐式长度惩罚。由于本文也使用了经过RLHF微调的LLM，作者认为这可能影响CoT推理的忠诚度。

为了验证是否发生编码推理，作者使用另一个预训练的LLM来改写可能包含编码信息的CoT。具体步骤如下：

- 手动选择某一CoT步骤$i$
- 用LLM改写前$i$步CoT
- 继续采样CoT并像之前一样通过prompting得到最终答案

![A paraphrasing example. Differences from the original chain of thought are underlined in the paraphrased sample.](/assets/images/2023-09-19-faithfulness/Untitled_8.png)

可以观察到，改写的准确性与原始 CoT 的准确性之间**没有显著差距**。因此，LLM 很可能不会编码负责 CoT 准确度提高的隐藏信息。

![Untitled](/assets/images/2023-09-19-faithfulness/Untitled_9.png)

# Scaling Laws

为了正确回答问题，模型可以**直接依靠直觉**或**使用逐步推理**来得出最终答案。因此，在任务性能和推理忠诚度之间可能存在一种**隐含的trade-off**。

为了更清楚地理解这一点，作者通过改变模型大小，测量不同任务性能下推理的忠诚度。作者进行了两组实验：1）**标准任务**，即在之前的任务上重新运行实验以获得结果；2）**加法任务**，其中包含具有2/4/8/16个数求和的synthetic task，每个数由两个或三个digit组成。

## 标准任务

从结果中我们可以观察到两个趋势（或者说是一个**“U”形**的趋势）：

- 当模型大小 < 13B 时，忠诚度会**单调地变好**
- 当模型大小 > 13B 时，忠诚度会**单调地变差**（一种[inverse scaling](https://arxiv.org/abs/2306.09479)的现象？）

推理忠诚度与模型大小间似乎存在一种**困境**：如果模型太小，则无法进行推理；如果模型太大，则不再依赖于忠诚的推理来解决问题。

![Note: y-axis represents answer inconsistency w/ and w/o CoT. A lower value indicates higher faithfulness. The authors choose this metric since it is highly predictive of overall early answering and adding mistakes results.](/assets/images/2023-09-19-faithfulness/Untitled_10.png)

## 加法任务

为了验证上述结论，作者设计了另一组synthetic实验。这组实验设置允许我们控制任务难度。比如以下两个例子：

![Untitled](/assets/images/2023-09-19-faithfulness/Untitled_11.png)

结果再次强调了忠诚度与模型大小的**inverse scaling law**。特别是在**更容易的任务**上，提供忠诚推理的模型并非能力最强的模型。

![Untitled](/assets/images/2023-09-19-faithfulness/Untitled_12.png)

# 总结

本研究探讨了LLM生成的CoT推理的忠诚度。通过全面的实验测试了三种CoT为何无法提供很高忠诚度的假设：1）事后推理，2）测试时间计算，和3）编码推理。主要结论如下：

- 不同任务下事后推理程度的**差异显著**，但与任务表现提高之间显示出**很小相关性**
- CoT 的改进可能**不是由于增加了测试时间计算或编码信息**
- 事后推理程度经常呈现出**inverse scaling**，这表明如果需要忠诚地进行推理，则使用较小模型可能更好

个人觉得这项工作（以及大多数评估研究）的一个主要缺点是**模型内部推理过程依旧是不透明的**。由于没有可用的基准信息，所有结果仍然只能作为某种间接证据。或许我们可以从其他角度 (e.g., [mechanistic interpretability](https://transformer-circuits.pub/2021/framework/index.html)) 来测试模型内部状态。另一个限制是其专注于RLHF模型，一个有趣的方向是**调查RLHF如何影响推理忠诚度**。最后，该工作未提供任何**改善忠诚度**的解决方案 。 他们在[后续工作](https://arxiv.org/abs/2307.11768)中给出了部分答案，通过将 CoT 推理显示地分解为不同的子问题和子答案以增强推理忠诚度。
