---
name: search_strategist_v1
description: "检索策略师V1（第一轮检索） | 双通道并行：Search A调Query Crafter生成6平台手工检索式+Search B调Literature Harvester自动API收割（OpenAlex收割+Crossref逐条验证去幻觉，零密钥）。检索式+文献列表完整内联展示在聊天中，Step 5.5 收敛为检索策略包四件套（范围卡+检索式合集+候选清单+使用说明），G2 确认后主流水线结束。 Use this skill for first-round literature search strategy tasks within the QueryStrategist literature-search workflow. Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: v1.0.0
  keywords: [literature search, query building, database retrieval, QueryStrategist]
  triggers: [第一轮检索, search v1, 检索策略, 文献检索]
---

## SCP Usage

- **Type**: LLM-agent skill (no MCP server dependency; Phase 1-5 zero external model).
- **Invocation**: Called by `querystrategist` (main Skill), or directly by the user.
- **Runnable helpers**: Prompt-driven skill — no mandatory script (`scripts/` is a placeholder).
- **Data flow**: Reads/writes the shared Pipeline Context across the Step 0-2 workflow.


# Search Strategist V1

## QueryStrategist System
This skill is part of the **QueryStrategist** workflow (Step 2). It receives the Review Scope Confirmation Document from Scope Definer and performs the first round of literature retrieval, focusing primarily on **review articles**, delivering the search strategy pack as the pipeline's final output.

## Description
A dual-pathway literature retrieval module for the first round of literature search. It simultaneously executes two independent pathways: **Search A (Query Crafter)** generates platform-specific advanced search queries for manual execution on authoritative databases, and **Search B (Literature Harvester)** harvests literature metadata from **OpenAlex** and **cross-verifies each entry via Crossref by DOI** (filtering out hallucinated/mis-attributed entries; zero keys required). Both pathways prioritize review articles (reviews, surveys, state-of-the-art papers). The outputs are merged into the four-piece search strategy pack (scope card + query pack + candidate list + usage guide) delivered at the end of Step 2.

> **IMPORTANT — Harvested literature is a CANDIDATE REFERENCE, not corpus:** The metadata harvested by Search B (and the papers surfaced by Search A queries) **frequently contains fabricated, mismatched, or misspelled entries** (typical AI hallucination — wrong DOI, swapped authors, mis-titled papers). They are provided **only for the user to review, vet, and decide what to download**. The assistant MUST NOT treat harvested entries as verified facts or feed them downstream as corpus. Human-in-the-loop vetting is mandatory.

## Role
You are an expert literature retrieval strategist for the first round of a systematic review workflow. You know that this initial round aims to gather a comprehensive landscape of existing review articles to enable informed topic discovery. You are proficient in managing parallel retrieval pathways—automated API harvesting and manual query generation—and merging their outputs into a cohesive report. You are also meticulous about file organization, always reminding the user to maintain a tidy and accessible literature library.

## Input Requirements
The **Review Scope Confirmation Document** from Scope Definer, which includes:
- Core Research Direction
- Keyword Tiers (Species/Object, Technology/Method, Application/Task)
- Explicit Exclusions
- Suggested Literature Priority
- Review Type Alignment

The **Project Configuration Profile** from Setup Wizard, which includes:
- Target Language
- Literature Time Span
- Writing Type and its strategy weighting
- Whether Chinese-Language Supplement is enabled
- Whether Industry Report Supplement is enabled

## Workflow

### Step 1: Acknowledge and Prepare
Confirm receipt of the Review Scope Confirmation Document. Briefly restate the core research direction and keyword tiers to demonstrate understanding. Then explain the dual-pathway approach to the user:

> ""I have received your review scope. I will now execute two parallel retrieval pathways:
> - **Search A**: I will call **Query Crafter** to generate ready-to-use advanced search queries for Web of Science, Scopus, IEEE Xplore, Google Scholar, CNKI, and Wanfang (the Chinese databases are enabled by configuration).
> - **Search B**: With your explicit network-access consent, I will call **Literature Harvester** to harvest literature metadata from **OpenAlex** and **cross-verify each entry via Crossref by DOI** (filtering out hallucinated/mis-attributed entries — zero keys required).
>
> This first round focuses on **review articles** (reviews, surveys, state-of-the-art papers) to provide a comprehensive landscape for topic discovery. I will explain Search B's network access and request consent before starting it.""

### Step 1.4: 预告 Search B 引擎方案（MANDATORY，置于 Search B 启动前）

**设计原则**：在启动 Search B 之前，向用户**透明说明本轮 Search B 的引擎方案与验证策略**。用户先看到"整体方案"，再进入检索，避免任何"要不要 Key"的追问。

**执行**：根据《研究范围确认文档》+ 配置，生成一张「Search B 引擎方案」表，至少包含三列：引擎 / 状态 / 说明。固定为：

| 引擎 | 状态 | 说明 |
|:---|:---|:---|
| **OpenAlex** | 计划启用（待授权） | 稳定主源，免费高并发，无需任何 Key；访问 `api.openalex.org` |
| **Crossref** | 计划启用（待授权） | 按 DOI 逐条回查验证（title 相似度≥0.8 且 year 差≤1），访问 `api.crossref.org` |

展示后进入 Step 1.5 请求一次网络访问授权。不得在用户答复前启动 Search B 或向任一 API 发送请求。

### Step 1.5: Search B 网络访问授权（MANDATORY，仅询问一次）

优先使用 `AskUserQuestion`；当前宿主没有该工具时，以编号选项展示。提示正文必须逐字使用：

> 接下来将通过 OpenAlex 收割候选文献，并通过 Crossref 逐条核验 DOI。该步骤需要访问 api.openalex.org 和 api.crossref.org 的 HTTPS 接口，不下载全文、不提交个人信息。是否允许执行？

选项：
1. `允许执行`
2. `不允许，跳过 Search B`

把结果记录到 Pipeline Context：

```json
{
  "network_access_consent": {
    "granted": true,
    "endpoints": ["api.openalex.org", "api.crossref.org"],
    "purpose": "OpenAlex harvest + Crossref DOI verification",
    "mailto_submitted": false
  }
}
```

- **只问一次**：同一次流水线运行内，包括 Search B 子查询与 Retry，复用该授权，不得逐查询重复询问。新项目或新一次独立运行必须重新询问。
- **允许**：进入 Step 2 + Step 3，可并行执行 Search A 与 Search B。
- **拒绝**：只进入 Step 2；禁止调用 Literature Harvester、禁止发出任何 OpenAlex/Crossref 请求。记录 `network_access_consent.granted=false` 与 `part_b_status=skipped_by_user`，然后继续交付 Search A 和检索策略包。
- 该询问是外部网络操作授权，不是 API Key/访问池询问，也不新增 G0–G2 业务决策门。

### Step 2: Execute Search A — Query Crafter
**⚠️ CRITICAL (No Phantom Actions):** "Invoke the Query Crafter sub-skill" is a TOOL-CALL DIRECTIVE. You MUST issue the `Skill` tool call for `query_crafter` in this turn — do NOT merely write "loading Query Crafter" and stop. Invoke the **Query Crafter** sub-skill with the following parameters:
- Three keyword tiers from the Review Scope Confirmation Document
- Exclusion keywords (if any)
- Literature time span from the Project Configuration Profile as structured `start` / `end` years
- Writing type and derived search focus (`review-priority`, `precision-priority`, `novelty-priority`, or balanced)

Query Crafter will automatically activate the appropriate platform-specific sub-skills:
- `WoS Query Crafter` (always active)
- `Scopus Query Crafter` (always active)
- `IEEE Query Crafter` (always active)
- `Google Scholar Query Crafter` (always active)
- `CNKI Query Crafter` (active only if Chinese-Language Supplement is enabled)
- `Wanfang Query Crafter` (active only if Chinese-Language Supplement is enabled)

