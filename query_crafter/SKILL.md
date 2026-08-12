---
name: query_crafter
description: "检索式构建总控 | 自动调用全部6个平台子skill（WoS/Scopus/IEEE/CNKI/Wanfang/Google Scholar），根据配置智能激活/跳过，并行产出多平台检索式合集。QueryStrategist Search Strategist子模块 Use this skill for multi-platform search-query orchestration tasks within the QueryStrategist literature-search workflow. Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 1.9
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
# 分层变体：默认生成 A0 召回基线、A1 主题检索和 B 平台专属精准式
python scripts/query_generator.py --scope scope.json --all
# 生成平台专属分层检索式；IEEE 按每个 search clause 的 25-term 上限校验并生成 A/B/C/D/E
python scripts/query_generator.py --scope scope.json --all --variants
# 带上游配置上下文输出（写作类型、时间范围、中文补充、实际启用平台）
python scripts/query_generator.py --scope scope.json --package --writing-type "综述" --min-year 2016 --max-year 2026 --chinese-supplement yes
```

**检索式宽窄口径（Search A 分层召回）**：
- **`broad=True`（默认，对应 A0）**：六库统一使用 `对象层(Tier1) AND 必需技术锚点(Tier2 Anchor)`；不强制任务层，不拼接排除项、年份或文献类型。若 Scope 提供 `tier1_recall_anchor`，A0 将其并入对象组；`tier2_supporting_method` 不得替代必需技术锚点。
- **`topical=True`（对应 A1）**：使用 `对象层 AND 必需技术锚点 AND 任务层`，并从这一层开始应用经核对的排除项。
- **`broad=False`（精准变体）**：使用各平台专属收紧规则（例如 WoS 标题 + `NEAR/10`、Scopus 标题 + `W/5`、CNKI 题名/主题字段、万方精确匹配），不替代人工检索式 A。

**`--variants` 多层级检索式（覆盖更全面）**：
返回 JSON `{platform: [{"variant","label","query"}, ...]}`。各平台默认生成以下核心层次：
- `broad` / A0 召回基线：对象 + 必需技术；不加任务、排除项、年份和文献类型。
- `topical` / A1 主题检索：对象 + 必需技术 + 任务；允许应用明确排除项。
- `precise` 精准检索（高精确）：调用各平台专属收紧规则；不能把所有平台简化为同一条“三层 AND”模板。具体规则以各平台子 Skill 和输出标签为准。
- `review` 综述导向：A1 主题式 + 各库 review/survey 限定。
- **Google Scholar 特例**：A0 与 A1 分别生成不超过 6 条互补短查询，按分组序号配对，禁止三层笛卡尔积和静默截断；A0 省略排除项。
- **IEEE 特例**：使用 Command Search 官方语法。A0 为对象+技术的 All Metadata 召回基线；A1 为对象+技术+任务的主题式；B 仅在题名中锁定对象+技术，不强迫任务词也出现在题名；C 仅在输入真实会议/出版物名称时生成；D 输出技术层与任务层的 `NEAR/ONEAR`；E 为综述导向。对象层自动补充重复出现的中心词（如多个复合短语中的 `fish`），也可读取 `tier1_recall_anchor`。25-term 限制按单个连续 search clause 校验。
- **中文词表与排除项**：CNKI/万方优先读取 `keyword_tiers_zh` / `explicit_exclusions_zh`；缺失时回退主词表并报警。其余平台经 `EXCLUSION_EN_MAP` 处理中文排除描述。

输出可直接粘贴进各库高级检索框。零依赖，可独立运行。使用 --package 时，输出包含 context 与 queries 两部分；时间范围作为各数据库筛选说明的结构化上下文保存，不强行拼入不兼容的平台语法。


# Query Crafter

## QueryStrategist System
This skill is part of the **QueryStrategist** workflow (V2.0). It serves as the central orchestration module for generating platform-specific search queries across all major academic databases. It is called by **Search Strategist V1** (Step 2) as part of its Search A pathway.

## Version
 V1.9

### Change Log
- **V1.9 (2026-08-12)**: 六库统一采用 A0/A1/B 分层语义：A0 仅对象+必需技术且不加排除，A1 恢复对象+技术+任务并应用排除，B 使用平台专属字段/邻近规则；Google Scholar 取消三层笛卡尔积，A0/A1 各最多生成 6 条互补短查询。
- **V1.8 (2026-08-12)**: 修复真实 IEEE 零命中案例：IEEE A0 改为对象+技术召回基线，A1 保留三层主题式，B 改为题名对象+技术；对象复合短语自动提取重复中心词作为召回锚点，并支持 `tier1_recall_anchor`。其余五库规则不变。
- **V1.7 (2026-08-11)**: 精准变体不再复用 Search A 原式：WoS 使用标题对象与 `NEAR/10`，Scopus 使用标题对象与 `W/5`，CNKI 使用题名/主题字段组合，万方启用精确匹配；Search A 缺失对象、技术锚点或任务层时快速失败。
- **V1.6 (2026-08-11)**: 六库 Search A 统一为三概念强制共现，新增必需技术锚点与中英文双词表；Google Scholar 改为完整互补查询列表；WoS 单词保留词形还原；万方对齐当前官方专业检索框。
- **V1.5 (2026-08-11)**: 修正 IEEE 25-term clause 口径与默认漏词；Query A 完整保留同义词，单词保留词干扩展，多词短语精确匹配；增加 10-wildcard/最小前缀校验；Query D 改为技术层与任务层邻近共现。
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
- Optional object/task recall anchors (`tier1_recall_anchor` / `tier3_recall_anchor`), required technology anchors (`tier2_required_anchor`), and supporting methods (`tier2_supporting_method`)
- Chinese database tiers (`keyword_tiers_zh`) and Chinese exclusions (`explicit_exclusions_zh`) when CNKI/Wanfang are enabled
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
[Complementary Query A1]
[Complementary Query A2, if needed]
`
*Usage: Run each line as an independent search. Use the time filter for the year range.*

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
*Usage: In Professional Search select 全部主题/主题, paste the Boolean expression, and set 发表时间 in the UI; or reproduce it row-by-row in Advanced Search.*

---

## Important Notes
- All queries are starting points. Users should iterate based on the results obtained and adjust keywords as needed.
- If a sub-skill fails or returns an error, report the failure for that specific database and continue with the remaining databases.
- The output of this skill is passed to the user as part of the Search Strategist's Literature Collection Report. The user will manually execute these queries and download the resulting PDFs.
