---
name: search_strategist_v1
description: "检索策略师V1（第一轮检索） | 双通道并行：Search A调Query Crafter生成6平台手工检索式+Search B调Literature Harvester自动API收割（OpenAlex收割+Crossref逐条验证去幻觉，零密钥）。检索式+文献列表完整内联展示在聊天中，Step 5.5 收敛为检索策略包四件套（范围卡+检索式合集+候选清单+使用说明），G2 确认后主流水线结束。 Use this skill for first-round literature search strategy tasks within the QueryStrategist literature-search workflow. Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 1.22
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
This skill is part of the **QueryStrategist** workflow (V2.0, Step 2). It receives the Review Scope Confirmation Document from Scope Definer and performs the first round of literature retrieval, focusing primarily on **review articles**, delivering the search strategy pack as the pipeline's final output.

## Version
 V1.22

## Change Log
- **V1.22（2026-08-11 交付格式优化）**: 检索策略包 Markdown/CSV 统一 UTF-8 BOM；从同名 Markdown 自动生成离线 HTML 作为默认阅读入口；正文状态标记改为纯文本，检索式代码块禁止改写；新增编码、U+FFFD、代码块与 HTML 落盘校验。
- **V1.20（2026-08-10 OA 简化）**: OA 状态改为**收割时直接附带**（用户决策）——OpenAlex 收割响应原生携带 `open_access` 字段，`harvest.py`（V2.1）通过 `select=open_access` 一次请求同时拿到 `is_oa` / `oa_status`，**零额外 API 调用、零额外错误点**。历史版本的 `scripts/enrich_oa.py` 方案已废弃删除，不再有独立回查环节。
- **V1.19（2026-08-10 修复·防"Search B 没返回结果"复发）**: 新增 **Step 3.5「后台任务同步展示铁律（MANDATORY）」**——Search B 若为后台长任务，禁止在启动后立即结束回合；必须**等待任务完成 → 校验输出文件存在且 >0 → 在同一回合内内联展示 Part B 全量结果**（统计表 + 全部候选 + dropped 样例），否则用户会看到"没有返回结果"（本次真实事故）。新增「后台任务启动 → 等待完成 → 校验落盘 → 同步展示」四段式约束、任务未完成时的正确话术、以及`wc -c`/统计字段双校验。同时修复 Step 4 标题中残留的 `??` 乱码。
- **V1.18**: Search B 精简为两源（与 Literature Harvester V2.0 对齐，用户决策 2026-08-10）——(1) **Step 1.5 整段删除**：Semantic Scholar Key 询问、Scholar-KG 适用性判断与门控、Crossref 访问池询问、两份申请指南全部移除，改为「零密钥零弹窗」说明；(2) Step 1.4 预告表改为固定两行（OpenAlex 收割 + Crossref 验证）；(3) Step 3 参数精简为 `verify` + 可选 `mailto`；(4) Part B 输出与 JSON Schema 增加 `verified / unverified / dropped` 三态验证分层；(5) Summary Statistics 引擎数 2。
- **V1.17**: Part B 文献表新增 **「OA状态」列** + DOI 改为**可点击的完整 `https://doi.org/` 链接**（按用户需求）。OA 状态通过对每篇 DOI 回查 OpenAlex `open_access.is_oa` / `open_access.oa_status` 判定。新增可复用脚本 `scripts/enrich_oa.py`：生成报告前运行，自动把 `is_oa` / `oa_status` / `doi_link` 写回 metadata JSON。脚本 mailto 从参数/环境变量读取，不在发布包硬编码私人邮箱。
- **V1.16**: 新增 **Safe File Persistence** 硬规则（Step 5）——V1 报告（Part A 全检索式 + Part B 65+ 条）体量较大，禁止用 Bash heredoc 内联生成（会撞 ~1.5–2 KB 命令行上限导致 `unexpected EOF` 并陷入重试循环），也禁止 sandbox / 非 sandbox Bash 混用（导致 split-brain、静默产出 0 字节文件）。改为：用 Write 工具写一个小生成器 `.py` 读 `literature_collection_v1_metadata.json` 产出 `.md`，再 **单次** `dangerouslyDisableSandbox: true` Bash 执行；写后必须 `wc -c` 校验 > 0。此规则固化了一次实际运行卡死的根因修复。
- **V1.15**: 精简 Step 1.5 交互——(1) S2 弹窗申请教程压缩为 4 步骨架（去掉用途/Endpoints/每日请求量等细节）；(2) 把 Scholar-KG 适用性说明从弹窗 question 文案中移除，**改为放在弹窗前的叙述文字里**，并做成**条件式**（域适用则写"含 Scholar-KG"，域不适用则写"跳过 Scholar-KG"），强调不写死、需随领域变通；(3) 同步精简英文版弹窗文案。
- **V1.14**: Step 1.5 交互重构——(1) Step 1.4 预告表中 Crossref「是否需要 Key/池」列改为「可选池（Polite/Plus/Public）」；(2) 将 S2 Key 与 Crossref 访问池拆分为**两次独立 AskUserQuestion 弹窗**，且每个弹窗的 question 文本内嵌**简要申请教程/说明**，方便用户边看边申请。
- **V1.13**: 新增 **Step 1.4「Search B 引擎启用计划预告」**（MANDATORY，置于 Step 1.5 之前）——在询问任何 API Key / 访问池之前，先用表格向用户透明预告本轮 Search B 实际启用的引擎（OpenAlex 默认主干 / Crossref 池 / Semantic Scholar 是否低速 / Scholar-KG 是否跳过及原因）。解决"直接跳到 Key 询问、用户不清楚整体方案、逐源追问"的体验问题；预告后再进入 Step 1.5 的 Key / 池询问。
- **V1.11**: Step 1.5 修订——用户选择「提供某 Key」选项后，若回复中未携带 Key 字符串，必须【立即停止】并立即用纯文本提示用户粘贴 Key，**不得**先以无 Key 模式启动 Search A / Search B 占位运行。修正了"先跑无 Key 版本、之后再追问 Key"的错误流程——收到 Key 后才同时开始 Search A（检索式）与 Search B（API 收割）；仅当用户明确选「都不需要」时才以无 Key 模式立即跑 A+B。
- **V1.12**: Crossref 增补源接入 Search B 编排层——与 Literature Harvester V1.6 的 Crossref 固化（`query.bibliographic` 写死、默认源含 crossref）对齐。Step 1.5 新增独立 Crossref 访问池弹窗（polite 需真实 mailto / plus 付费 / public 匿名）；Step 3 将 `crossref_mode` / `mailto` / `plus_token` 透传给 Literature Harvester；Summary Statistics 引擎数 2→3；元数据 JSON `part_b_statistics` 增 `crossref_results`；Part B 检索统计表增 Crossref 列。
- **V1.9**: 删除 Step 5.5（G2）中英文版的 PDF 数量建议句（"预计需要准备 30–50 篇 PDF 即可满足选题挖掘需求" / "Approximately 30–50 PDFs should be sufficient for topic discovery"），不再对 PDF 篇数做预估暗示。
- **V1.10**: Step 5.5（G2）筛选建议强化「以综述为主」——明确文献应以 review/survey 类为主、占比过半用于搭框架；同时保留少量高被引原创研究作方法/实证支撑，避免全综述缺一手证据。中英文版同步。
- **V1.8**: 修正 Step 5.5（G2）PDF 下载交接提示——明确用户须**整合两条通道**（通道 A 手工检索式 Part A + 通道 B API 收割文献 Part B）检索到的全部文献，将二者筛选后下载的 PDF **统一放入同一文件夹**；不再把 Part B 仅当作"定位辅助"，并删除硬编码的"80 篇"数字，改为动态表述。强调下游只读取真实 PDF。
- **V1.6**: Added **No Phantom Actions** hard rule at Step 2 and Step 3 — "Invoke the Query Crafter / Literature Harvester sub-skill" is now an explicit TOOL-CALL DIRECTIVE. The assistant MUST issue the actual `Skill` tool call; it is forbidden from merely narrating "loading X" and ending the turn without the call. This fixes the failure mode where the prompt existed but the sub-skill was never actually loaded.
- **V1.7**: Reinforced the **"harvested ≠ corpus" principle** — harvested metadata (Search B) / surfaced papers (Search A) frequently contain fabricated/mismatched/misspelled entries (AI hallucination). V1 output is ONLY a candidate reference for the user to vet and decide downloads; the assistant MUST NOT feed harvested entries downstream as corpus. Added an IMPORTANT callout, aligned with orchestrator "Data Flow Principle".
- **V1.5**: Added **Step 5.5: PDF Download Handoff (MANDATORY)** — a standalone, mandatory gate between V1 and the downstream topic-selection module. This step blocks the assistant from loading that module until the user returns with a PDF folder path. (旧口径：Step 5.5 已随 V4.0 改为检索策略包交付，不再有 PDF 交接与下游模块加载。) Previously, the PDF download instruction was buried inside Step 5's "Next Steps" sub-section; when the user chose not to save files, the instruction was lost entirely, and the assistant would prematurely load the topic-selection module and ask "PDF vs metadata mode" — which is incorrect, because that module's standard workflow requires PDFs. Now the handoff is explicit, always-executes, and includes clear download instructions + estimated 30-50 PDF count.
- **V1.4**: When user selects "我去申请" / "Let me apply" in Step 1.5, immediately display a detailed **API Key Application Guide** with: (1) step-by-step instructions clarifying that the key is sent via email (not in a dashboard), (2) pre-filled templates for all form fields (usage description, endpoints, daily requests), (3) a low-speed fallback offer so the user can proceed without waiting. Previously the skill only said "wait until they return" with zero guidance, causing significant friction.
- **V1.3**: Step 1.5 API Key question MUST be presented via `AskUserQuestion` tool (interactive popup), NOT as plain text. Ensures consistent popup UX every time the skill is activated, without requiring user reminders.
- **V1.2**: Added Semantic Scholar API Key check (Step 1.5). Before executing Search B, the user is asked whether they have or want to apply for a free Semantic Scholar API key. The key status is passed to Literature Harvester, which adjusts its request rate accordingly (10 req/s with key vs 1 req/s without). Anti-rate-limiting strategies (429 backoff, request spacing, OpenAlex fallback) are now built into Literature Harvester V1.1.
- **V1.1**: Part A (all database queries) and Part B (all harvested literature entries) MUST be displayed inline in chat in full detail. Do NOT save output files before the user provides a folder path.
- **V1.1**: After inline display, ask user for save directory before writing any files to disk.

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
> - **Search B**: I will call **Literature Harvester** to harvest literature metadata from **OpenAlex** and **cross-verify each entry via Crossref by DOI** (filtering out hallucinated/mis-attributed entries — zero keys required).
>
> This first round focuses on **review articles** (reviews, surveys, state-of-the-art papers) to provide a comprehensive landscape for topic discovery in the next step. Both pathways will run simultaneously. Let me begin.""

