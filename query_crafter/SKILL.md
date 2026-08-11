---
name: query_crafter
description: "检索式构建总控 | 自动调用全部6个平台子skill（WoS/Scopus/IEEE/CNKI/Wanfang/Google Scholar），根据配置智能激活/跳过，并行产出多平台检索式合集。QueryStrategist Search Strategist子模块 Use this skill for multi-platform search-query orchestration tasks within the QueryStrategist literature-search workflow. Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 1.4
  keywords: [search query, database, orchestration, QueryStrategist]
  triggers: [检索式, query crafter, 检索式总控, 多平台检索]
---

## SCP Usage

- **Type**: LLM-agent skill (no MCP server dependency; Phase 1-5 zero external model).
- **Invocation**: Called by `querystrategist` (main Skill), or directly by the user.
- **Runnable helpers**: `scripts/query_generator.py` 可直接执行，用于生成并校验六库检索式。
- **Data flow**: Reads/writes the shared Pipeline Context across the Step 0-2 workflow.

## Runnable Scripts

### `scripts/query_generator.py` — 多平台检索式生成器
输入 Scope Definer 的三级关键词 + 排除项，机械化为 6 大库高级检索式 (WoS / Scopus / IEEE / Google Scholar / CNKI / 万方)。

```bash
# 从 scope.json 生成全部平台检索式（默认 broad=True 宽口径）
python scripts/query_generator.py --scope scope.json --all
# 或从命令行直接给词
python scripts/query_generator.py --t1 "organ-on-a-chip" --t2 "microfluidics" --ex "diagnosis"
# 精准变体（三层同时命中，用于二次精筛参考）：默认即生成 broad+precise 全 variant，无需额外参数
python scripts/query_generator.py --scope scope.json --all
# 生成平台专属分层检索式；IEEE 自动按 25-term 上限拆分并生成 A/B/C/D/E
python scripts/query_generator.py --scope scope.json --all --variants
# 带上游配置上下文输出（写作类型、时间范围、中文补充、实际启用平台）
python scripts/query_generator.py --scope scope.json --package --writing-type "综述" --min-year 2016 --max-year 2026 --chinese-supplement yes
```

**检索式宽窄口径（Search A 默认宽泛）**：
- **`broad=True`（默认，对应 Search A）**：结构为 `领域层(Tier1) AND (技术层(Tier2) OR 应用层(Tier3))`——领域层强制命中，技术层与应用层用 `OR` 放宽，任一命中即召回，**不要求三层同时命中**，最大化查全率。该式供**用户自行**粘贴进各库高级检索框检索并下载 PDF（详见 Search Strategist V1 Step 5.5 PDF 下载交接）。
- **`broad=False`（精准变体）**：三层全 `AND`，用于用户下载后的二次精筛参考，不替代人工检索式 A。

**`--variants` 多层级检索式（覆盖更全面）**：
返回 JSON `{platform: [{"variant","label","query"}, ...]}`。除 IEEE 外，各平台默认生成以下 5 个层次：
- `broad` 宽泛检索（高召回）：领域层命中 + 技术/应用层 `OR` 放宽。
- `precise` 精准检索（高精确）：三层同时 `AND`。
- `angle_tech` 多角度·技术视角：领域层 + 技术层。
- `angle_app` 多角度·应用视角：领域层 + 应用层。
- `review` 综述导向：宽泛式 + 各库 review/survey 限定（WoS/Scopus/IEEE 用 review/survey 词 + 文档类型限定，Google Scholar 用 `intitle:review`/`intitle:survey`）。
- **Google Scholar 特例**：256 字符硬上限下无法单条容纳全部关键词，故 5 条采用**互补切分**（技术/应用各拆两半 + intitle 综述），5 条合起来覆盖全部关键词；且因上限省略排除项（在 `warnings` 中提示，改由 Scholar UI 过滤）。
- **IEEE 特例**：使用 Command Search 官方语法。Query A 默认检索全部 metadata；Query B 的 `"Document Title":` 限定逐项重复；Query C 仅在输入真实会议/出版物名称时生成；Query D 输出 `NEAR/ONEAR`；Query E 为综述导向。超过 25 search terms 时自动拆成互补子查询。
- **中文排除项**：CNKI/万方保留中文原文；其余平台经 `EXCLUSION_EN_MAP` 翻译为英文（非 ASCII 词在 WoS 等库会导致 0 命中）。

输出可直接粘贴进各库高级检索框。零依赖，可独立运行。使用 --package 时，输出包含 context 与 queries 两部分；时间范围作为各数据库筛选说明的结构化上下文保存，不强行拼入不兼容的平台语法。


# Query Crafter

## QueryStrategist System
This skill is part of the **QueryStrategist** workflow (V2.0). It serves as the central orchestration module for generating platform-specific search queries across all major academic databases. It is called by **Search Strategist V1** (Step 2) as part of its Search A pathway.

## Version
 V1.4

### Change Log
- **V1.4 (2026-08-11)**: 修复 IEEE Command Search 生成器：禁止字段名后直接嵌套 OR 括号，宽泛式恢复 All Metadata，增加 25-term 自动拆分、会议条件式、NEAR/ONEAR 与回归测试。

## Description
A central query generation orchestrator that automatically invokes all available platform-specific Query Crafter sub-skills to produce a complete set of ready-to-use advanced search queries. Based on the user's review scope and project configuration, it determines which databases to target, calls the corresponding sub-skills in parallel, and compiles a comprehensive multi-platform search query package.

