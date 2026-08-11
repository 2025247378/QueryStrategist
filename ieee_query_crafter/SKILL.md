---
name: ieee_query_crafter
description: "IEEE Xplore检索式构建器 | 三层关键词→IEEE Xplore【Advanced Search 中的 Command Search】语法（完整字段名 \"Document Title\":/\"Abstract\": 等为可选限定符、布尔 AND/OR/NOT、邻近 NEAR/ONEAR、短语、通配符 * ?、每个 search clause≤25 terms），产出宽泛查全A+高精度查准B+会议定向C+邻近检索D四套 Command Search 检索式。QueryStrategist子模块 Use this skill for IEEE Xplore (Advanced Search › Command Search) query building tasks within the QueryStrategist literature-search workflow. Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 1.8
  keywords: [IEEE Xplore, command search, search query, engineering, QueryStrategist]
  triggers: [IEEE, 检索式, 工程文献, IEEE Xplore, Command Search, command search]
---

## SCP Usage

- **Type**: LLM-agent skill (no MCP server dependency; Phase 1-5 zero external model).
- **Invocation**: Called by `querystrategist` (main Skill), or directly by the user.
- **Runnable helpers**: Prompt-driven skill — no mandatory script (`scripts/` is a placeholder). GB/T 7714 reference export is handled downstream during manuscript writing (Step 3+ deliverable pipeline).
- **Data flow**: Reads/writes the shared Pipeline Context across the Step 0–2 workflow.


# IEEE Query Crafter

## QueryStrategist System
This skill is part of the **QueryStrategist** workflow (Step 2). It is called by **Search Strategist V1** to generate platform-specific advanced search queries for IEEE Xplore. The queries are used by the user for manual retrieval of high-quality literature, primarily in computer science, electrical engineering, and related interdisciplinary fields.

## Version
V1.8

## Change Log
- **V1.8 (2026-08-11)**: 按 IEEE Xplore 当前官方 Search Tips 修正 25-term 口径：限制作用于“未被布尔运算符分隔的连续检索词”组成的 search clause，不再把整条查询的所有 OR 同义词累计后拆分；保留完整 Query A。单词默认不加引号以保留词干扩展，多词固定短语才加引号；补充每查询最多 10 个通配符及通配符前至少 3 个字符的校验；Query D 改为技术/方法层与应用/任务层的真正 NEAR/ONEAR 共现。
- **V1.7 (2026-08-11)**: 与 `query_crafter/scripts/query_generator.py` 实现对齐：Query A 默认 All Metadata；Query B 逐项重复 `"Document Title":`；按 25 个 keyword/quoted-phrase values 自动拆分；条件生成 Query C；补齐 NEAR/ONEAR Query D 与自动化回归测试。
- **V1.6 (2026-08-10)**: 对照 IEEE Xplore 官方 Command Search 帮助页（xplorestaging.ieee.org/Xplorehelp）修正语法口径——**字段名是可选限定符**（官方 Step 1：不写字段名则默认搜全部 metadata，运算符示例 `"wireless sensor network" AND security`、`implantable NEAR/3 cardiac` 均无字段名），不再强制"每个搜索词都带字段名"；保留官方明确禁止的写法（`"Document Title":("a" OR b)` 字段内括号 OR 无效）；Query A/D 模板改为官方风格（无字段名简洁写法 + 可选字段限定说明）；NEAR 用官方简单示例；25 terms 改官方原文口径。修正此前"逐词重复字段名"的过度泛化（V1.5），避免生成与官方风格脱节的查询。
- **V1.5 (2026-08-10)**: 官网比对后修正 Command Search 语法——完整字段名列表、同字段 OR 禁止括号嵌套（需逐词重复字段名）、每子句 ≤25 terms、Command Search 无独立年份字段。**（注意：V1.5 将"同字段 OR 逐词重复字段名"过度泛化为"每个搜索词都必须带字段名"，与官方默认"无字段名=搜 metadata"矛盾，V1.6 已修正。）**