### Step 1.4: 预告 Search B 引擎方案（MANDATORY，置于 Search B 启动前）

**设计原则**：在启动 Search B 之前，向用户**透明说明本轮 Search B 的引擎方案与验证策略**。用户先看到"整体方案"，再进入检索，避免任何"要不要 Key"的追问。

**执行**：根据《研究范围确认文档》+ 配置，生成一张「Search B 引擎方案」表，至少包含三列：引擎 / 状态 / 说明。固定为：

| 引擎 | 状态 | 说明 |
|:---|:---|:---|
| **OpenAlex** | ✅ 启用（收割主源） | 稳定主源，免费高并发，无需任何 Key |
| **Crossref** | ✅ 启用（验证器） | 按 DOI 逐条回查验证（title 相似度≥0.8 且 year 差≤1），剔除疑似幻觉/错配条目 |

展示后直接进入 Step 2 + Step 3 并行执行 Search A 与 Search B——**本轮 Search B 零密钥、零弹窗、零申请教程**（V2.0 起不再询问 Semantic Scholar Key / Crossref 访问池 / Scholar-KG，三者已从套件移除）。

### Step 1.5: （已移除 — V2.0 起零密钥零弹窗）

> 原 Step 1.5 的 Semantic Scholar Key 询问、Scholar-KG 适用性判断与门控、Crossref 访问池询问、两份申请指南，已随 Literature Harvester V2.0 整段删除。Search B 现仅用 OpenAlex（收割）+ Crossref（验证），均无需 Key。若用户主动询问"要不要 Key"，回答：本套件 Search B 已精简为两源开放 API，无需任何 Key。

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
**⚠️ CRITICAL (No Phantom Actions):** "invoke the Literature Harvester sub-skill" is a TOOL-CALL DIRECTIVE. You MUST issue the `Skill` tool call for `literature_harvester` in this turn — do NOT merely write "先加载 Literature Harvester 子技能…" and stop. Simultaneously with Step 2, invoke the **Literature Harvester** sub-skill with the following parameters:
- `species_terms`：对象层词列表，对应 `--species`
- `tech_terms`：必需技术锚点词列表，对应 `--technology`
- `task_terms`：任务/应用层词列表，对应 `--task`
- `exclude_terms`：排除词列表，对应 `--exclude`；无排除项则传空列表
- Literature time span as `min_year` / `max_year`
- Writing type and derived search focus
- Results limit: 20–25 per sub-query
- `verify`: `True` (default) — Crossref 逐条验证开启
- `mailto`: optional real email for Crossref polite pool (10 req/s); empty → anonymous public pool (5 req/s)

