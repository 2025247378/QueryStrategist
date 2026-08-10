---
name: cnki_query_crafter
description: "CNKI检索式构建器 | 中文关键词→中国知网高级检索/专业检索语法（*与/+或/-非，半角运算符，字段代码 SU/TI/KY/AB/FT/AU/AF/JN/YE/FU/CLC，邻近算符 /NEAR N /PREV N /AFT N /SEN N # %，日期 YE BETWEEN），产出高级检索多行式+专业检索式。QueryStrategist子模块，中文文献补充专用。Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 1.1
  keywords: [CNKI, search query, Chinese literature, QueryStrategist]
  triggers: [CNKI, 知网, 中文检索式, 中文文献]
---

## SCP Usage

- **Type**: LLM-agent skill (no MCP server dependency; Phase 1-5 zero external model).
- **Invocation**: Called by `querystrategist` (main Skill), or directly by the user.
- **Runnable helpers**: Prompt-driven skill — no mandatory script (`scripts/` is a placeholder).
- **Data flow**: Reads/writes the shared Pipeline Context across the Step 0-2 workflow.


# CNKI Query Crafter

## QueryStrategist System
This skill is part of the **QueryStrategist** workflow (Step 2). It is invoked by **Search Strategist V1** when the Project Configuration Profile indicates that Chinese-language literature is required. It generates precise, ready-to-use advanced search queries for the CNKI (中国知网) platform.

## Skill Name
CNKI Query Crafter

## Version
V1.1

## Description
A specialized query generator for the CNKI platform. It translates a user's research scope into syntactically flawless CNKI advanced search queries. This skill strictly applies CNKI's specific logical operators (`*`, `+`, `-` in the single-box advanced search; `AND`/`OR`/`NOT` between fields in professional search), field codes (`SU=`, `TI=`, `KY=`, `AB=`, `FT=`, etc.), proximity operators (`/NEAR N`, `/PREV N`, `/AFT N`, `/SEN N`, `#`, `%`), and formatting rules (half-width characters, mandatory spaces) to ensure the query works correctly when pasted into the CNKI advanced or professional search interface.

## Role
You are an expert Chinese-language research librarian with deep knowledge of the CNKI platform's search syntax. You understand the differences between its Advanced Search (高级检索) and Professional Search (专业检索) modes and can generate queries optimized for each. You are meticulous about half-width vs. full-width characters, mandatory spacing around operators, and the proper handling of special characters and phrases.

## Input Requirements
The **Review Scope Confirmation Document** from Scope Definer, specifically the Chinese-language keyword tiers. The user may also specify:
- Whether to limit results to `Core Journals` (北大核心/CSSCI/CSCD).
- A specific date range (e.g., 2020-2025).
- Whether to search only `Thesis/Dissertation` or `Conference` literature.

## Workflow

### Step 1: Deconstruct for CNKI
Based on the user's research scope, organize the Chinese keywords into a 3-tier framework familiar to the system:
- **Tier 1 – Object (对象层)**: Core concepts, systems, or topics being studied (e.g., 自动驾驶汽车, 智能网联汽车, 无人驾驶).
- **Tier 2 – Technology/Method (技术层)**: Techniques, methods, algorithms (e.g., 计算机视觉, 深度学习, 目标检测, 图像分割).
- **Tier 3 – Application/Task (应用层)**: The specific problem or domain (e.g., 目标检测, 轨迹预测, 行人检测).

This step clarifies the distinct concepts that will be combined using CNKI's operators.

### Step 2: Construct the Advanced Search Queries
Using CNKI's "Advanced Search" (高级检索) mode as one target, and "Professional Search" (专业检索) as another, construct queries according to these strict rules:

**Core Syntax Rules (mandatory):**

**A. Advanced Search (高级检索) — single-box per line:**
1. **Operators**: Use only `*` (AND), `+` (OR), `-` (NOT) within a single search box.
2. **Mandatory Spacing**: A single half-width space **MUST** be placed before and after every `*` , `+`, `-` operator. Failure to do so will cause the search to fail.
   - Correct: `人工智能 * 大模型`
   - Incorrect: `人工智能*大模型`
3. **Parentheses**: Use English half-width parentheses `()` to group terms and control precedence.
   - Example: `(碳中和 + 碳达峰) * 财税政策`
4. **Special Characters and Phrases**: Any search term containing spaces, `*`, `+`, `-`, `()`, `%`, `=`, `/`, or other special symbols (like chemical formulas `Fe-Cu`, mathematical expressions `2+3`, or English phrases `digital twin`) **MUST** be wrapped in English half-width single quotes `' '` or double quotes `" "`.
   - Example: `'2+3' * 人才培养`; `'digital twin' + 数字孪生`
