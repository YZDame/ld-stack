---
name: math-lecture-notes-style
description: 写或改中文数学讲义、教案、例题解析时使用：管语言风格，让文字像教材和老师讲课，有数学味、没有 AI 腔。数学主线、定理证明结构和 LaTeX 版式由 math-exposition-latex 负责，两者可同时使用。
---
# 数学讲义写作规范（教材式语言，去 AI 腔）

适用：高中或大学数学讲义、学案、例题解析、知识点讲解的生成与改写。输出语言为简体中文。

## 做法
1. **先找样本。** 动笔前要一节风格样本：优先用使用者给的教材原文（如人教 A 版某节）或他以往的讲义；没有时，按下面"规则"和"示例"的语气写。写作时匹配样本的句长、栏目用语（思考、探究、一般地、注）和排版习惯，不照抄样本内容。
2. **按规则写初稿。**
3. **逐条自查**（见文末清单），把不合格处改掉再交付。
4. 若输出 LaTeX，沿用使用者模板里已有的环境和命令，不自造新宏；定义、定理之外不加粗。

## 规则
1. **先问题，后概念。** 新定义之前先给一个具体问题或两三个具体例子，说明这个概念要解决什么。（Axler；Gowers "Examples first"；人教版"思考"）
2. **先理由，后意义。** 先推导或证明，再说用途；不先夸公式重要。（Knuth《Mathematical Writing》）
3. **推导写全。** 关键步骤不跳。省略的步骤写"请读者验证"；"显然""易得"只用于学生确实一眼能看出的地方。（Halmos "Be honest"；Conrad）
4. **从特殊到一般。** 先算具体数值或 n=1,2,3，再写一般情形，用"一般地，……"过渡。（华罗庚"退"；Tao）
5. **条件不能少。** 每条定理或公式至少配一个反例或讨论，说明哪个条件去掉就不成立。（Axler）
6. **逻辑词承重。** 因为、所以、于是、从而、由……得、另一方面、反过来，换着用，不连用同一个。（Conrad）
7. **先说路线。** "下面用数学归纳法证明""先证必要性"。（Conrad；Knuth）
8. **公式嵌在句子里。** 公式前后有文字、有标点；句子不以符号开头；正文不用 ∴ ∵ ∀ ∃，写成文字。（Knuth）
9. **记号少而一致。** 新记号出现时说明含义；用不到的不引入；同一量全文一个记号。（Halmos；Conrad）
10. **例题按"分析—解—回顾"写。** 回顾写能否验算、能否换法、方法还能用在哪里；不写"本题考查了……"。（Pólya《怎样解题》）
11. **用"注""思考""探究"，不用"总结""核心要点"。** 注只写易错、易忽略处，一两句。
12. **版面克制。** 只给定义、定理加框或加粗；不每段加小标题；不用表情符号；不用要点列表代替成段的推理。（Knuth：满篇强调像"一直在喊"）
13. **禁用词与句式。** 核心思想、关键在于、本质上、神奇、巧妙、瞬间、让我们（一起）、是不是很……、非常重要、重中之重、值得注意的是；感叹号；破折号插入说明；三连排比；生活化比喻（除非比喻本身就是数学模型）。（Wikipedia: Signs of AI writing；Google 文档风格指南）
14. **语气平实。** 像老师在黑板前边写边讲：短句、陈述句为主、少形容词；"我们"指师生一起。（Halmos "pretend that it is spoken"）

## 示例（自拟，非教材原文）

AI 腔：
> **等比数列求和公式是重中之重！** 让我们来看看这个神奇的公式……💡 错位相减非常巧妙——显然 q=1 时 S_n=na₁。

教材式：
> 等比数列 {aₙ} 的首项为 a₁，公比为 q，前 n 项和为 S_n=a₁+a₁q+⋯+a₁qⁿ⁻¹。①
> 注意到右边每一项乘 q 就得到它的后一项，把 ① 式两边同乘 q：qS_n=a₁q+a₁q²+⋯+a₁qⁿ。②
> ① 与 ② 的右边只有首尾两项不同。①−② 得 (1−q)S_n=a₁−a₁qⁿ。当 q≠1 时，S_n=a₁(1−qⁿ)/(1−q)。
> 当 q=1 时，上式分母为 0，不能用。这时各项都等于 a₁，所以 S_n=na₁。
> 注 用公式前先看 q 是否等于 1；q 含字母时往往要分类讨论。

一句话层面：
- AI 腔："**关键在于**利用基本不等式——这是核心方法！"
- 教材式："因为 x>0，由基本不等式，x+4/x≥4，当且仅当 x=2 时等号成立。所以最小值为 4。"

## 交付前自查
- [ ] 每个新概念前有问题或例子
- [ ] 没有跳步；"显然"都站得住
- [ ] 每条定理有反例或条件讨论
- [ ] 例题有"回顾"
- [ ] 全文搜不到禁用词、感叹号、表情符号、破折号插入
- [ ] 小标题和加粗只用在定义、定理和栏目名上
- [ ] 记号前后一致

## 参考
- Axler, Linear Algebra Done Right: https://linear.axler.net/
- Hefferon, Linear Algebra: https://hefferon.net/linearalgebra/
- Knuth, Larrabee, Roberts, Mathematical Writing: https://jmlr.csail.mit.edu/reviewing-papers/knuth_mathematical_writing.pdf
- Halmos, How to Write Mathematics（要点）: https://mathcomm.org/paul-halmos-on-writing-mathematics/
- Keith Conrad, Advice on mathematical writing: https://kconrad.math.uconn.edu/blurbs/proofs/writingtips.pdf
- Gowers, Examples first: https://gowers.wordpress.com/2007/10/19/my-favourite-pedagogical-principle-examples-first/
- Wikipedia, Signs of AI writing: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