**三层参数传递硬规则：** 当 Scope Document 提供三层词时，每个子查询必须调用 `harvest.py --query <trace-query> --species <对象词...> --technology <技术词...> --task <任务词...> [--exclude <排除词...>]`。不得只传普通 `--query`，否则不会启用 OpenAlex 三层强制共现过滤。

Literature Harvester will:
- Harvest candidate metadata from **OpenAlex** (the sole harvest source)
- **Cross-verify each entry via Crossref by DOI** (title similarity ≥0.8, year delta ≤1) — V2.0 verification layer
- Split results into `verified` / `unverified` / `dropped` (suspected hallucination/mis-attribution)
- Compile a unified verified-candidate literature list

Receive the compiled harvesting + verification report from Literature Harvester.

### Step 3.5: 后台任务同步展示铁律（MANDATORY — 防"Search B 没返回结果"）

**⚠️ CRITICAL (V1.19 — 由真实事故固化):** 若 Search B（收割+验证）作为**后台任务**运行，本步骤是**硬性约束**——禁止在启动 Search B 后立即结束回合并抛下一句"正在后台运行，稍后展示"。那会导致用户界面长时间只看到"没有返回结果"（本次实际发生：任务 1m39s 完成、结果完整，但上一回合只写了"正在后台运行"，用户误以为失败）。

