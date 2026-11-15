# Evan 模板说明与中文编译规范

本技能随附的 `assets/evan.sty` 同步自 Evan Chen 2025 版 `evan.sty`（已补全中文 XeLaTeX/LuaLaTeX 适配，保留 Boost Software License 1.0 原声明），基于 `amsthm`、`thmtools` 与 `mdframed`（`TikZ` 后端）。

---

## 1. 工作区模式 vs 独立模式

### A. 在工作区（如 `latex` 仓库）内部撰写讲义
工作区根目录 `.latexmkrc` 已将 `templates//` 加入 `TEXINPUTS`，**禁止**复制 `evan.sty` 到讲义目录，也**禁止**使用 `../templates/...` 相对路径。直接使用包路径名加载：

```tex
\documentclass[11pt,a4paper]{ctexart}
\usepackage[chinese,sexy]{evan-zh/evan}
```

编译命令：
```bash
sh scripts/build-xelatex.sh path/to/main.tex
```

### B. 在独立目录中交付可移植源码
仅当不在统一 LaTeX 仓库内工作时，才把 `assets/evan.sty`（及声明文件 `assets/LICENSE.evan.txt`）复制到主 `.tex` 同级目录，然后加载：

```tex
\documentclass[11pt,a4paper,fontset=fandol]{ctexart}
\usepackage[chinese,sexy,noasy,noauthor,nofancy]{evan}
```

可用模板起点：
- `assets/textbook-template.tex`：配合 `evan.sty` 使用（适合多定理框讲义与章节）。
- `assets/ctex-mini-paper-template.tex`：纯 `ctexart + amsthm` 轻量模板（适合微专题短讲义、文章式讲稿）。

---

## 2. 2025 版 `evan.sty` 关键特性

- **定理环境**：自动提供 `theorem`、`lemma`、`proposition`、`corollary`、`assume`、`algorithm`、`claim`、`example`、`remark`、`answer`、`conjecture`、`definition`、`exercise`、`fact`、`problem`、`ques` 及带 `*` 无编号版本；开启 `sexy` 时按节编号并启用彩色 `mdframed` 盒子（蓝框定理、绿框引理/命题式 `claim`、红框例题、左侧黑线注记）与彩色章节标题。
- **中文支持 (`chinese` / `evanchinese`)**：
  - 搭配 `ctexart` / `ctexbook` 时，检测到 `ctex` 已激活（`\@ifundefined{CJKfamilydefault}`）后自动跳过重复 `xeCJK` 加载，无冲突。
  - 若使用标准 `article` + XeLaTeX，加 `[chinese]` 会自动配置 `xeCJK`（默认 `Songti SC` / `Heiti SC` / `STFangsong`；Linux/CI 需配置 `FONT_MAP` 或改用 `ctexart[fontset=fandol]`）。
- **常用数学宏**：已内置 `\abs`、`\norm`、`\dang`、`\ray`、`\seg`、`\arc`、`\cycsum`、`\symsum`、`\vocab`、`\half`、`\CC/\RR/\ZZ/\QQ/\NN/\FF` 等；新增自定义命令前先查是否冲突，需要时用 `\renewcommand`。
- **禁用闲置重包**：不使用 Asymptote 内联编译时加 `noasy`；需要自定义页面与页眉时加 `nofancy,noauthor`。

---

## 3. 编译与版面检查

- 始终用 `latexmk -xelatex` 或两次 `xelatex` 编译，确保交叉引用稳定。
- 若使用 `Fandol` 字体，注意控制台 `fontspec` 关于缺字集的提示并非全都导致实际缺字，应检查 `.log` 中的 `Missing character` 实际记录与 `There were undefined references`。
- 对照渲染 PDF 页面（可用 `pdftoppm -png -r 150` 转为图像查验），确认公式断行、定理框分页、页边距及图表对齐正常后再交付。
