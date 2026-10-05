# daofa-knowledge

一个基于 **Codex Skills + Markdown 知识库** 的初中《道德与法治》学习与答题项目。

目标：

- 用户直接 `git clone` 获取最新知识库与 Skill。
- 在仓库目录中启动 Codex 后，直接粘贴题目或上传题目图片。
- Codex 先检索本仓库 `knowledge/`，再依据教材知识组织答案。
- 输出“知识定位 → 材料分析 → 采分点 → 参考答案”，尽量使用教材术语。
- 当知识库证据不足时明确说明，不用模型常识强行补全。

> 当前第一阶段以七年级上册《道德与法治》为目标。

## 快速开始

```bash
git clone https://github.com/xiaoyi001yeye/daofa-knowledge.git
cd daofa-knowledge
codex
```

然后直接提问，例如：

```text
请使用 daofa-qa skill 回答：

进入初中后，小明觉得自己什么都不如别人，因此越来越自卑。
请结合教材知识分析小明应该怎样正确认识自己。
```

也可以要求不同回答风格：

```text
考试模式：只给适合写在答题卡上的采分点。
```

```text
讲题模式：先告诉我题眼，再说明每个题眼对应哪个教材知识点。
```

## 项目结构

```text
.
├── .codex/
│   └── skills/
│       └── daofa-qa/
│           ├── SKILL.md
│           ├── agents/openai.yaml
│           └── references/
│               ├── answer-rules.md
│               ├── question-types.md
│               └── textbook-structure.md
├── knowledge/
│   └── 七年级上册/
│       ├── 00_知识库索引.md
│       └── 01-13_各课知识.md
├── questions/
│   └── examples.md
├── AGENTS.md
└── README.md
```

## 回答原则

1. 教材知识库优先。
2. 先定位章节，再分析材料。
3. 结论尽量拆成可评分的采分点。
4. 使用初中生可以直接书写的表达。
5. 不把未经知识库支持的内容伪装成“教材原话”。
6. 如果题目跨课，明确列出涉及的多个知识点。

## 更新

```bash
git pull
```

以后知识库、答题规则或 Skill 更新后，使用者只需拉取最新代码即可。

## 说明

本仓库保存的是对教材内容进行结构化整理后的学习知识，不包含教材扫描 PDF。请仅在合法获得教材的前提下学习和使用。

## Roadmap

- [x] Codex 项目级 Skill
- [x] 七年级上册知识库框架
- [ ] 完善全部课次的细粒度知识卡片
- [ ] 增加选择题/材料题/辨析题专用策略
- [ ] 增加错题复盘模式
- [ ] 增加知识点测试题自动生成
- [ ] 增加更多年级与册次

