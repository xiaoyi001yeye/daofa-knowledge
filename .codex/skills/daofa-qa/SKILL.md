---
name: daofa-qa
description: Answer junior-middle-school Chinese Morality and Rule of Law (道德与法治) questions using this repository's Markdown knowledge base. Use when Codex is asked to solve, explain, review, grade, or analyze 道法 questions, especially material-analysis, short-answer,辨析, or exam-style questions, and when answers should be grounded in the local knowledge/ directory rather than model memory.
---

# Daofa QA

Use the repository knowledge base as the primary authority.

## Workflow

1. Read the user's question carefully.
2. Identify likely grade, unit, lesson, and concept. Check the knowledge-base index for current coverage.
3. Search `knowledge/` using `python scripts/knowledge.py search --knowledge knowledge --query "题目"`, or use `rg` to locate relevant entries. The generated 题眼索引 helps find candidates; matching is not proof of applicability.
   For questions spanning topics, search each clue and question type separately when the initial candidates omit a needed topic. Read the corresponding lesson before selecting scoring points.
4. Read the complete knowledge point and its `daofa` metadata. Use only points marked `verified` whose source references match a `reviewed` page in `knowledge/sources.json`. Drafts, placeholders and OCR raw text are not textbook evidence.
5. Extract the question's key clues or “题眼”.
6. Map each clue to one or more supported knowledge points.
7. Map each scoring point to its knowledge-point ID, then write the answer in concise exam-ready Chinese. In default and teaching modes, give the lesson, textbook page and PDF page for the supporting sources.
8. If evidence is insufficient, say “当前知识库依据不足” and identify the missing support. Any general analysis must be clearly separated from textbook-supported scoring points.

## Grounding rules

- Prefer repository knowledge over general memory.
- Do not invent textbook wording.
- Do not add unsupported “standard answers”.
- If several lessons are relevant, list them separately.
- Preserve the knowledge base's terminology.
- Distinguish source-grounded content from optional inference.
- Public source records certify a previous review. Users without the PDF can use verified published knowledge; do not claim to have rechecked the original in the current session.
- If the repository's source or index validation fails, state the problem and repair it when authorized; do not treat the failure as successful verification.
- “标准答案” means a textbook-supported reference answer unless the user supplied an official answer or rubric.

## Default answer format

### 教材知识定位
List the most relevant lesson/section and textbook page; include the PDF page when helpful for locating the original.

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