**四段式约束（缺一不可）**：

1. **启动**：发起后台任务（`run_in_background: true`）时，仅在聊天中提示"Search B 正在后台运行"。
2. **等待完成**：**必须**等待后台任务完成（通过任务通知 / `TaskOutput` 阻塞轮询），**不得**在启动后立即结束回合。
3. **校验落盘**：任务完成后，**先校验输出文件存在且内容有效**——
   - `wc -c <harvest.json>` 确认文件字节数 > 0；
   - 读取 JSON 校验 `statistics` 字段（harvested / verified / unverified / dropped 计数）与 `verified` / `dropped` 数组实际长度一致。
   - 校验失败（0 字节 / 字段缺失 / 计数不符）→ 如实报告错误并按「Error Handling」提供 Retry / Skip / Abort，**不得**假装成功。
4. **同步展示**：校验通过后，**在同一回合内**把 Part B 全量结果内联展示在聊天中（统计表 + 全部候选条目 + dropped 典型样例 + 验证汇总），**不得**以"已写入文件""稍后展示"等话术跳过展示。展示完毕后才进入 Step 4/5。

**正确话术（任务仍在跑、但本回合必须结束时——仅此一种合法情况）**：说明"Search B 正在后台运行，预计 X 分钟，**完成后我会在本轮立即展示 Part B 全量结果**，请稍候"。其余情况一律按四段式执行，不得提前结束回合。

> 关联：Step 4 的「?? CRITICAL OUTPUT RULE (V1.1)」要求所有结果内联展示、不截断、不写文件——本条是其**执行前置**：先等任务完成，再展示。

### Step 4: Display Full Results Inline in Chat (DO NOT SAVE YET)

**⚠️ CRITICAL OUTPUT RULE (V1.1):** 
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
Display:
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

