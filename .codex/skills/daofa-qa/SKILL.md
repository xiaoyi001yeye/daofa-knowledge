---
name: daofa-qa
description: Answer junior-middle-school Chinese Morality and Rule of Law (道德与法治) questions using this repository's Markdown knowledge base. Use when Codex is asked to solve, explain, review, grade, or analyze 道法 questions, especially material-analysis, short-answer,辨析, or exam-style questions, and when answers should be grounded in the local knowledge/ directory rather than model memory.
---

# Daofa QA

Use the repository knowledge base as the primary authority.

## Workflow

1. Read the user's question carefully.
2. Identify likely grade, unit, lesson, and concept.
3. Search `knowledge/` for relevant Markdown files and headings.
4. Read enough surrounding context to understand the complete knowledge point.
5. Extract the question's key clues or “题眼”.
6. Map each clue to one or more supported knowledge points.
7. Write the answer in concise exam-ready Chinese.
8. If evidence is insufficient, say so explicitly.

## Grounding rules

- Prefer repository knowledge over general memory.
- Do not invent textbook wording.
- Do not add unsupported “standard answers”.
- If several lessons are relevant, list them separately.
- Preserve the knowledge base's terminology.
- Distinguish source-grounded content from optional inference.

## Default answer format

### 教材知识定位
List the most relevant lesson/section.

### 题目分析
Explain the key clues in the material.

### 对应知识点
List concise supported knowledge points.

### 参考答案
Write numbered scoring points suitable for an exam answer.

### 答题关键词
Give 3-8 compact keywords.

## Modes

### 考试模式
When the user asks for 考试模式 / 标准答案 / 只要答案:
- output only concise numbered scoring points;
- avoid long explanations;
- keep wording easy to copy into an answer sheet.

### 讲题模式
When the user asks for 讲题 / 解释为什么:
- show “题眼 -> 知识点 -> 采分点” mapping;
- explain why each point is relevant;
- finish with a concise reference answer.

### 复习模式
When the user asks to review a topic:
- summarize the concept;
- list common question patterns;
- include frequent confusions only if supported by the knowledge base.

## References

Read these when needed:

- `references/answer-rules.md`: answer-writing rules
- `references/question-types.md`: question-type handling
- `references/textbook-structure.md`: current textbook map