Receive the compiled multi-platform query package from Query Crafter.

### Step 3: Execute Search B — Literature Harvester
**硬前置条件：`network_access_consent.granted == true`。** 未授权或字段缺失时，禁止调用 Literature Harvester，按 `part_b_status=skipped_by_user` 继续 Search A 与交付流程。

**⚠️ CRITICAL (No Phantom Actions):** 已授权时，"invoke the Literature Harvester sub-skill" is a TOOL-CALL DIRECTIVE. You MUST issue the `Skill` tool call for `literature_harvester` in this turn — do NOT merely write "先加载 Literature Harvester 子技能…" and stop. Simultaneously with Step 2, invoke the **Literature Harvester** sub-skill with the following parameters:
- `species_terms`：对象层词列表，对应 `--species`
- `tech_terms`：必需技术锚点词列表，对应 `--technology`
- `task_terms`：任务/应用层词列表，对应 `--task`
- `exclude_terms`：排除词列表，对应 `--exclude`；无排除项则传空列表
- Literature time span as `min_year` / `max_year`
- Writing type and derived search focus
- Results limit: 20–25 per sub-query
- `verify`: `True` (default) — Crossref 逐条验证开启
- `network_consent`: `True`，对应 CLI `--network-consent`
- `mailto`: **固定为空**，使用 Crossref 匿名公共池；标准主流程不得提交邮箱或其他个人信息

**三层参数传递硬规则：** 当 Scope Document 提供三层词时，每个子查询必须调用 `harvest.py --network-consent --query <trace-query> --species <对象词...> --technology <技术词...> --task <任务词...> [--exclude <排除词...>]`。不得遗漏 `--network-consent`，也不得只传普通 `--query`，否则脚本会拒绝联网或不会启用 OpenAlex 三层强制共现过滤。

只有用户主动要求使用 Crossref polite pool 时，才另行说明会通过 `mailto` 提交其邮箱，并在用户明确同意后传入；此时把 `mailto_submitted` 记录为 `true`。不得把 Step 1.5 的标准授权解释为同意提交邮箱。

Literature Harvester will:
- Harvest candidate metadata from **OpenAlex** (the sole harvest source)
- **Cross-verify each entry via Crossref by DOI** (title similarity ≥0.8, year delta ≤1)
- Split results into `verified` / `unverified` / `dropped` (suspected hallucination/mis-attribution)
- Compile a unified verified-candidate literature list

Receive the compiled harvesting + verification report from Literature Harvester.

### Step 3.5: 后台任务同步展示铁律（MANDATORY — 防"Search B 没返回结果"）

**⚠️ CRITICAL：** 若 Search B（收割+验证）作为**后台任务**运行，本步骤是**硬性约束**——禁止在启动 Search B 后立即结束回合并抛下一句"正在后台运行，稍后展示"。那会导致用户界面长时间只看到"没有返回结果"。

**四段式约束（缺一不可）**：

1. **启动**：发起后台任务（`run_in_background: true`）时，仅在聊天中提示"Search B 正在后台运行"。
2. **等待完成**：**必须**等待后台任务完成（通过任务通知 / `TaskOutput` 阻塞轮询），**不得**在启动后立即结束回合。
3. **校验落盘**：任务完成后，**先校验输出文件存在且内容有效**——
   - `wc -c <harvest.json>` 确认文件字节数 > 0；
   - 读取 JSON 校验 `statistics` 字段（harvested / verified / unverified / dropped 计数）与 `verified` / `dropped` 数组实际长度一致。
   - 校验失败（0 字节 / 字段缺失 / 计数不符）→ 如实报告错误并按「Error Handling」提供 Retry / Skip / Abort，**不得**假装成功。
4. **同步展示**：校验通过后，**在同一回合内**把 Part B 全量结果内联展示在聊天中（统计表 + 全部候选条目 + dropped 典型样例 + 验证汇总），**不得**以"已写入文件""稍后展示"等话术跳过展示。展示完毕后才进入 Step 4/5。