**⚠️ Safe File Persistence (V1.16 — CRITICAL, prevents the empty-report hang):**
The V1 report Markdown is large (Part A full queries + Part B 65+ entries). Persisting it via a Bash heredoc is fragile and was the root cause of a previous multi-minute non-completion. Follow the orchestrator's **Hard Rule — Bash Sandbox Consistency & Safe File Persistence**:
- **Do NOT embed the report text in a Bash heredoc** (`cat <<'EOF'` / `python <<'PYEOF'`). The command hits the Bash length cap (~1.5–2 KB) and gets truncated → `unexpected EOF` parse error; retrying the same pattern loops forever.
- **Do NOT mix sandbox and non-sandbox Bash.** A `cat > file` under a normal (sandboxed) Bash call writes to a throwaway FS layer, invisible to a later `dangerouslyDisableSandbox` Bash call or to Read/Write tools → silently produces a 0-byte file.
- **Correct pattern:** Write a small generator script (e.g. `gen_report.py`) via the **Write tool** (no length cap), reading `literature_collection_v1_metadata.json` and emitting the `.md`. Then run it in **ONE** `dangerouslyDisableSandbox: true` Bash call. This sidesteps both bugs at once.
- **Verify after write:** Immediately `wc -c literature_collection_report_v1.md` and confirm > 0. If 0 bytes, the write failed — do not proceed silently. (The same applies to the metadata JSON.)

**OA 状态获取（V1.20 — 收割时直接附带，无需回查）：**
OpenAlex 收割响应**原生携带** `open_access` 字段（`is_oa` / `oa_status`，取值 open/gold/green/hybrid/bronze/closed）。`harvest.py`（V2.1）已通过 `select=open_access` 在收割时一次性附带，**每条记录自带 `is_oa` / `oa_status`，零额外 API 调用、零额外错误点**。
- 原 V1.17 的 `scripts/enrich_oa.py` 逐篇回查方案**已废弃删除**（V1.20）：不再按 DOI 回查 OpenAlex open_access，不再有回查脚本、回查字段与相关容错分支。
- 渲染规则不变：DOI 列 = `[https://doi.org/<doi>](https://doi.org/<doi>)`；OA状态列 = `OA期刊 (<oa_status>)` 当 `is_oa` 为 true，否则 `非OA期刊 (<oa_status>)`，缺失时为 `未知`。在 Part B 统计区加按来源的 OA 汇总。

**Literature Collection V1 Metadata JSON Schema** (save alongside the .md report):

