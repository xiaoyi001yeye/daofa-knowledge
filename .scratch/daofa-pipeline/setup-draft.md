# 本地工程流程配置草案

状态：已于 2026-10-05 经用户确认并应用到 AGENTS.md 与 docs/agents/。

已确定：规格和任务使用本地 Markdown，保留默认任务状态。本仓库使用单一领域语境，不需要多语境目录结构。

## 拟追加到 AGENTS.md 的内容

保留现有道法答题规则，在末尾追加以下块：

```markdown
## Agent skills

### Issue tracker

规格和任务保存为 .scratch/ 下的本地 Markdown。见 docs/agents/issue-tracker.md。

### Triage labels

使用默认的五个任务分类状态。见 docs/agents/triage-labels.md。

### Domain docs

本仓库使用单一领域语境：根目录 CONTEXT.md 与 docs/adr/。见 docs/agents/domain.md。
```

## 拟创建 docs/agents/issue-tracker.md

```markdown
# Issue tracker: Local Markdown

本仓库的规格和任务保存为 .scratch/ 下的 Markdown 文件。

## 文件约定

- 每项功能使用一个目录：.scratch/<feature-slug>/。
- 实现规格保存为 spec.md。
- 实现任务每项一个文件，位于 issues/<NN>-<slug>.md；按依赖顺序从 01 编号。
- 任务分类状态记录在任务文件顶部的 Status 行，名称以 triage-labels.md 为准。
- 后续讨论追加到任务文件末尾的 Comments 标题下。

本次三个能力使用 .scratch/daofa-pipeline/。

## 发布规格和任务

技能要求“发布到任务跟踪器”时，创建对应的本地 Markdown 文件。
技能要求“读取相关任务”时，读取指定的完整文件及其追加讨论。

## 依赖与执行

- 每项任务用 Blocked by 行声明阻塞它的任务编号；没有依赖时写 None。
- 只有阻塞任务全部完成，当前任务才能开始。
- 开始执行前将任务状态记录为 claimed；完成后记录为 resolved 并附验证结果。
- 保留任务中的讨论和验证证据，不用一份合并清单替代独立任务文件。

## Wayfinding operations

- 决策地图保存为 .scratch/<effort>/map.md。
- 子任务保存为该目录 issues/ 下的独立编号文件，并包含 Type、Status、Blocked by。
- 领取前检查阻塞任务，领取时保存 claimed 状态。
- 解决后将结论追加到 Answer 标题下，记录 resolved，并在地图中添加结论及文件链接。
```

## 拟创建 docs/agents/domain.md

```markdown
# Domain Docs

## 读取条件

探索本仓库的工程实现前，读取根目录 CONTEXT.md，使用其中的领域术语。
涉及已有设计取舍时，读取 docs/adr/ 下相关的决策记录。
文件不存在时继续工作；只在术语已经明确或确实需要记录决策时创建对应文件。

## 布局

本仓库使用单一领域语境：根目录 CONTEXT.md 与 docs/adr/。
CONTEXT.md 只保存领域术语，不保存实现规格或任务清单。
只有难以逆转、需要解释且涉及实际取舍的决定才记录为 ADR。

## 使用术语与决策

规格、任务和工程讨论使用 CONTEXT.md 定义的术语。
术语缺失或存在冲突时，在领域建模步骤中澄清。
新方案与已有 ADR 冲突时，指出冲突及重新考虑该决定的理由。
```

## 拟创建 docs/agents/triage-labels.md

以下为推荐默认值；如果用户选择自定义，按其选择调整后再应用。

```markdown
# Triage Labels

| 技能中的状态 | 本仓库中的状态 | 含义 |
| --- | --- | --- |
| needs-triage | needs-triage | 需要评估任务 |
| needs-info | needs-info | 等待补充信息 |
| ready-for-agent | ready-for-agent | 规格明确，可由代理执行 |
| ready-for-human | ready-for-human | 需要人工完成 |
| wontfix | wontfix | 决定不处理 |

本地 Markdown 使用这些字符串记录任务分类。
领取和完成时的执行状态由 issue-tracker.md 中的约定记录。
```

## 应用后的下一步

1. 在交接格式草案中明确核对标准和验收方式。
2. 将已确定的范围整理为本地实现规格。
3. 拆分能够独立验收的完整流程任务，标出真实依赖。
4. 先实现第二课 PDF → 核对文本 → 知识点 → 材料题答案，再扩展全书。