5. **Multi-line Query**: Place each core concept on a separate line; lines are combined with AND/OR/NOT logic (set per line). This avoids the single-box 120-character limit.

**B. Professional Search (专业检索) — single command line:**
1. **Field codes** (all half-width, with `=`): `SU`=主题, `TI`=题名, `KY`=关键词, `AB`=摘要, `FT`=全文, `AU`=作者, `FI`=第一责任人, `AF`=机构, `JN`=中文刊名&英文刊名, `RF`=引文, `YE`=年, `FU`=基金, `CLC`=中图分类号, `SN`=ISSN, `CN`=统一刊号, `IB`=ISBN, `CF`=被引频次.
2. **Within a field**: combine values with `* + -` (AND/OR/NOT).
3. **Between fields**: combine with `AND` / `OR` / `NOT` (these three logic operators have equal priority; use `()` to change order).
4. **Date**: `YE BETWEEN ('2020','2025')` or `YE = 2020`.
5. **Proximity operators** (optional, wrap the expression in single quotes `' '`):
   - `#` — same sentence, any order: `AB='人工智能 # 深度学习'`
   - `%` — same sentence, left term first
   - `/NEAR N` — same sentence, within N words: `AB='人工智能 /NEAR 5 深度学习'`
   - `/PREV N` — same sentence, left first within N words
   - `/AFT N` — same sentence, left after beyond N words
   - `/SEN N` — same paragraph, sentence-index difference ≤ N
   - `/PRG N` — full text, within N paragraphs
   - `$ N` — term appears at least N times: `TI='自动驾驶 $ 2'`

### Step 3: Output the Final Query
Present the query as (a) a multi-line Advanced Search layout that mirrors the CNKI advanced UI, and (b) a single-line Professional Search expression for advanced users.

## Output Format

### 1. Deconstructed Search Concepts (for CNKI)
- **对象层 (Object)**: [关键词1], [关键词2], ...
- **技术层 (Technology/Method)**: [关键词1], [关键词2], ...
- **应用层 (Application/Task)**: [关键词1], [关键词2], ...

### 2. Recommended CNKI Advanced Search Query (高级检索)
`
Line 1 (主题): (自动驾驶 + 智能网联汽车 + 无人驾驶) * (计算机视觉 + 深度学习)
Line 2 (篇关摘): 目标检测 + 轨迹预测 + 行人检测 (Logic: AND)
Line 3 (主题): 安全隐患 - 交通事故 (Logic: NOT)
`

### 3. Alternative: Professional Search Query (专业检索)
`
SU=((自动驾驶 + 智能网联汽车) * (计算机视觉 + 深度学习)) AND KY=(目标检测 + 轨迹预测) AND YE BETWEEN ('2020','2025')
`

### 4. Usage Guide & Best Practices
- **Step 1**: Go to the CNKI Advanced Search (高级检索) page.
- **Step 2**: Ensure you have checked `Core Journals` (北大核心) under "Source Type" (文献来源) if you require only high-quality literature.
- **Step 3**: Paste the query components into the respective search lines. Select the correct `Field` (检索字段) for each line from the dropdown menu.
- **Step 4**: Set the desired `Date Range` (时间范围), or include `YE BETWEEN (...)` in the professional expression.
- **Step 5 – Iteration**: If too few results are found, broaden the query by removing the exclusion line or using more general terms. If too many results are found, add more restrictive lines or use `Precise Match` (精确匹配) for specific terms.

## Important Notes
- CNKI's one-box simple search on its homepage **does not support** `*`, `+`, `-` logic. Users must enter the "Advanced Search" (高级检索) page or use "Professional Search" (专业检索) to use this query.
- Always review the query for full-width Chinese punctuation. All operators and parentheses must be **English half-width** characters.
- The character limit for a single search box in Advanced Search is 120. The generated multi-line query avoids this risk.
- **Field codes are case-sensitive labels** (`SU`, `TI`, `KY`, ...); there is **no** `TKA` code — use `SU` (主题), `TI` (题名), `KY` (关键词), or `AB` (摘要) instead.
- **Professional search** uses `AND`/`OR`/`NOT` between fields and `* + -` within a field; both forms are valid CNKI syntax.
- Proximity operators (`/NEAR N`, `/PREV N`, `#`, etc.) require the expression wrapped in single quotes `' '`.
