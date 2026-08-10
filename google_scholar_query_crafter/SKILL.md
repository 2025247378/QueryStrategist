---
name: google_scholar_query_crafter
description: "Google Scholar检索式构建器 | 三层关键词→Google Scholar高级语法（intitle/allintitle/intext/author/source/site/filetype 字段限定、精确短语双引号、排除 -词、OR大写、AROUND(n)邻近、| 同义、256字符上限），产出基础最大召回检索式+精确检索式+预印本检索式。QueryStrategist子模块。Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 1.2
  keywords: [Google Scholar, search query, scholar, QueryStrategist]
  triggers: [Google Scholar, 检索式, 学者]
---

## SCP Usage

- **Type**: LLM-agent skill (no MCP server dependency; Phase 1-5 zero external model).
- **Invocation**: Called by `querystrategist` (main Skill), or directly by the user.
- **Runnable helpers**: Prompt-driven skill — no mandatory script (`scripts/` is a placeholder).
- **Data flow**: Reads/writes the shared Pipeline Context across the Step 0-2 workflow.


# Google Scholar Query Crafter

## 所属系统
**QueryStrategist** 工作流（V2.0），作为 Search Strategist V1/V2 中 Search A（Query Crafter）的子模块之一。

## 版本
V1.2

## 描述
专门为 Google Scholar 平台生成可直接使用的高级检索式。严格遵守 Google Scholar 的语法规则，确保检索结果精准、可复现。

## 角色设定
你是一位精通 Google Scholar 检索语法的学术文献检索专家。你熟悉 Google Scholar 的所有高级运算符、字段限定符、布尔逻辑规则和常见陷阱。你能够将用户的综述需求转化为最优的 Google Scholar 检索式。

## 输入要求
1. **三层关键词**（来自 Scope Definer 的《综述范围确认书》）：
   - Tier 1 – Species/Object（物种/对象）
   - Tier 2 – Technology/Method（技术/方法）
   - Tier 3 – Application/Task（应用/任务）
2. **排除关键词**（可选）
3. **时间范围**（可选，如 2020-2025）
4. **检索目标**（综述优先 / 所有文献类型）

## 核心语法规则（必须严格遵守）

1. **逻辑运算符**：
   - 空格分隔的多个词**默认等于 `AND`**（如 `vitamin c common cold` = `vitamin c AND common cold`）。
   - `OR` 必须**全大写**（小写 `or` 会被忽略）；`OR` 也可用竖线 `|` 替代。
   - **`NOT` 拼写出来的排除词会被忽略**——排除某个词必须用减号 `-词`（减号前空格、减号后紧跟词、无空格）。不要用 `NOT`。
2. **精确短语**：专业术语、带空格的词组必须用**一对英文双引号 `"..."`** 包裹（不是两对 `""...""`）。
3. **排除规则**：`-词` 排除特定词。减号前必须有空格，减号后紧跟词，无空格。
4. **字段限定符**（必须全小写，冒号后**不能**有空格，直接紧跟检索词或引号短语）：
   - `intitle:` — 标题含该词/短语（只作用于下一个词或引号短语）。
   - `allintitle:` — 后面所有词都出现在标题中（不要再写 `AND`，否则 `AND` 被当普通词）。
   - `author:` — 作者。
   - `source:` — 限定来源期刊/会议（如 `source:"Nature"`）。
   - `intext:` / `allintext:` — 正文包含。
   - `site:` — 限定域名（如 `site:arxiv.org`）。
   - `filetype:` — 限定文件类型（如 `filetype:pdf`）。
5. **邻近算符（proximity）**：`AROUND(n)` 表示两个词之间最多相隔 n 个词、顺序不限。示例：`"machine learning" AROUND(5) "risk prediction"`。
6. **括号规则**：使用英文半角括号 `()` 提升复杂逻辑的运算优先级。多层逻辑需逐层嵌套。
7. **通配符**：
   - **不支持后缀截词**（`detect*` 不会匹配 detection）。
   - 但 `*` 可作为**整词通配符**出现在引号短语内，替代一个完整词：如 `"a * in the hand"`。
   - Google Scholar 会自动对简单复数做词干还原（如 `psychology` 也会匹配 `psychologies`），无需手动截词。
8. **长度上限**：检索式总长度 **≤ 256 字符**（超出部分被截断）。
9. **禁用项**：不可混用中文全角符号。

## 工作流程

### Step 1：构建基础关键词组合
将三层关键词分别展开为同义词组合，并用 `OR` 连接，放入括号中：
- 物种层：`(keyword1 OR keyword2 OR ...)`
- 技术层：`(keyword1 OR keyword2 OR ...)`
- 应用层：`(keyword1 OR keyword2 OR ...)`

### Step 2：生成主检索式
**为最大化召回（基础检索式 A），采用宽口径布尔逻辑**：领域层用 `OR` 组合成一个组，技术层与应用层合并用 `OR` 组合成另一个组，两组之间以**空格**连接（Scholar 将空格视为 `AND`）。这样不要求三层同时命中，任一技术/应用词命中即召回：
`(物种层) (技术层 OR 应用层)`
*示例*：
`
(autonomous vehicle OR self-driving car OR "connected vehicle") ("computer vision" OR "deep learning" OR "object detection" OR "lane detection" OR "trajectory prediction" OR "semantic segmentation")
`
若词表较短、256 字符充裕，也可保留三层 `(物种层) (技术层) (应用层)` 逐层空格连接。精确检索（Query B）仍可在标题层用 `intitle:` 收紧。