```json
{
  "report_version": "V1.4",
  "saved_at": "ISO-8601 datetime",
  "retrieval_context": {
    "search_focus": "review-priority",
  "time_span": {"start": YYYY, "end": YYYY},
  "writing_type": "综述",
    "core_keywords": {"tier1_species": [...], "tier2_technology": [...], "tier3_application": [...]}
  },
  "part_a_databases": ["WoS", "Scopus", "IEEE", "Google Scholar", "CNKI", "Wanfang"],
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
      "doi_link": "https://doi.org/10.xxx/...",   // V1.17: full clickable link
      "is_oa": true,                               // V1.19: 收割时 OpenAlex 原生附带（原 V1.17 回查方案已废弃）
      "oa_status": "gold",                         // V1.19: open/gold/green/hybrid/bronze/closed/未知
      "verification": "verified | unverified | dropped",   // V2.0: Crossref 逐条验证状态
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
**CRITICAL (V4.0): Search Strategist V1 是 QueryStrategist 主流水线（Step 0–2）的终点。Step 5 保存文献采集报告后，立即进入本步，把结果收敛为检索策略包四项逻辑交付物（范围卡 + 6 库检索式合集 + 文献候选清单 + 使用说明）。每份 Markdown 同步生成离线 HTML，CSV/Markdown 使用 UTF-8 BOM；HTML 是默认阅读入口。然后停在 G2 决策门等用户确认。本步不加载任何下游综述选题模块，不询问 PDF 文件夹路径，不替用户下载 PDF。**

**为什么有本步：** 检索策略包是主流水线的最终交付物——AI 把"检索策略"（范围卡 + 检索式 + 候选清单 + 使用说明）做对做好，下载 PDF 与写作是用户自己的事。模板见 `assets/search_strategy_pack_template.md`；所有字段标注上游出处（【继承自 Step 0/1/2】），禁止凭空生成。

**执行流程：**
1. **读取上游产物**：Step 0 `project_meta.json`（写作类型 / 目标语言 / 目标期刊 / 时间跨度）、Step 1 `scope_definition.md`（三级关键词 + 排除项 + 优先级）、Step 5 保存的 `literature_collection_report_v1.md` + `literature_collection_v1_metadata.json`。
2. **按模板落盘四项逻辑交付物**（到 Step 5 用户指定的目录）：
   - `scope_card.md`：写作类型与策略权重、三级关键词、排除项、优先级、G0–G1 确认记录；
   - `query_pack.md`：Part A 的已启用平台检索式合集。每条检索式必须放入独立 fenced code block，禁止放进 Markdown 表格；
   - `candidate_list.csv/.md`：Part B 收割的全量候选文献。表格单元格中的 `|` 必须写成 `\|`；
   - `usage_guide.md`：平台填入位置、筛选下载方法和写作类型策略权重。
3. **规范编码并生成 HTML（MANDATORY）**：运行 `python <QueryStrategist包根>/_shared_tools/scripts/render_deliverables.py --directory <交付目录>`。脚本只替换正文中的易乱码展示符号，不改写 fenced code block 中的检索式；同时生成 `scope_card.html`、`query_pack.html`、`candidate_list.html`、`usage_guide.html`，并给 Markdown/CSV 写入 UTF-8 BOM。
4. **写后校验（缺一不可）**：确认所有 `.md/.csv/.html` 文件存在且字节数大于 0；Markdown/CSV 前 3 字节为 `EF BB BF`；所有文本可严格按 UTF-8 解码且不含 U+FFFD（`�`）；HTML 含 `<meta charset="utf-8">`；`query_pack.md` 与 `query_pack.html` 中的每条检索式逐字一致。任一校验失败均不得进入 G2。
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

> **V2.0 — 验证状态渲染规则（强制）：**
> - **verification 列**：`[已验证] verified`（Crossref 按 DOI 回查通过）/ `[待人工核验] unverified`（无 DOI 或验证瞬时失败，保留供人工参考）/ `[已剔除] dropped`（验证不通过，不进主表，另列典型例子）。最终文件禁止使用 Emoji 表示状态。
> - **V1.17 — DOI 必须是可点击的完整链接**：单元格写为 `[https://doi.org/<doi>](https://doi.org/<doi>)`（即在 DOI 前加 `https://doi.org/` 前缀），不要只写裸 `10.xxxx`。
> - **V1.20 — 「OA状态」列**：值为 `OA期刊 (<oa_status>)`、`非OA期刊 (<oa_status>)` 或 `未知`。`is_oa` 与 `oa_status` 来自收割时 OpenAlex 原生附带的 `open_access` 字段（V1.20 起不再逐篇回查）。
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
- **V2.0 CRITICAL**: Search B = **OpenAlex 收割 + Crossref 逐条验证**，零密钥零弹窗。Semantic Scholar / Scholar-KG 及其 Key 询问、申请指南、门控规则已整段删除。不要向用户询问任何 API Key / 访问池。
- **V2.0 CRITICAL**: 验证是去幻觉核心——Crossref 按 DOI 回查比对 title（相似度≥0.8）与 year（|Δ|≤1），不通过 → `dropped`（疑似幻觉/错配）；无 DOI → `unverified`。展示时用 `verified / unverified / dropped` 三态，绝不把 `dropped` 混进候选清单。
- **V4.0 CRITICAL**: After Search A + Search B results are displayed (and Step 5 save is handled), the assistant MUST execute **Step 5.5: Deliver Search Strategy Pack**. This is the pipeline endpoint (G2). Do NOT load any downstream topic-selection module (removed in V4.0, not part of this suite), do NOT ask the user for a PDF folder path, do NOT offer to auto-download PDFs. Deliver the four-piece pack and stop at the G2 gate for user confirmation.
- **V1.1 CRITICAL**: Part A (all queries) and Part B (all harvested literature) MUST be inline in chat, never summarized or file-only.
- **V1.1 CRITICAL**: Do NOT save any file to disk until the user provides a save directory path in Step 5.
- This skill calls two sub-skills (Query Crafter and Literature Harvester) and merges their outputs. It does not directly generate queries or call APIs.
- The search focus for Search Strategist V1 is `review-priority` when the Step 0 writing type is 综述; adjust per writing type (论著查准 / 开题基金新颖性).
- The search strategy pack delivered at Step 5.5 (scope card + query pack + candidate list + usage guide) is the pipeline's final deliverable and the end of the QueryStrategist flow.
