# Zotero Obsidian Paper Note Skill

这是一个可移植的 Codex skill，用来把本地 Zotero 文献库中的论文整理成 Obsidian 中文精读笔记。它面向“每天读一篇论文并沉淀到 Obsidian”的工作流：优先读取 Zotero 元数据、本地 PDF、Zotero child notes、PDF annotations 和全文缓存，然后在 Obsidian 的 `论文` 目录下创建或更新结构化读书笔记。

## 核心能力

- 按标题、DOI、Zotero collection/category 查找论文条目。
- 读取 Zotero 本地 `zotero.sqlite` 中的元数据、作者、期刊、年份、DOI、collection、附件 key、child notes 和 PDF annotations。
- 定位 Zotero 本地 PDF 附件，并尽量利用 Zotero indexed full-text cache 作为辅助，但笔记内容要求基于 PDF 全文理解，而不是只改写摘要。
- 将 Zotero collection 镜像到 Obsidian `论文/<collection>` 目录；无 collection 时写入 `论文/未分类`。
- 根据 `zotero_item_key`、DOI、标题或文件名识别已有 Obsidian 笔记，优先更新而不是重复创建。
- 生成中文深度阅读笔记，包括 verified metadata、Zotero item/PDF links、核心问题、方法、关键结果、局限、关键图读图点、阅读心得、适合引用的观点、可延伸方向和关联主题。
- 裁剪关键图，使用“图注起点作为下边界”的 caption-boundary 规则，避免截掉坐标轴单位、legend、colorbar、panel label 或把正文/图注裁进去。
- 支持跨电脑迁移：本机路径通过环境变量或 `skill-config.local.json` 配置，不需要把个人路径写死进 skill。

## 目录结构

```text
zotero-obsidian-paper-note/
├─ SKILL.md                      # Codex skill 入口说明
├─ README.md                     # 项目说明
├─ LICENSE
├─ skill-config.json             # 可提交的空配置模板
├─ references/
│  ├─ note-template.md           # Obsidian 论文笔记模板
│  └─ tools.md                   # Zotero 查询、路径配置、图像裁剪说明
├─ scripts/
│  ├─ query_zotero_item.py       # 从本地 Zotero SQLite 查询条目/PDF/notes/annotations
│  ├─ render_pdf_crops.py        # 渲染 PDF 预览和裁剪关键图
│  ├─ resolve_config.py          # 解析当前电脑的 Zotero/Obsidian 路径
│  ├─ smoke_test.py              # 新电脑迁移 smoke test
│  └─ test_*.py                  # 回归测试
└─ evals/
   └─ evals.json                 # skill 行为评估样例
```

## 安装

把整个目录复制到 Codex skills 目录：

```powershell
Copy-Item -Recurse . "$env:CODEX_HOME\skills\zotero-obsidian-paper-note"
```

也可以从 release zip 解压，最终路径应类似：

```text
%CODEX_HOME%\skills\zotero-obsidian-paper-note\SKILL.md
```

如果 Codex 没有立即识别新 skill，重启 Codex 或刷新 skills 列表。

## 配置路径

这个 skill 不应该提交个人路径。新电脑上推荐使用环境变量：

```powershell
$env:ZOTERO_OBSIDIAN_VAULT = "D:\path\to\ObsidianVault"
$env:ZOTERO_OBSIDIAN_PAPER_ROOT = "D:\path\to\ObsidianVault\论文"
$env:ZOTERO_DATA_DIR = "D:\path\to\Zotero"
$env:ZOTERO_DB = "D:\path\to\Zotero\zotero.sqlite"
```

也可以在 `SKILL.md` 同级创建本地私有配置文件 `skill-config.local.json`：

```json
{
  "obsidianVaultRoot": "D:/path/to/ObsidianVault",
  "paperNotesRoot": "D:/path/to/ObsidianVault/论文",
  "zoteroDataDir": "D:/path/to/Zotero",
  "zoteroDatabase": "D:/path/to/Zotero/zotero.sqlite"
}
```

`skill-config.local.json` 已被 `.gitignore` 忽略，不应提交到 GitHub。

路径解析优先级：

1. 用户在对话中明确给出的路径。
2. 环境变量：`ZOTERO_OBSIDIAN_VAULT`、`ZOTERO_OBSIDIAN_PAPER_ROOT`、`ZOTERO_DATA_DIR`、`ZOTERO_DB`。
3. 本地私有配置：`skill-config.local.json`。
4. 模板配置：`skill-config.json`。
5. 常见系统默认路径，且必须实际存在并包含数据。

## 新电脑迁移检查

在新电脑安装后，先运行：

```powershell
python scripts\resolve_config.py --show
```

确认 Zotero 数据库、Zotero storage、Obsidian vault 和 `论文` 目录都解析正确。

再用一篇已知存在的 Zotero 论文做 smoke test：

```powershell
python scripts\smoke_test.py --title "known Zotero paper title"
```

运行回归测试：

```powershell
python -m unittest discover -s scripts -p "test_*.py"
```

## Python 依赖

基础查询使用 Python 标准库。裁剪 PDF 图像时需要至少一个 PDF 渲染后端和 Pillow：

```powershell
python -m pip install PyMuPDF Pillow
```

可选安装 `pypdfium2`：

```powershell
python -m pip install pypdfium2
```

`render_pdf_crops.py` 会优先尝试 `pypdfium2`，不可用时回退到 PyMuPDF。

## 典型使用方式

在 Codex 中可以这样触发：

```text
使用 zotero-obsidian-paper-note，把 Zotero 中 DOI 为 10.xxxx/yyyy 的论文整理成 Obsidian 中文精读笔记。
```

```text
阅读 Zotero 的 光 collection 中最近加入且有 PDF 的论文，写入 Obsidian 的 论文\光，关键图裁剪进来。
```

```text
这篇论文已有 Obsidian 摘要笔记，请基于 Zotero PDF 全文补充实验细节、局限和关键图，不要重复建文件。
```

## 笔记输出风格

默认输出中文精读笔记，而不是短摘要。笔记通常包含：

- YAML frontmatter：标题、年份、期刊、DOI、Zotero item key、PDF key、category 等。
- 一句话 summary callout。
- `文献信息`：verified metadata、Zotero item/PDF links。
- `关键图`：重要图像嵌入和逐图读图要点。
- 正文深度阅读：核心问题、方法、器件/模型/系统、实验结果、关键数字、局限。
- `阅读心得`：对论文贡献、边界和可复用思路的判断。
- `适合引用的观点`：可直接转化成论文引用语境的观点。
- `可延伸方向`：后续实验、复现、对比或综述方向。
- `关联主题`：Obsidian wikilinks。


## License

MIT
