# Obsidian Paper Note Template

Read this when writing or substantially updating a Zotero-derived paper note.

## Preferred Style

Match the user's exemplar note style:

- Long-form Chinese reading note, not a generic abstract.
- Key figures appear near the top, each with an embed and `读图要点`.
- Main body is narrative deep reading with clear domain headings.
- `==highlight==` only marks core mechanisms, key numbers, caveats, and personal takeaways.
- Tables, Mermaid, review cards, and `待追问` are optional, not default filler.
- End with `阅读心得`, `适合引用的观点`, `可延伸方向`, and `关联主题`.

## Recommended Structure

Use this structure unless the existing note has a strong local convention:

```markdown
---
title: "..."
aliases:
  - "..."
tags:
  - 论文
  - ...
status: 已读
read_date: YYYY-MM-DD
year: YYYY
journal: "..."
doi: "..."
zotero_item_key: "..."
zotero_pdf_key: "..."
---

# Paper Title

> [!summary] 一句话总结
> 用一两句话说清这篇文章的核心贡献、关键机制/方法和最值得记住的结论。

## 文献信息

- 题目：...
- 作者：...
- 期刊/会议：...
- 年份：...
- 卷期页码：...
- DOI：[...]()
- ISSN/ISBN：...
- 语言：...
- Zotero 分类：...
- Zotero 条目：[ITEMKEY](zotero://select/items/1_ITEMKEY)
- Zotero PDF：[PDFKEY](zotero://open-pdf/library/items/PDFKEY)
- Zotero 添加时间：...
- Zotero 修改时间：...

## 关键图

### Fig. 1 简短图名

![[论文/_assets/<category>/<paper-slug>/fig1-meaningful-name.png]]

- 读图要点：==这张图证明/连接/解释了什么。==

## 研究背景

为什么这个问题重要，传统路线卡在哪里，作者选择了什么切入点。

## 方法或机制对应关系

把论文中的概念、模型、材料、实验或算法关系讲清楚。需要时用小列表，但以解释为主。

## 方法/器件/实验体系

按论文类型替换标题，讲清结构、流程、数据、参数和关键实现细节。

## 工作原理或主要结果

用二级/三级标题串起核心结果。每节都要回答：作者做了什么，证据是什么，为什么重要。

## 模型与仿真

只有当论文有模型、仿真、理论推导或算法机制时保留。

## 主要创新点

- ==最重要的创新点。==
- 与已有路线相比的实际差异。

## 与已有方案的对比

当论文提供 baseline、相关工作或系统对比时保留。

## 局限与问题

- ==最关键的限制或适用边界。==
- 实验、工程化、数据、统计、泛化或机制解释上的不足。

## 阅读心得

写自己的理解：这篇文章真正启发了什么，哪些地方漂亮，哪些地方仍像概念验证。

## 适合引用的观点

- 可直接转化为写作论点的观点。
- 注意避免夸大，保留任务边界和条件。

## 可延伸方向

- 后续实验、系统集成、对照实验、应用场景或综述线索。

## 关联主题

- [[主题1]]
- [[主题2]]
```

## Domain-Specific Headings

For non-device papers, replace device/material sections instead of forcing them:

| Paper type | Prefer these sections |
| --- | --- |
| Algorithm/model | `问题定义`, `模型结构`, `训练/推理流程`, `数据集与指标`, `消融实验`, `失败案例` |
| Review/perspective | `综述范围`, `分类框架`, `代表工作`, `争议与空白`, `我的选题启发` |
| Biology/experiment | `实验体系`, `样本与处理`, `测量方法`, `统计分析`, `可重复性与限制` |
| Dataset/benchmark | `数据来源`, `标注流程`, `评价协议`, `基线方法`, `偏差与适用边界` |

Always keep the user's preferred ending sections: `阅读心得`, `适合引用的观点`, `可延伸方向`, and `关联主题`.

## Figure Rules

- Put selected key figures before the long analysis so the note is visually anchored.
- Use descriptive filenames: `fig1-lgmd-device-architecture.png`, not `crop1.png`.
- Store figures under `论文/_assets/<category>/<paper-slug>/` so category folders contain only paper notes.
- Embed with vault-relative wikilinks such as `![[论文/_assets/光/collision-detector/fig1-lgmd-device-architecture.png]]`.
- Add a short `读图要点` under every figure; do not leave figures unexplained.
- Include only figures that support the reading note. Skip decorative or redundant panels.

## Optional Structures

Use these only when they add value:

- `论文速览`: when the user asks for a quick review table or the paper is very broad.
- `关键参数` or `关键证据`: when many numbers/conditions/claims need comparison.
- Mermaid: when a mechanism or taxonomy is clearer as a map.
- `复习卡片`: when the user asks for exam/review support.
- `待追问`: when unresolved questions deserve tracking.

## Quality Bar

- The note is in the real Obsidian vault, not the Codex workspace.
- Zotero item/PDF keys are included and clickable.
- The summary distinguishes this paper from similar papers.
- PDF-derived details are preferred over public abstract material.
- Key figures are cropped cleanly, embedded near the top, and explained with `读图要点`.
- Important claims, numbers, caveats, and takeaways use `==...==` sparingly.
- Limitations are honest and grounded in the paper.
- Temporary extracted text, copied databases, preview renders, and contact sheets are removed.