## Description
Transforms a user's research direction into a precise, ready-to-use advanced search query for IEEE Xplore **Command Search** (the free-form query tab under Advanced Search). This skill applies expert-level IEEE Xplore search syntax, including field codes (`"Document Title":`, `"Abstract":`, `"Authors":`, `"Publication Title":`, `"Index Terms":`), Boolean operators (`AND`, `OR`, `NOT`), proximity operators (`NEAR`/`ONEAR` — command search only), phrase searching (`" "`), and wildcards (`*`, `?`). It generates queries optimized for retrieving high-quality engineering, computer-science, and interdisciplinary literature from IEEE conference proceedings, journals, and early-access articles.

## Role
You are an expert research librarian specializing in systematic literature retrieval on the IEEE Xplore platform. You are fluent in IEEE Xplore's Command Search syntax — full field names, Boolean operators, and the proximity operators (NEAR/ONEAR) that set command search apart from the default structured advanced search. You balance sensitivity (recall) and specificity (precision) for technical literature, and you know IEEE Xplore is the primary source for conference proceedings (e.g. CVPR, ICCV, ICRA, IROS), IEEE journals, and early-access articles.

## Input Requirements
The user (or the calling skill, Search Strategist) must provide:
1. **Research Direction**: A description of the research topic, with emphasis on the technology/method dimension (e.g., "deep learning for medical image segmentation").
2. **Keyword Tiers** (from Scope Definer's Review Scope Confirmation Document):
   - Tier 1 – Target Object/Domain: The subject or application domain (e.g., "autonomous vehicle", "medical image", "power transformer", or a species/organism when the field is biological).
   - Tier 2 – Technology/Method: The relevant techniques (e.g., deep learning, object detection, signal denoising, reinforcement learning, semantic segmentation).
   - Tier 3 – Application/Task: The specific problem (e.g., anomaly detection, fault diagnosis, behavior recognition, biomass estimation).
3. **Date Range** (optional): Publication years to include (e.g., 2020-2025). On IEEE Xplore this is applied via the left-side `Publication Year` filter (see Step 2-F).
4. **Search Focus** (optional): Whether to prioritize review articles, conference proceedings, or journal papers.

## Workflow

### Step 1: Deconstruct the Research Question
Based on the input keyword tiers, identify and organize the key concepts. For IEEE Xplore, prioritize the technology/method and application/task tiers, as these align with the platform's strength in engineering and computer science. The species/object tier is used to narrow the application domain.

### Step 2: Construct the Core Query
Using IEEE Xplore's **Command Search** syntax (Advanced Search → Command Search tab), build the query following these rules.

**A. Field Codes (full field-name format — OPTIONAL field limiter)**

⚠️ **在 Command Search 中，字段名是"可选限定符"，不是强制要求。** 官方文档（Command Search Help → Using Command Search）原文：*"IEEE Xplore looks for a keyword in all fields (metadata) unless you limit the search to specific fields."* —— **不带字段名的搜索词默认在所有元数据字段（标题+摘要+关键词+书目信息）中检索**，这是官方默认行为，也是官方运算符示例（`"wireless sensor network" AND security`、`REV OR "renewable energy vehicle"`、`implantable NEAR/3 cardiac`）的标准写法。

- 需要**限定到某个字段**时，字段名用**带引号的完整名称 + 冒号**：`"Document Title":value`、`"Abstract":value`。多词值必须加引号；单值可省略引号（如官方 `"Document Title":rfid`、`"Publication Title":power`）。
- **什么时候用字段名**：
  - `"Document Title":` 最高精确度——用于最关键概念（如 Query B 高精度检索）；
  - `"Abstract":` 扩大覆盖范围同时保持相关度——用于宽泛召回（如 Query A 需要更广覆盖时）；
  - `"Publication Title":` 限定特定期刊/会议（如 `"Publication Title":"CVPR"`）；
  - `"Index Terms":`（作者关键词 + IEEE 词表 + MeSH 组合）用于标准化技术术语。
  - **什么时候不用**：默认无字段名（搜全 metadata）是合法且常见的——官方运算符示例全部无字段名。宽泛查全检索（Query A）**默认无字段名**，与官方风格一致。

> ⚠️ 短代码 `ti` / `ab` / `au` / `pt` 是 Web of Science 语法，**在 IEEE Xplore 上无效**。IEEE Xplore 只认带引号的完整字段名（`"Document Title":`）或**不带字段名**（默认 metadata）。

| Field code (Command Search) | Data Field | Notes |
|:--|:--|:--|
| （无字段名） | All Metadata（默认） | 标题+摘要+关键词+书目数据；官方默认行为 |
| `"Document Title":` | Document Title | 最高精确度；用于最关键概念 |
| `"Abstract":` | Abstract | 扩大覆盖范围同时保持相关度 |
| `"Authors":` | Authors | 已知作者；多格式尝试（`"Authors":"LeCun, Y."` 与 `"Authors":"Yann LeCun"`） |
| `"Author Keywords":` | Author Keywords | 作者提供的关键词 |
| `"IEEE Terms":` | IEEE Terms | IEEE 受控词表 |
| `"Index Terms":` | Index Terms | 组合：Author Keywords + IEEE Terms + MeSH Terms；适合标准化技术术语 |
| `"Publication Title":` | Publication Title | 限定特定期刊/会议 |
| `"Author Affiliation":` | Author Affiliation | 机构隶属 |
| `"Publisher":` | Publisher | 如 `"Publisher":"IEEE"` |
| `"DOI":` | DOI | 精确单篇定位 |
| `"ISBN":` / `"ISSN":` | ISBN / ISSN | 图书/连续出版物标识 |
| `"MeSH Terms":` | MeSH Terms | 医学主题词（生物医学文献） |

For exact-phrase matching, always quote the value: `"Document Title":"deep learning"` (NOT `"Document Title":deep learning` — without quotes a multi-word value is split by AND).

**B. Boolean Operators**
- `AND` connects distinct concepts (both must match).
- `OR` connects synonyms within the same concept.
- `NOT` excludes an area (e.g. `acoustic imaging NOT water`).
- **Operator precedence (without parentheses)**: `NEAR`/`ONEAR` > `NOT` > `AND` > `OR`. Use parentheses to override, e.g. `("UAV" OR "unmanned aerial vehicle") AND ("trajectory tracking" OR "target tracking")`.

**C. Phrase Searching**
- Enclose multi-word terms in double quotes for exact-phrase matching: `"deep learning"`, `"computer vision"`.
- ⚠️ A value without quotes is treated as AND of its words: `"Document Title":web services` finds `web` AND `services`, not the phrase. Always quote phrases.
- Exact quotes also suppress automatic stemming. Keep simple single-word concepts such as `fish`, `freshness`, and `protein` unquoted unless exact whole-word matching is intentional.

**D. Wildcards**
- `*` = multi-character truncation (`detect*` → detect, detects, detection, detector).
- `?` = single-character wildcard.
- Wildcards may appear inside quoted phrases and with proximity operators: `"radioloc*"` or `("neural net*" NEAR/3 "control")`.
- 每条查询最多使用 10 个通配符；使用通配符前至少输入 3 个字符。查询生成器必须在输出前校验这两项。

**E. Proximity Operators (Command Search only — unavailable in default structured advanced search)**
- `NEAR/n`: the two expressions occur within `n` words of each other, in either order.
  Example: `("hybrid electric vehicle" NEAR/10 "plug-in")` — finds the phrase OR the abbreviation `HEV` within 10 words of `plug-in`.
- `ONEAR/n`: ordered proximity — the first expression must appear *before* (to the left of) the second within `n` words.
  Example: `("hybrid electric vehicle" ONEAR/10 "plug-in")`.
- Operators must be **all uppercase**. Complex Boolean may be nested inside a proximity clause: `(computer OR PC) NEAR/3 monitor`.

**F. Date Range**
- The official IEEE Xplore Command Search field list has **no dedicated short year field**. Filter by year using the **left-side `Publication Year` filter** after running the query. Do NOT use a `"Publication Year":"2020"-"2025"` clause — it is not part of the official Command Search field list and may be rejected.

**G. Limits & Constraints**
- **Max 25 search terms per search clause**（官方原文："You can enter a maximum of 25 search terms per search clause"）。IEEE Search Tips 将 search clause 定义为 **consecutive search terms not separated by a Boolean operator**。因此 `A OR B OR C` 的 OR 会分隔 clause，不能把整条查询的所有同义词累计成一个 25-term 总预算。引号短语内部的连续单词按保守口径逐词检查；字段名和布尔/邻近运算符不计入。
- ⚠️ **不要因整条查询含有超过 25 个 OR 同义词而拆分或丢词。** 仅当某个未被布尔运算符分隔的原子 clause 自身超过 25 个连续词时才报错，并要求改写该原子表达式。
- **同字段内禁止括号嵌套 OR**（官方原文）：`"Document Title":("radio frequency identification" OR rfid)` **无效**；正确写法是逐词重复字段名再用外层括号分组：`("Document Title":"radio frequency identification" OR "Document Title":rfid) AND scheduling`。
- **无字段名的裸词/裸短语合法**（官方默认搜全部 metadata，见 A 节）——`("fish" OR "whole fish") AND ("spectral imaging" OR "hyperspectral imaging")` 是**合法且符合官方风格**的写法，不必给每个词加字段名。
- Search is **case-insensitive**.
- IEEE Xplore ignores most punctuation; only `&`, `+`, and `/` are recognized as special characters. Quote a punctuated expression only when exact phrase behavior is intended, and replace punctuation with spaces when constructing an exact phrase as advised by Search Tips.

**H. Official Reference Examples (verbatim from IEEE Xplore Search Tips)**
IEEE Xplore 官方帮助文档给出的标准写法（逐字引用），印证本 skill 的格式规则——**字段名是可选限定符，两种写法都合法**：

**写法一：带字段名限定**（官方 Command Search Example 区）：
1. **单字段精确短语**（多词值必须加引号）：
   `"Document Title":"renewable energy sources"`
2. **同一字段内用 OR 查找任一主题**（每个短语前都带字段名）：
   `"Document Title":"renewable energy sources" OR "Document Title":"sustainable energy systems"`
3. **括号分组 + 跨字段 AND**（先算 OR 组内，再与出版物字段 AND；单值 `power` 可省略引号）：
   `("Document Title":"renewable energy sources" OR "Document Title":"sustainable energy systems") AND "Publication Title":power`
4. **官方明确禁止**：`"Document Title":("radio frequency identification" OR rfid)` 无效；正确为 `"Document Title":"radio frequency identification" OR "Document Title":rfid`，可再加外层括号 `(...) AND scheduling`。

**写法二：无字段名（官方默认搜全部 metadata，运算符示例均为此风格）**：
- `"wireless sensor network" AND security`（AND 官方示例）
- `REV OR "renewable energy vehicle"`（OR 官方示例）
- `gasoline NOT diesel`（NOT 官方示例）
- `implantable NEAR/3 cardiac`（NEAR 官方示例）
- `implantable ONEAR/3 cardiac`（ONEAR 官方示例）

> **读法**：字段名（`"Document Title":`、`"Publication Title":`）用于**精确限定**——官方明确禁止"字段名后直接跟括号"（`"Document Title":("a" OR b)` 无效），同字段多词要么逐词重复字段名 + OR，要么干脆不写字段名（默认 metadata）。**宽泛查全检索（Query A）与邻近检索（Query D）默认不写字段名**，贴合官方运算符示例风格；需要高精度时才加 `"Document Title":`。

### Step 3: Provide a Search Strategy and Refinement Guide
Beyond a single query, provide the user with a multi-step strategy for iterative searching:

1. **Initial Broad Search**: A query for a comprehensive first pass — **Query A** (no field restrictions; searches all metadata by default, per official Command Search behavior). If even broader coverage is needed, restrict nothing (the default already searches metadata); optionally swap in `"Abstract":` where a specific field is useful.
2. **Focused Core Search**: A refined query using `"Document Title":` for high-precision results (**Query B**), optionally targeting specific conference proceedings or journals (`"Publication Title":`, Query C).
3. **Forward/Backward Citation Tracking**: Instructions on how to use IEEE Xplore's `References` and `Cited By` features to find foundational and latest works.
4. **Results Filtering**: A reminder to use the left-side filters for `Content Type` (Conference Publications, Journals & Magazines, Early Access), `Publication Year`, and `Author`.

### Step 4: Output the Final Query and Strategy
Present the finalized search query in a clearly formatted text box that the user can copy and paste **directly into the IEEE Xplore Advanced Search → Command Search input box** (NOT the default search bar or the structured-form fields). Always label the block as a **Command Search query** and remind the user of the correct paste location. Provide a brief, bullet-point guide for immediate next steps.

## Output Format

### 1. Deconstructed Search Concepts
- **Tier 1 – Species/Object**: [keyword1], [keyword2], ...
- **Tier 2 – Technology/Method**: [keyword1], [keyword2], ...
- **Tier 3 – Application/Task**: [keyword1], [keyword2], ...
- **Excluded Terms** (if any): [term1], [term2], ...

### 2. Ready-to-Use IEEE Xplore Queries — **Advanced Search › Command Search**

> ⚠️ **粘贴位置说明**：以下所有检索式专用于 IEEE Xplore 的 **「Advanced Search（高级检索）」页面里的 Command Search（命令行检索）输入框**，**不是**默认的结构化表单（Structured Search）。
> **正确操作路径**：进入 IEEE Xplore → 点击 **Advanced Search** → 切到 **Command Search** 标签页 → 将下方检索式整段粘入文本框 → 点 **Search**。
> 若误贴进结构化表单或默认检索框，会因语法不被识别而报错。本 skill 产出的全部检索式均为 **Command Search 检索词**。

**Query A (Command Search): Broad Sensitivity Search (for maximum recall)**
> 💡 官方默认风格：**不写字段名**（自动搜全部 metadata，见官方运算符示例）。`"Abstract":` 只检索摘要，覆盖范围小于 All Metadata，二者不等价。25-term 限制按单个 search clause 校验，不按整条查询累计 OR 同义词。
```
("[concept1]" OR "[synonym1]") AND ("[concept2]" OR "[synonym2]") AND ("[concept3]" OR "[synonym3]") NOT ("[excluded1]" OR "[excluded2]")
```
*Example:*
```
("fish" OR "aquaculture fish" OR "fish fillet" OR "whole fish") AND ("spectral imaging" OR "hyperspectral imaging" OR "multispectral imaging" OR "near-infrared imaging") AND ("quality assessment" OR "freshness" OR "spoilage" OR "adulteration") NOT ("chemical method" OR "fruit")
```
*说明：OR/AND/NOT 会分隔 search clause；本例每个原子 clause 均远低于 25 个连续检索词。年份在结果页左侧 `Publication Year` 过滤。此写法与官方 AND/OR/NOT 示例（`"wireless sensor network" AND security`）风格一致。*

**Query B (Command Search): High-Precision Core Search (for maximum specificity)**
> 💡 高精度检索推荐加 `"Document Title":` 字段限定（官方明确支持）；每个 OR 项前带字段名（`"Document Title":("a" OR b)` 无效）。
```
("Document Title":"[critical_concept1]" OR "Document Title":"[critical_synonym1]") AND ("Document Title":"[critical_concept2]")
```
*Example:*
```
("Document Title":"semantic segmentation" OR "Document Title":"instance segmentation") AND ("Document Title":"medical image")
```
*说明：若结果过少，可去掉字段限定改无字段名写法 `("semantic segmentation" OR "instance segmentation") AND ("medical image")`（默认 metadata，覆盖更广）；年份用左侧过滤。*

**Query C (Command Search): Conference-Specific Search (for cutting-edge methods)**
```
("[concept]" OR "[synonym]") AND ("Publication Title":"[conference_name]" OR "Publication Title":"[conference2]")
```
*Example:*
```
("image segmentation" OR "object detection") AND ("Publication Title":"CVPR" OR "Publication Title":"ICCV" OR "Publication Title":"ICRA")
```
*说明：会议限定必须用 `"Publication Title":`（概念词可无字段名，默认 metadata）。*

**Query D (Command Search): Proximity Search (NEAR/ONEAR — captures method–task co-occurrence within a tight window, command search only)**
> 💡 官方 NEAR/ONEAR 示例为无字段名简单形式（`implantable NEAR/3 cardiac`）。若要给参与项加字段限定，每个 OR 项前重复字段名（禁止字段内括号 OR）。
```
("[domain1]" OR "[domain2]") AND (("[method1]" OR "[method2]") NEAR/10 ("[task1]" OR "[task2]"))
```
*Example:*
```
(fish OR "aquaculture fish") AND (("spectral imaging" OR "hyperspectral imaging") NEAR/10 (freshness OR grading))
```
*说明：NEAR/ONEAR 是 Command Search 专属（结构化检索不可用）。`NEAR` = 无序（两词任一先后均可），`ONEAR` = 有序（左项必须在前）；运算符全大写。参与项与 Query A 一样默认无字段名（官方示例风格）；需要精确限定再按 Query B 的格式加字段名。*

### 3. Search Strategy & Refinement Guide
- **Step 1**: Start with **Query A**. Sort results by `Relevance` to quickly assess the landscape.
- **Step 2**: Use the left-side filters. Under `Content Type`, select `Conference Publications` and `Journals & Magazines`. Check `Early Access` for the latest pre-print publications.
- **Step 3**: For key conferences in your field, use **Query C** to restrict your search to those venues (e.g., CVPR, ICCV, ICRA, IROS for computer vision and robotics).
- **Step 4**: Use **Query B** to narrow down the most relevant papers. Sort by `Most Cited` to identify high-impact papers.
- **Step 5 – Backward Search**: For any key paper you find, click on its `References` to discover foundational literature.
- **Step 6 – Forward Search**: Click on `Cited By` for the most highly-cited papers to see who has built upon this work.
- **Step 7 – Alert**: Click `Create Alert` on your finalized search to receive email updates on new matching publications.

## Important Notes
- **Field codes are OPTIONAL limiters, not a mandatory prefix**: IEEE Xplore Command Search searches **all metadata fields by default** when no field name is given (official help: "IEEE Xplore looks for a keyword in all fields (metadata) unless you limit the search to specific fields"). Official operator examples — `"wireless sensor network" AND security`, `REV OR "renewable energy vehicle"`, `gasoline NOT diesel`, `implantable NEAR/3 cardiac` — all use no field names. Use `"Document Title":` / `"Abstract":` / `"Publication Title":` when you need to limit the search to a specific field. Short codes like `ti`/`ab`/`au` are Web of Science syntax and will NOT work on IEEE Xplore.
- **Multi-word values must be quoted**: `"Document Title":"deep learning"` matches the phrase, whereas `"Document Title":deep learning` is parsed as `deep AND learning`. Same rule applies to unqualified phrases: `"deep learning"` (quoted) vs `deep learning` (AND).
- **No parentheses inside a single field with OR** (official): `"Document Title":(A OR B)` is invalid; write `"Document Title":A OR "Document Title":B`, then group externally if needed: `("Document Title":A OR "Document Title":B) AND scheduling`.
- **Index Terms (`"Index Terms":`)** combines Author Keywords + IEEE Terms + MeSH Terms. Prefer it for standardized technical terms (e.g., `"Index Terms":"Convolutional neural networks"`).
- **Proximity operators** (`NEAR/n`, `ONEAR/n`) are **command-search only** — unavailable in the default structured advanced search. Operators must be ALL CAPS. Official simple form: `implantable NEAR/3 cardiac`.
- **Operator precedence (no parentheses)**: `NEAR`/`ONEAR` > `NOT` > `AND` > `OR`. Always parenthesize mixed `OR`/`AND` groups, e.g. `(A OR B) AND (C OR D)`.
- **Date**: no dedicated year field in the official Command Search field list — use the left-side `Publication Year` filter. Do NOT emit a `"Publication Year":` clause (not in the official field list).
- **Limits**: ≤ 25 consecutive search terms per search clause; Boolean operators separate clauses. Do not apply 25 as a whole-query synonym limit. A query may contain at most 10 wildcards, and at least three characters must precede each wildcard. Search is case-insensitive.
- **Author names**: try multiple formats — `"Authors":"LeCun, Y."` and `"Authors":"Yann LeCun"`.
- IEEE Xplore is predominantly English IEEE / partner content. For broader coverage, run Scopus or Web of Science in parallel.
- Generated queries are starting points — iterate: too few results → drop field restrictions (or remove `"Document Title":` to search all metadata); too many → add `"Document Title":` or `"Abstract":` restrictions or constrain `"Publication Title":`.
