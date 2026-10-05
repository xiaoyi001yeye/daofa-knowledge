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