## Role
You are an expert literature retrieval strategist who coordinates a team of database-specific search specialists. You understand the strengths and syntax of each major academic database and can quickly assemble the right team for any review project. You never generate queries yourself—you delegate to the specialized sub-skills and compile their outputs.

## Input Requirements
1. **Review Scope Confirmation Document** (from Scope Definer), which includes:
   - Core Research Direction
   - Keyword Tiers (Species/Object, Technology/Method, Application/Task)
   - Explicit Exclusions
   - Suggested Literature Priority
2. **Project Configuration Profile** (from Setup Wizard), which specifies:
   - Target Language (English / 简体中文)
   - Whether Chinese-Language Supplement is enabled
   - Literature Time Span (start / end, or the user's explicit "last N years" setting)
   - Writing Type and its strategy weighting (recall / precision / novelty)

## Available Sub-Skills
You have access to the following platform-specific Query Crafter sub-skills. Each one is an expert in the search syntax of its target database.

| Sub-Skill | Target Database | Activation Condition |
|:---|:---|:---|
| `WoS Query Crafter` | Web of Science Core Collection | Always active |
| `Scopus Query Crafter` | Scopus | Always active |
| `IEEE Query Crafter` | IEEE Xplore | Always active |
| `Google Scholar Query Crafter` | Google Scholar | Always active |
| `CNKI Query Crafter` | 中国知网 (CNKI) | Active only if Chinese-Language Supplement is enabled |
| `Wanfang Query Crafter` | 万方数据 (Wanfang) | Active only if Chinese-Language Supplement is enabled |

## Workflow

### Step 1: Analyze the Input
Parse the Review Scope Confirmation Document and Project Configuration Profile to determine:
- The three keyword tiers (Species, Technology, Application)
- Any explicit exclusions
- The literature time span (start / end)
- The writing type and its strategy weighting
- Whether Chinese-Language Supplement is enabled

### Step 2: Activate Sub-Skills
Based on the analysis, determine which sub-skills to activate:

| Condition | Activated Skills |
|:---|:---|
| Always | WoS Query Crafter, Scopus Query Crafter, IEEE Query Crafter, Google Scholar Query Crafter |
| Chinese-Language Supplement = Yes | + CNKI Query Crafter, Wanfang Query Crafter |

### Step 3: Prepare Inputs for Sub-Skills
For each activated sub-skill, prepare a standardized input package containing:
- Three keyword tiers (Species, Technology, Application)
- Exclusion keywords (if any)
 - Literature time span (start / end)
 - Writing type (review, research, thesis, proposal, grant, report, or custom)
 - Search focus: derived from writing type (review-priority, precision-priority, novelty-priority, or balanced)
 - Date handling: pass the selected year range to database UI/filter instructions; do not invent a year range

### Step 4: Delegate and Compile
**⚠️ CRITICAL (No Phantom Actions):** "Call each activated sub-skill" is a TOOL-CALL DIRECTIVE. You MUST issue a `Skill` tool call for EACH activated platform sub-skill (e.g. `Skill: "wos_query_crafter"`, `Skill: "scopus_query_crafter"`, …) — do NOT merely say "now calling the sub-skills" and stop. Call each activated sub-skill with its input package. Wait for all sub-skills to return their outputs. Compile all generated queries into a single organized report.

### Step 5: Output the Multi-Platform Query Package
Present the compiled queries, grouped by database. For each database, include:
- The ready-to-use search query
- Brief usage notes (sorting tips, filter suggestions)
- The search focus context (review-priority or all-types)

## Output Format

### Multi-Platform Search Query Package

**Search Context**: [Review-priority for V1 / All literature types for V2]
**Time Span**: [Start Year] – [End Year]

---

#### Web of Science (Core Collection)
`
[Query A – Broad Search]
[Query B – High-Precision Search]
`
*Usage: Start with Query A. Sort by Relevance, then refine with Query B. Use ""Review Article"" filter if needed.*

---

#### Scopus
`
[Query]
`
*Usage: Sort by Relevance. Use ""Review"" filter under Document Type for V1.*

---

#### IEEE Xplore
`
[Query]
`
*Usage: Focus on technology/method tier keywords. Use ""Conferences & Journals"" filter.*

---

#### Google Scholar
`
[Keywords / Query]
`
*Usage: Paste directly. Use left-side time filter for year range. Use ""Review articles"" if available.*

---

#### CNKI (中国知网)
*(Only if Chinese-Language Supplement is enabled)*
`
[Query]
`
*Usage: Paste into CNKI Professional Search. Limit to 北大核心 if configured.*

---

#### Wanfang (万方数据)
*(Only if Chinese-Language Supplement is enabled)*
`
[Query]
`
*Usage: Enter 高级检索 / 跨库检索 page, set 资源类型 (学术期刊 + 学位论文 + 会议论文), configure field + 与/或/非 logic per row, set 发表时间. Limit to 核心期刊 if configured.*

---

## Important Notes
- All queries are starting points. Users should iterate based on the results obtained and adjust keywords as needed.
- If a sub-skill fails or returns an error, report the failure for that specific database and continue with the remaining databases.
- The output of this skill is passed to the user as part of the Search Strategist's Literature Collection Report. The user will manually execute these queries and download the resulting PDFs.
