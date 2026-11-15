# LD Stack

面向数学教学与科研整理的个人核心 Agent Skills 集合。

[English](README.en.md)

LD Stack（原 `ta-skills` 精简重整版）聚焦**跨项目可复用的通用数学工作流能力**——把具体仓库的目录结构、模板索引、PR 流程留在工作区自身的 `AGENTS.md` 中，只在技能包内保留真正通用且经实战打磨的 4 个核心 Skill。

---

## 核心 Skills（共 4 个）

| Skill | 类型 | 用途 |
| --- | --- | --- |
| [`math-exposition`](skills/math-exposition/) | 原创合并 | 教材级中文数学讲义与微专题写作规范（统筹数学主线、去 AI 腔语言规范、LaTeX 排版与 2025 版 `evan.sty` 适配） |
| [`doc-ocr`](skills/doc-ocr/) | 原创升级 | 多引擎通用文档与手写板书 OCR 路由及分片组装（支持 PaddleOCR-VL、MinerU、Mistral OCR、Gemini，纯 Python 标准库） |
| [`tsqx-gen`](skills/tsqx-gen/) | 原创精简 | 奥数平面几何 TSQX $\to$ Asymptote 声明式绘图与本地编译验证 |
| [`math-olympiad`](skills/math-olympiad/) | 外部上游 | 数学竞赛求解与证明审校（源自 Anthropic 官方插件仓库，Apache-2.0，见 [`UPSTREAM.md`](skills/math-olympiad/UPSTREAM.md)） |

外部内容与模板许可边界详见 [THIRD_PARTY.md](THIRD_PARTY.md)。

---

## 安装与挂载

### 作为工作区本地 Skill（推荐）
在 `latex` 等工作区的 `.agents/skills/` 下以相对路径软链接挂载所需 Skill，例如：

```bash
ln -sfn ../../ld-stack/skills/math-exposition .agents/skills/math-exposition
ln -sfn ../../ld-stack/skills/doc-ocr .agents/skills/doc-ocr
ln -sfn ../../ld-stack/skills/tsqx-gen .agents/skills/tsqx-gen
ln -sfn ../../ld-stack/skills/math-olympiad .agents/skills/math-olympiad
```

### 通过 Plugins / Skills CLI 安装
```bash
npx plugins add YZDame/ld-stack
# 或安装单个 Skill
npx skills add YZDame/ld-stack --skill math-exposition
```

---

## 运行依赖

| 功能 | 依赖 |
| --- | --- |
| `doc-ocr` 多引擎 OCR | 按需配置对应环境变量：`PADDLE_OCR_API_KEY` / `MINERU_TOKEN` + `mineru-open-api` / `MISTRAL_API_KEY` / `GEMINI_API_KEY` |
| `math-exposition` 编译 | 本地 XeLaTeX / `latexmk` |
| `tsqx-gen` 本地编译 | `tsqx` 与 `asy`（仅生成 TSQX 源码时无需安装） |

---

## 仓库结构

```text
ld-stack/
├── .codex-plugin/plugin.json
├── .claude-plugin/plugin.json
├── skills/
│   ├── math-exposition/
│   ├── doc-ocr/
│   ├── tsqx-gen/
│   └── math-olympiad/
├── README.md
├── README.en.md
├── LICENSE
└── THIRD_PARTY.md
```

## 许可证

本仓库原创内容采用 [Apache License 2.0](LICENSE)。第三方 Skill 及 `evan.sty` 模板沿用各自原许可条款，详见 [THIRD_PARTY.md](THIRD_PARTY.md)。