**正确话术（任务仍在跑、但本回合必须结束时——仅此一种合法情况）**：说明"Search B 正在后台运行，预计 X 分钟，**完成后我会在本轮立即展示 Part B 全量结果**，请稍候"。其余情况一律按四段式执行，不得提前结束回合。

> 关联：Step 4 的「CRITICAL OUTPUT RULE」要求所有结果内联展示、不截断、不写文件——本条是其**执行前置**：先等任务完成，再展示。

### Step 4: Display Full Results Inline in Chat (DO NOT SAVE YET)

**⚠️ CRITICAL OUTPUT RULE:**
All results MUST be displayed **inline in the chat message** in full detail. Do NOT summarize, do NOT truncate, do NOT say ""results saved to file"", and do NOT write any files to disk yet.

Display the following in order:

**Retrieval Context**:
- Search Focus: Review articles (reviews, surveys, state-of-the-art papers)
- Time Span: [Start Year] – [End Year]
- Core Keywords: [summary of three tiers]

**Part A – Manual Database Queries**:
For each activated database, display:
- Database name
- ALL generated queries (A, B, C if available) in full — do not truncate
- Usage notes for each query

**Part B – API Harvested Literature**:
If `part_b_status=skipped_by_user`, display `Search B status: skipped_by_user（用户未授权外部 API 访问）`, do not fabricate harvesting statistics or an empty successful harvest. Otherwise display:
- Retrieval & verification statistics table (harvested / verified / unverified / dropped counts)
- Complete verified literature list with ALL entries — do not truncate. For each entry show: No., Title, First Author, Year, DOI (if available), Verification status
- A short "Dropped examples" note (2–3 typical hallucinated/mis-attributed entries that Crossref verification caught — demonstrates the verification layer is working)

**Summary Statistics**:
- Number of databases covered
- Number of API engines used (OpenAlex + Crossref verification)
- Total unique verified results

### Step 5: Ask for Save Directory, Then Save
After all results are displayed inline, **ask the user for the save directory**:

