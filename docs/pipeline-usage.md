# 教材知识流程使用说明

命令从仓库根目录执行，使用 Python 3.10+。知识检索只需标准库；PDF 提取额外需要 pypdf 和 Poppler 的 pdftoppm。需要安装 Python 依赖时运行 `python -m pip install -r requirements.txt`；自动测试依赖见 requirements-dev.txt。Codex 桌面环境可通过工作区依赖工具获取 bundled Python 和 Poppler 路径。脚本也支持 `--renderer` 明确指定 pdftoppm。

扫描 OCR 第一版使用 Windows PowerShell 5.1 与已安装的简体中文 OCR，不调用收费服务。缺少 OCR 时可使用 `--skip-ocr` 保存页面供核对，扫描页保持 `needs_review`；非 Windows 环境仍可提取文本 PDF，或保留扫描页面供手动处理。

## 提取

```powershell
python scripts/pdf_pages.py prepare --pdf "sources/道德与法治七年级上册.pdf" --out "sources/work/七年级上册" --pages 17-23
```

默认以 180 dpi 渲染。manifest 中所有 PDF 页序从 1 开始；教材页码初始为空，在逐页核对时填写。工作目录保存在 `sources/` 中，不共享教材扫描件或完整转录。

同一工作目录的 prepare/review 使用互斥锁，忙碌时会拒绝第二个写入操作。异常退出留下 `.pipeline.lock` 时，先确认对应进程已结束，再移除该锁后重试；不同目录可独立处理。

## 核对

对照页面图修订文字，按阅读顺序保存为候选文件；正文、活动和案例分别标明。为一个页面记录核对结果：

```powershell
python scripts/pdf_pages.py review --manifest "sources/work/七年级上册/manifest.json" --page 18 --text "sources/work/七年级上册/page-018.candidate.txt" --textbook-page 10 --reviewer Codex --notes "逐页对照图像核对正文、栏目和页脚。"
```

疑难尚未解决时追加 `--needs-review`。没有教材印刷页码时省略 `--textbook-page`。核对文本当前版本和历史修订均保留。修改核对文本后重新运行 review；来源 PDF 变化时改用独立工作目录。

## 知识点输入

Codex 阅读核对文本后组织卡片 JSON，存放在本地工作目录。下面仅为格式示例，内容和定位文字必须替换为实际教材支持的表达：

```json
{
  "book": "七年级上册",
  "title": "第二课 正确认识自我",
  "unit": "第一单元 少年有梦",
  "filename": "02_第二课_正确认识自我.md",
  "summary": "本课主旨的教材支持表达。",
  "points": [
    {
      "id": "7A-L02-K01",
      "title": "知识点名称",
      "section": "认识自己",
      "kind": "做法",
      "content": "适合初中生书写的结构化整理。",
      "clues": ["对应的材料题眼"],
      "question_patterns": ["怎么做"],
      "sources": [{"pdf_page": 18, "locator": "核对文字中的实际短语"}]
    }
  ]
}
```

`content` 可包含 Markdown 分点。每个来源的 `locator` 应是核对文本中连续、可辨认的短语，用于定位实际依据；跨页知识点列出所有相关来源。编号以课次为基础，已存在知识点修订时保留编号。

## 生成与校验

```powershell
python scripts/knowledge.py compile --cards "sources/work/七年级上册/lesson-02.cards.json" --manifest "sources/work/七年级上册/manifest.json" --knowledge knowledge
python scripts/knowledge.py build --knowledge knowledge --manifest "sources/work/七年级上册/manifest.json"
```

compile 对照本地资料检查核对状态、来源与文字指纹，生成逐课 Markdown。公开 `sources.json` 只包含书目信息、指纹、页码与核对记录；题眼索引由有效知识点生成。脚本的来源校验不替代 Codex 对知识表达的语义核对。

维护者使用 `build --manifest` 验证本地原始依据；使用者没有 PDF 时可运行 `build --knowledge knowledge` 校验已发布记录。公开记录表示过去已核对，不表示本次重新看过原教材。

同一教材可以分批在独立目录处理，生成时合并该来源的公开页记录。带 manifest 的校验检查其中实际包含的页面资料，其余页面沿用已发布核对记录；全册验收时应使用包含全册相关页的合并 manifest。

## 检索与答题

```powershell
python scripts/knowledge.py search --knowledge knowledge --query "小明觉得自己什么都不如别人，因此自卑，应该怎样认识自己？"
```

search 每次读取当前 Markdown 和来源登记，返回候选知识点；不依赖可能过时的缓存。候选相关性仍须结合设问检查。索引或来源异常时先修复，不把错误状态作为教材依据。

`daofa-qa` 根据候选正文完成题眼映射、材料分析和参考答案。缺少适用依据时明确提示“当前知识库依据不足”。考试模式只给精炼采分点，讲题模式解释映射并说明来源。

## 开发验证

```powershell
python -m unittest discover -s tests -v
```

自动测试需 reportlab 生成独立测试 PDF。教材内容验收使用真实页面和材料题；自动检查覆盖页码、核对状态、重跑保留、来源校验及新副本检索，不代替内容核对。