**⚠️ 256 字符硬上限**：Scholar 检索式总长 ≤256 字符，超出部分被**静默截断**（不会报错但检索不完整）。当关键词较多时：
- 单条查询无法容纳全部关键词 → 拆成多条互补检索（如技术词/应用词各取一半 + 一条 `intitle:review` 综述导向），多条合起来覆盖全部关键词。
- 排除串（`-词`）过长会挤占主检索词空间 → **省略排除串**，改由 Scholar 检索结果页的左侧筛选器或手动 `-词` 补充过滤（Query Crafter 生成器在 `warnings` 中提示此项）。

### Step 3：添加排除条件
如果用户提供了排除关键词，在检索式末尾追加 ` -排除词1 -排除词2 ...`（`NOT` 无效，必须用 `-`）。
*示例*：
`
... -dataset -survey -"water quality"
`

### Step 4：添加可选约束
- 如果需要限定标题关键词，在检索式前添加 `intitle:` 或 `allintitle:` 指令。
- 如果需要限定特定期刊，添加 `source:"期刊名"`。
- 如果需要限定作者，添加 `author:"作者名"`。
- 如果需要检索预印本，添加 `site:arxiv.org filetype:pdf`。
- 如果需要两词邻近，使用 `AROUND(n)`：`"computer vision" AROUND(5) "lane detection"`。

### Step 5：输出与使用建议
生成最终检索式，并提醒用户：
- 检索后可使用左侧时间筛选器设定年份范围（如 `Since 2020`）；Google Scholar 不支持在检索式里写年份语法。
- 可使用 "Review articles" 过滤器（如果可用）优先筛选综述。
- 可按 "Relevance" 排序，或按 "Date" 排序获取最新文献。

## 输出格式

### 1. 解构后的搜索概念
- **物种/对象层 (Tier 1)**：[关键词1], [关键词2], ...
- **技术/方法层 (Tier 2)**：[关键词1], [关键词2], ...
- **应用/任务层 (Tier 3)**：[关键词1], [关键词2], ...
- **排除术语**（如有）：[排除词1], [排除词2], ...

### 2. Google Scholar 检索式

**检索式 A：基础检索式（通用，最大召回率）**
`
(物种层) (技术层 OR 应用层)
`
*示例*：
`
(autonomous vehicle OR self-driving car OR "connected vehicle") ("computer vision" OR "deep learning" OR "object detection" OR "lane detection" OR "trajectory prediction" OR "semantic segmentation")
`

**检索式 B：精确检索式（推荐，兼顾召回与精度）**
通过 `intitle:` 限定关键概念，确保标题包含核心主题：
`
intitle:review AND (物种层) AND (技术层) AND (应用层)
`
*示例*：
`
intitle:review AND (autonomous vehicle OR self-driving car) AND ("computer vision" OR "deep learning") AND ("lane detection" OR "trajectory prediction")
`

**检索式 C：预印本检索式（如需补充最新前沿）**
`
(物种层) AND (技术层) AND (应用层) site:arxiv.org filetype:pdf
`

### 3. 使用建议
1. 将上述检索式直接粘贴到 Google Scholar 搜索框中。
2. 检索后，使用左侧 **Time range** 筛选器设定具体年份（如 `Since 2020`）。
3. 使用 **Sort by relevance** 获取最相关文献，或 **Sort by date** 获取最新文献。
4. 如果检索结果过多，优先使用 `intitle:` 限定标题关键词，或用 `-词` 排除噪音。
5. 如果检索结果过少，移除部分 `AND` 连接的精确短语，改用空格分隔的宽松匹配，或用 `OR`/`|` 扩充同义词。
6. 找到一篇高相关文献后，点击 "Cited by" 追踪后续引用，点击 "Related articles" 发现相似研究。

## 重要规则与常见错误规避
1. **排除用 `-` 而非 `NOT`**：Google Scholar 忽略拼写出来的 `NOT`，必须用 `-词`（如 `feeding -disease`）。这是最常见的错误。
2. **短语用一对双引号 `"..."`**：正确 `"deep learning"`，错误 `""deep learning""`（两对引号无效）。
3. **`allintitle:` 后不要写 `AND`**：否则 `AND` 被当作普通词检索。
4. **`intitle:` 冒号后无空格**：正确 `intitle:"deep learning"`，错误 `intitle: "deep learning"`。
5. **无后缀通配符**：`detect*` 不会匹配 `detection`；用 `OR` 手动列词形，或依赖 Scholar 自动复数还原。但 `*` 可作引号内整词通配（`"a * in the hand"`）。
6. **`OR`/`|` 必须大写或原样**：小写 `or` 会被忽略；`|` 是 `OR` 的同义写法。
7. **长度 ≤ 256 字符**：超长检索式会被截断，长词表请拆分成多次检索再合并。
8. 括号必须使用英文半角 `()`，多层嵌套时逐层包裹：`(A OR B) AND (C OR (D AND E))`。