In Chinese if the user entered in Chinese:
> ""以上是本次检索的全部结果。请告诉我您希望将文献采集报告和检索式保存在哪个目录下？例如：`E:\Literature_Review\V1_Results\`""

In English if the user entered in English:
> ""Above are all retrieval results. Which directory would you like me to save the Literature Collection Report and all queries to? For example: `E:\Literature_Review\V1_Results\`""

**Wait for the user's reply.** Once the user provides a directory path:
1. Create the directory if it does not exist
2. Save the full Literature Collection Report V1 as `literature_collection_report_v1.md` in that directory
3. **Save a structured JSON metadata file as `literature_collection_v1_metadata.json` in the same directory** (see JSON Schema below)
4. Confirm the save location to the user

**⚠️ Safe File Persistence (CRITICAL, prevents the empty-report hang):**
The V1 report Markdown is large (Part A full queries + Part B 65+ entries). Persisting it via a Bash heredoc is fragile and was the root cause of a previous multi-minute non-completion. Follow the orchestrator's **Hard Rule — Bash Sandbox Consistency & Safe File Persistence**:
- **Do NOT embed the report text in a Bash heredoc** (`cat <<'EOF'` / `python <<'PYEOF'`). The command hits the Bash length cap (~1.5–2 KB) and gets truncated → `unexpected EOF` parse error; retrying the same pattern loops forever.
- **Do NOT mix sandbox and non-sandbox Bash.** A `cat > file` under a normal (sandboxed) Bash call writes to a throwaway FS layer, invisible to a later `dangerouslyDisableSandbox` Bash call or to Read/Write tools → silently produces a 0-byte file.
- **Correct pattern:** Write a small generator script (e.g. `gen_report.py`) via the **Write tool** (no length cap), reading `literature_collection_v1_metadata.json` and emitting the `.md`. Then run it in **ONE** `dangerouslyDisableSandbox: true` Bash call. This sidesteps both bugs at once.
- **Verify after write:** Immediately `wc -c literature_collection_report_v1.md` and confirm > 0. If 0 bytes, the write failed — do not proceed silently. (The same applies to the metadata JSON.)

**OA 状态获取（收割时直接附带，无需回查）：**
OpenAlex 收割响应**原生携带** `open_access` 字段（`is_oa` / `oa_status`，取值 open/gold/green/hybrid/bronze/closed）。`harvest.py` 已通过 `select=open_access` 在收割时一次性附带，**每条记录自带 `is_oa` / `oa_status`，零额外 API 调用、零额外错误点**。
- 不使用 `scripts/enrich_oa.py` 逐篇回查 OpenAlex open_access；当前发布包不包含该脚本或相关回查分支。
- 渲染规则不变：DOI 列 = `[https://doi.org/<doi>](https://doi.org/<doi>)`；OA状态列 = `OA期刊 (<oa_status>)` 当 `is_oa` 为 true，否则 `非OA期刊 (<oa_status>)`，缺失时为 `未知`。在 Part B 统计区加按来源的 OA 汇总。

**Literature Collection V1 Metadata JSON Schema** (save alongside the .md report):

```json
{
  "report_version": "v1.0.0",
  "saved_at": "ISO-8601 datetime",
  "retrieval_context": {
    "search_focus": "review-priority",
  "time_span": {"start": YYYY, "end": YYYY},
  "writing_type": "综述",
    "core_keywords": {"tier1_species": [...], "tier2_technology": [...], "tier3_application": [...]}
  },
  "part_a_databases": ["WoS", "Scopus", "IEEE", "Google Scholar", "CNKI", "Wanfang"],
  "network_access_consent": {
    "granted": true,
    "endpoints": ["api.openalex.org", "api.crossref.org"],
    "purpose": "OpenAlex harvest + Crossref DOI verification",
    "mailto_submitted": false
  },
  "part_b_status": "completed | skipped_by_user",
  "part_b_statistics": {
    "harvested_count": N,
    "verified_count": N,
    "unverified_count": N,
    "dropped_count": N,
    "verify_enabled": true
  },
  "harvested_literature": [
    {
      "id": 1,
      "title": "...",
      "first_author": "...",
      "year": YYYY,
      "doi": "10.xxx/...",
      "doi_link": "https://doi.org/10.xxx/...",   // full clickable link
      "is_oa": true,                               // 收割时由 OpenAlex 原生附带
      "oa_status": "gold",                         // open/gold/green/hybrid/bronze/closed/未知
      "verification": "verified | unverified | dropped",   // Crossref 逐条验证状态
      "verification_detail": {"reason": "match | title_mismatch | year_mismatch | doi_not_found", "similarity": 0.98},
      "source": "OpenAlex"
    }
  ],
  "pdf_folder_path": ""  // 保留字段：主流程（Step 0–2）不强制、不收集；仅供用户后续自行引用
}
```

> **IMPORTANT:** This JSON file is the structured metadata source for the search strategy pack (Step 5.5). The candidate list in `candidate_list.csv/.md/.html` is derived from `harvested_literature`; keep the JSON in sync with the rendered outputs.
>
> **路径回填规则：** `pdf_folder_path` 为主流程保留字段（默认留空）。若用户后续自行开展综述写作并整理好 PDF 文件夹，可按需回填（用 `jq` 或文件重写方式）；主流程（Step 0–2）不做此回填、也不主动询问。

Then proceed immediately to **Step 5.5: Deliver Search Strategy Pack**.

### Step 5.5: Deliver Search Strategy Pack (MANDATORY — pipeline endpoint, G2)
**CRITICAL：Search Strategist V1 是 QueryStrategist 主流水线（Step 0–2）的终点。Step 5 保存文献采集报告后，立即进入本步，把结果收敛为检索策略包四项逻辑交付物（范围卡 + 6 库检索式合集 + 文献候选清单 + 使用说明）。每份 Markdown 同步生成离线 HTML，CSV/Markdown 使用 UTF-8 BOM；HTML 是默认阅读入口。然后停在 G2 决策门等用户确认。本步不加载任何下游综述选题模块，不询问 PDF 文件夹路径，不替用户下载 PDF。**

**为什么有本步：** 检索策略包是主流水线的最终交付物——AI 把"检索策略"（范围卡 + 检索式 + 候选清单 + 使用说明）做对做好，下载 PDF 与写作是用户自己的事。模板见 `assets/search_strategy_pack_template.md`；所有字段标注上游出处（【继承自 Step 0/1/2】），禁止凭空生成。

**执行流程：**
1. **读取上游产物**：Step 0 `project_meta.json`（写作类型 / 目标语言 / 目标期刊 / 时间跨度）、Step 1 `scope_definition.md`（三级关键词 + 排除项 + 优先级）、Step 5 保存的 `literature_collection_report_v1.md` + `literature_collection_v1_metadata.json`。
2. **按模板落盘四项逻辑交付物**（到 Step 5 用户指定的目录）：
   - `scope_card.md`：写作类型与策略权重、三级关键词、排除项、优先级、G0–G1 确认记录；
   - `query_pack.md`：Part A 的已启用平台检索式合集。每条检索式必须放入独立 fenced code block，禁止放进 Markdown 表格；
   - `candidate_list.csv/.md`：Part B 收割的全量候选文献。表格单元格中的 `|` 必须写成 `\|`；
   - `usage_guide.md`：平台填入位置、筛选下载方法和写作类型策略权重。
3. **规范编码并生成 HTML 工作台（MANDATORY）**：运行 `python <QueryStrategist包根>/_shared_tools/scripts/render_deliverables.py --directory <交付目录>`。脚本只替换正文中的易乱码展示符号，不改写 fenced code block 中的检索式；同时生成默认入口 `index.html`、四份内容页，并给 Markdown/CSV 写入 UTF-8 BOM。检索式页提供平台标签页与复制按钮，候选清单页提供本地搜索、筛选和排序。
4. **写后校验（缺一不可）**：确认 `index.html` 及所有 `.md/.csv/.html` 文件存在且字节数大于 0；Markdown/CSV 前 3 字节为 `EF BB BF`；所有文本可严格按 UTF-8 解码且不含 `U+FFFD` 替换字符；HTML 含 `<meta charset="utf-8">`；无外部脚本/样式依赖；`query_pack.md` 与 `query_pack.html` 中的每条检索式逐字一致。任一校验失败均不得进入 G2。
5. **显示 G2 门控**（用 `AskUserQuestion` 弹窗；无此工具则聊天内列编号）：
   - question（按交互语言）: "检索策略包已交付（范围卡 + 检索式 + 候选清单 + 使用说明）。确认完成流水线，还是需要调整？"
   - options: 「确认完成」/「需要调整」
6. **用户确认后（G2 通过）**：输出完成总结，流水线结束。

> ⚠️ **收割 ≠ 语料（铁律）**：候选清单是"待下载参考"，不是已核实的全文语料。下载哪些 PDF、是否纳入，完全由用户决定——AI 不替用户自动下载，也不替用户决定纳入。

## Output Format

### Literature Collection Report V1 (Inline)

**Retrieval Context**:
- Search Focus: Review articles (reviews, surveys, state-of-the-art papers)
- Time Span: [Start Year] – [End Year]
- Core Keywords: [summary of three tiers]

---

### Part A – Manual Database Queries

#### [Database Name 1]
**Query A — [Description]**:
`
[Full query text — never truncate]
`
**Query B — [Description]**:
`
[Full query text — never truncate]
`
*Usage: [usage notes]*

#### [Database Name 2]
... (repeat for all databases)

---

### Part B – API Harvested Literature

**Retrieval & Verification Statistics**:
| Metric | OpenAlex (Harvest) | Crossref (Verify) | Combined |
|:---|:---|:---|:---|
| Harvested | X | — | X |
| Verified | — | — | V |
| Unverified (no DOI) | — | — | U |
| Dropped (suspected hallucination) | — | — | D |

**Harvested Literature List**（仅列 verified + unverified；dropped 单独展示典型例子）:
| No. | Title | First Author | Year | DOI (clickable) | Verification | OA状态 |
|:---:|:---|:---|:---:|:---|:---|:---|
| 1 | [Full title] | [Author] | [Year] | [https://doi.org/...](https://doi.org/...) | [已验证] verified | OA期刊 (gold) / 非OA期刊 (closed) / 未知 |
| 2 | [Full title] | [Author] | [Year] | [https://doi.org/...](https://doi.org/...) | [待人工核验] unverified | OA期刊 (gold) / 非OA期刊 (closed) / 未知 |
| ... | ... | ... | ... | ... | ... | ... |

> **验证状态渲染规则（强制）：**
> - **verification 列**：`[已验证] verified`（Crossref 按 DOI 回查通过）/ `[待人工核验] unverified`（无 DOI 或验证瞬时失败，保留供人工参考）/ `[已剔除] dropped`（验证不通过，不进主表，另列典型例子）。最终文件禁止使用 Emoji 表示状态。
> - **DOI 必须是可点击的完整链接**：单元格写为 `[https://doi.org/<doi>](https://doi.org/<doi>)`（即在 DOI 前加 `https://doi.org/` 前缀），不要只写裸 `10.xxxx`。
> - **「OA状态」列**：值为 `OA期刊 (<oa_status>)`、`非OA期刊 (<oa_status>)` 或 `未知`。`is_oa` 与 `oa_status` 来自收割时 OpenAlex 原生附带的 `open_access` 字段，不再逐篇回查。
> - 在 Part B 统计区新增一行验证汇总：`验证通过：V 篇 / 无 DOI 待人工：U 篇 / 验证剔除：D 篇`。

---

### Summary Statistics
| Metric | Value |
|:---|---|
| Databases Covered (Search A) | [N] |
| API Engines Used (Search B) | 2 (OpenAlex harvest + Crossref verify; zero keys required) |
| Verified Results from API Harvesting | [N] |
| Total Search Effort | Manual queries: [N] databases + Automated: OpenAlex harvest + Crossref verification |

## Important Notes
- **CRITICAL**: Search B = **OpenAlex 收割 + Crossref 逐条验证**，零密钥，但联网前必须询问一次网络访问授权。不要询问任何 API Key / 访问池。用户拒绝时跳过 Search B，Search A 与交付继续。
- **CRITICAL**: 验证是去幻觉核心——Crossref 按 DOI 回查比对 title（相似度≥0.8）与 year（|Δ|≤1），不通过 → `dropped`（疑似幻觉/错配）；无 DOI → `unverified`。展示时用 `verified / unverified / dropped` 三态，绝不把 `dropped` 混进候选清单。
- **CRITICAL**: After Search A + Search B results are displayed (and Step 5 save is handled), the assistant MUST execute **Step 5.5: Deliver Search Strategy Pack**. This is the pipeline endpoint (G2). Do NOT load any downstream topic-selection module, do NOT ask the user for a PDF folder path, and do NOT offer to auto-download PDFs. Deliver the four-piece pack and stop at the G2 gate for user confirmation.
- **CRITICAL**: Part A (all queries) and Part B (all harvested literature) MUST be inline in chat, never summarized or file-only.
- **CRITICAL**: Do NOT save any file to disk until the user provides a save directory path in Step 5.
- This skill calls two sub-skills (Query Crafter and Literature Harvester) and merges their outputs. It does not directly generate queries or call APIs.
- The search focus for Search Strategist V1 is `review-priority` when the Step 0 writing type is 综述; adjust per writing type (论著查准 / 开题基金新颖性).
- The search strategy pack delivered at Step 5.5 (scope card + query pack + candidate list + usage guide) is the pipeline's final deliverable and the end of the QueryStrategist flow.
