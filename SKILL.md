---
name: querystrategist
description: "QueryStrategist 单包主 Skill（Step 0–2）| 基于 LLM 的交互式文献检索系统，通过结构化提问把模糊科研意图转化为高精度专业检索策略。面向综述、研究论著、学位论文、开题报告、基金申请、调研报告等各类文献写作场景。终点交付检索策略包（范围卡 + 6 库检索式 + 文献候选清单 + 使用说明）。本包为 Skill 集合：1 个主 Skill（本文件）+ 11 个子模块（目录内 SKILL.sub.md）。 Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 4.3.1
  keywords: [literature search, query strategy, retrieval, human-in-the-loop, QueryStrategist]
  triggers: [文献检索, 检索策略, 建检索式, QueryStrategist, start querystrategist]
---

# QueryStrategist — 主 Skill（Step 0–2 完整流水线）

本文件是 **QueryStrategist** 的主 Skill（唯一入口），承担编排器职责：驱动 **Step 0–2 状态机**（Setup Wizard → Scope Definer → Search Strategist V1），在每个决策门（G0–G2）暂停等待人工确认，最终交付**检索策略包**（范围卡 + 6 库检索式 + 文献候选清单 + 使用说明）。

本包内还包含 **11 个子模块目录**（`setup_wizard/`、`scope_definer/`、`search_strategist_v1/`、`query_crafter/`、6 个平台检索器、`literature_harvester/`）。子模块指令文件有两种形态：**SCP 单包形态**为 `SKILL.sub.md`（上架文件名），**本地独立安装形态**为 `SKILL.md`（下载解压改回后可被注册为独立 Skill）。主 Skill 按"子模块执行机制"读取并执行它们（两种文件名均支持）。

---

## Version
QueryStrategist 单包版（Step 0–2）— 2026-08-11 检索策略版

## Change Log
- **V4.3.1 (2026-08-11)**: 修复 IEEE Xplore Command Search 生成器：移除无效的 `"Field":(A OR B)`，增加 25-term 自动拆分、All Metadata 宽泛式、逐项字段限定、NEAR/ONEAR 与回归测试。
- **V4.3.0 (2026-08-10)**: 落实发布复盘 P0/P1：Search B 增加真实 API 配额守卫与 dry-run；统一 6 平台口径并补齐 Wanfang；标准化写作类型/年份配置透传；修复共享校验器 Windows 编码失败；清理演示材料中的已移除引擎描述。
- **V4.2 (2026-08-09)**: 触发方式新增「演示模式提示」——为录屏/评审演示，入口统一用「开始文献检索」+ 全程固定话术（Setup Wizard Step 0.6），保证输出逐字一致、可复现。
- **V4.1 (2026-08-09)**: 从"套件总入口（11 个独立子 Skill）"升级为"**单包主 Skill**"（Skills 广场上架形态）：编排器全部逻辑合并进根 SKILL.md；11 个子 Skill 指令文件改为 `SKILL.sub.md`（子模块形态）；新增"子模块执行机制"（读 `SKILL.sub.md` 内联执行，禁止幽灵动作）。
- **V4.0 (2026-08-09)**: 从 AI for Review（Step 0–3 综述套件）精简为 QueryStrategist（Step 0–2 检索策略生成器）。移除综述选题模块（Step 3 及全部相关资产）；终点产出改为「检索策略包（范围卡 + 6 库检索式 + 文献候选清单 + 使用说明）」；决策门收缩为 G0–G2；Setup Wizard 的"综述类型"扩展为"写作类型"并按类型调检索策略权重。（旧口径，已被 V4.1 取代）
- **V3.0 (2026-07-31)**: 精简为 Step 0–3，移除 Step 4–8。（旧口径，仅存于变更记录）
- **This release**: A self-contained human-in-the-loop pipeline covering Steps 0–2 — from project configuration and scope definition, through dual-channel retrieval, to search strategy pack delivery. Mandatory confirmation gates (G0–G2) keep the human in control at every decision point. The deliverable is a search strategy pack (scope card + multi-platform queries + candidate list + usage guide).

---

## 子模块执行机制（MANDATORY — 禁止幽灵动作）

**本主 Skill 是唯一入口，11 个子模块（`<module>/SKILL.sub.md` 或本地形态 `<module>/SKILL.md`）不是独立 Skill，不会被平台注册**。因此任何"调用子能力"的步骤都是**执行指令**，必须真实执行，执行通道按优先级：

1. **(a) 平台 Skill 工具调用** — 若运行环境中存在已注册的同名独立 Skill（如用户本地安装了子 Skill），可先尝试 `Skill` 工具调用。
2. **(b) 读取执行（单包默认通道）** — 读取对应子模块的指令文件（优先 `SKILL.sub.md`；不存在则读 `SKILL.md`），按其指令**真实执行**：运行其 `scripts/` 脚本、遵循其门控、产出其交付物。**读取并执行才算执行**；仅写一句"加载 X 子技能"就结束回合 = 幽灵动作，严格禁止。
3. **(c) Agent 委派** — 若环境提供子代理/队友机制，可将子模块委派给 agent 并等待其返回。

**自检**：任何回合结束前，对自己描述的每个"已完成/进行中"动作，确认有匹配的真实执行（工具调用 / agent 返回 / 已按子模块指令运行脚本产出文件）。若写了"加载 X"却三种通道都没有执行，立即补齐后再回复。

> 兼容提示：下载本包解压后，若用户希望子能力恢复为独立 Skill，把任意 `<module>/SKILL.sub.md` 改回 `SKILL.md` 即可。主 Skill 优先走 (a) 通道调用已注册的独立 Skill，未注册则自动回退 (b) 读取执行——两种形态均可用。

---

## 触发方式

- **完整流水线**：对任意支持 Skill 的 Agent 说「**开始文献检索**」或「**Start QueryStrategist**」，即进入本主 Skill 驱动的 Step 0–2 状态机。
- **直接给方向**：「**开始文献检索，我的研究方向是：[topic]**」——主 Skill 将方向预填给 Step 0 与 Step 1，不再要求用户复述。
- **单步使用**：若用户只想用某个子能力（如只生成某库检索式），主 Skill 按子模块执行机制读取对应子模块指令文件并执行其逻辑（不要求走完整流水线）。

> **演示模式提示**：为录屏/评审演示，入口请统一使用「**开始文献检索**」，全程使用固定话术（见 `setup_wizard` 子模块的 **Step 0.6 固定话术脚本**），保证每次运行的输出逐字一致、可复现。

## 包内子模块一览

| 子模块目录 | 流程定位 | 功能 |
|---|---|---|
| `setup_wizard` | Step 0 | 写作类型 + 目标语言/期刊 + 时间跨度配置 |
| `scope_definer` | Step 1 | 范围界定（三级关键词 + 排除项 + 优先级） |
| `search_strategist_v1` | Step 2（终点） | 双通道检索：Search A 检索式 + Search B API 收割 → 交付检索策略包 |
| `query_crafter` | 子模块 | 6 平台检索式总控 |
| `wos_query_crafter` / `scopus_query_crafter` / `ieee_query_crafter` / `google_scholar_query_crafter` / `cnki_query_crafter` / `wanfang_query_crafter` | 子模块 | 各平台高级检索式构建器 |
| `literature_harvester` | 子模块 | 两源 API 收割 + 验证（OpenAlex 收割 + Crossref 按 DOI 逐条验证去幻觉） |

---

## 流水线终点：检索策略包

G2 确认后，自动产出四份相互衔接的文件（模板见 `search_strategist_v1/assets/search_strategy_pack_template.md`）：

1. **`scope_card.md`** — 范围界定卡（三级关键词 + 排除项 + 写作类型 + 策略权重）；
2. **`query_pack.md`** — 多平台检索式合集（6 库，每库查全式 A + 查准式 B）；
3. **`candidate_list.csv` / `.md`** — 文献候选清单（去重元数据 + OA 状态 + DOI 链接，标注"候选清单、非最终语料"）；
4. **`usage_guide.md`** — 使用说明（检索式填入位置 + 命中量级预估 + 调宽/调窄方法 + 按写作类型建议）。

所有字段继承 Step 0–2 上游选择（`【继承自 …】` 标注），禁止凭空生成。

---

## 核心红线

- **收割 ≠ 语料**：API 收割的元数据仅作候选清单，绝不自动进入下游当作全文语料，需用户自行下载验证。
- **人机闸门**：G0–G2 为强制人工确认点，范围与检索策略确认始终由人类决定。
- **语言锁**：回复语言严格跟随用户当前消息语言；检索式与候选清单的语言由 Step 0 目标期刊决定。

---

## Response Language Rule (Mandatory — Hard Language Lock)

**Language Lock:** The reply language is strictly bound to the language the user is writing in their *current* message. No other criterion applies. This is a hard constraint that overrides any default model tendency or system hint. **ALL natural languages are supported** — not only Chinese and English.

- **Default from Step 0:** Setup Wizard (Step 0) detects the user's first-message language and records it as `interaction_language` (ISO 639-1 code) in the Project Configuration Profile. This value is the **default interaction language** passed to every sub-module, ensuring sub-modules that do not directly see the user's latest message still reply in the correct language.
- **Detect per message, not just at entry:** For EVERY user message, detect its language and reply in *exactly that language*. Do NOT base the reply language on the entry command alone — if the user switches languages mid-conversation, the reply language switches with them. The Step 0 `interaction_language` is the default; the per-message detection is the active enforcer.
- **Any language → same-language reply:** When the user writes in any language (Chinese, English, Japanese, French, German, Korean, Spanish, Russian, Arabic, Portuguese, etc.), ALL output — greetings, configuration prompts, scope questions, status displays, decision-gate confirmations, completion messages — MUST be in that same language. Brand names / technical terms may stay in their original form; the explanatory prose MUST match the user's language.
- **Mixed input:** If a single message mixes languages, follow the *dominant* (majority) language of that message.
- **NEVER switch unprompted:** Under no circumstances reply in a language the user did not use in their latest message (e.g., never answer a Chinese message in Japanese or English, and never answer an English message in Chinese). If unsure of the language, default to matching the most recent user message, or fall back to the Step 0 `interaction_language`.
- **Sub-module binding:** This lock binds every delegated sub-module. When the main Skill invokes a sub-module, it MUST explicitly instruct that sub-module to reply in the locked language (passing the `interaction_language` value from the config profile). Sub-modules must not introduce a different language.
- **Low-resource languages:** For the ~30–40 major world languages, language following is highly reliable. For very low-resource languages, if the model occasionally slips, default to the Step 0 `interaction_language` and inform the user they may switch to a major language if they prefer.

This rule takes priority over any conflicting language preference in downstream modules or system defaults.

---

## Hard Rule — No Phantom Actions (禁止幽灵动作)

**This is a MANDATORY, non-negotiable rule, on par with the Language Lock above.**

**The problem it prevents:** A workflow step says "invoke / call / load / execute / delegate to the X sub-module", but the assistant only *writes* that sentence (often ending with a colon, e.g. "先加载 X 子模块以获取…") and then ends the turn — **without ever actually executing the sub-module's logic** (no tool call, no script run, no inline execution). The instruction exists, the action does not. This is a "phantom action" and is a critical failure.

**The binding rule:**
1. Any instruction in this SKILL that reads "invoke / call / load / execute / delegate to a sub-module" is an **EXECUTION DIRECTIVE**, not narration. When you reach such a step, you MUST actually run the sub-module's logic through whichever channel your environment provides, in this order of preference:
   - (a) **`Skill` tool call** — if the platform exposes a Skill tool and the sub-module is installed as an independent Skill (e.g. `Skill: "literature_harvester"`), emit the real call.
   - (b) **Read-and-execute** — if the sub-module is not an independent Skill (single-package form), READ its `SKILL.sub.md` (and any `scripts/` helpers it references) and EXECUTE its instructions inline: run its scripts, follow its gates, produce its artifacts. Importing the module's content as context and acting on it counts as execution; merely narrating that you will do it does not.
   - (c) **Agent delegation** — if a sub-agent / teammate mechanism is available, delegate the sub-module to an agent and wait for its result.
   Do not describe it; do it.
2. **You are strictly forbidden** from writing a transitional sentence about loading/calling a sub-module and then ending the turn without the actual tool call. Examples of forbidden behavior:
   - ❌ "先加载 Literature Harvester 子模块以获取收割脚本与参数规范：" → [turn ends, no call]
   - ❌ "Now invoking Query Crafter…" → [turn ends, no call]
3. **Self-check before ending ANY turn:** For every action you described as done or in-progress, verify a matching execution actually happened (a `Skill` call, an agent delegation that returned, or an inline run of the sub-module's instructions/scripts). If you wrote "loading X" but executed none of the three channels above, you have a phantom action — fix it NOW by executing it before replying.
4. **If you genuinely must wait for user input** (e.g., a decision gate, an AskUserQuestion), do NOT narrate a sub-module load you have not made. Instead state what the NEXT step will be after the user responds (e.g., "下一步将读取 Literature Harvester 的 SKILL.sub.md 执行 Search B"). The narration must reflect reality.
5. This rule binds every delegated sub-module call across Steps 0–2, including search_strategist_v1 → (Query Crafter, Literature Harvester) and query_crafter → (platform Query Crafters) delegations.

---

## Hard Rule — Project Isolation (项目隔离)

**This is a MANDATORY, non-negotiable rule, on par with the Language Lock and No Phantom Actions above.**

**The problem it prevents:** A pipeline run begins by selecting/creating a project in Step 0 (Setup Wizard's Project Workspace Gate). Without an isolation rule, the agent may accidentally read, modify, or borrow files from a *different* project's folder (`projects/<other_id>/`), corrupting one project with another's data, or leaking a past project into a "fresh start".

**The binding rule:**
1. **Step 0 sets the active project.** After the user chooses "继续 <项目>" or "新建项目", the active project is fixed for the rest of the session and recorded in `active_project_dir` (Pipeline Context) + workspace-root `active_project.json`.
2. **All file reads/writes are confined to `active_project_dir`.** Every downstream module (Steps 1–2) MUST resolve paths relative to `projects/<active_id>/` — its `pipeline_state/`, `Step2*/`, `config.json`, and `.workbuddy/memory/`. The agent MUST NOT read, write, move, copy, or otherwise reference any `projects/<other_id>/`.
3. **"新建项目" severs access to prior projects.** Once the user picks a fresh project, the previous project's workspace is effectively disconnected for the remainder of the session. The agent MUST treat `projects/<other_id>/` as non-existent — it must not peek at old configs, PDFs, reports, or memory to "help" the new project.
4. **Memory is isolated too.** The workspace-root `.workbuddy/memory/` is the live mirror of the ACTIVE project only (restored at Step 0). The agent MUST NOT read another project's `.workbuddy/memory/`; it must not write cross-project notes. Switching projects at Step 0 archives/restores memory per the Setup Wizard's "记忆隔离" procedure.
5. **Self-check before any file operation:** Before reading or writing any path, verify it is under `projects/<active_id>/`. If a tool call targets `projects/<other_id>/` (or the workspace root outside `active_project_dir`), STOP — it is a violation of this rule.
6. This rule binds every sub-module call across Steps 0–2.

---

## Hard Rule — No Long-Term Memory Borrowing (禁止借用长期记忆/跨项目背景)

**This is a MANDATORY, non-negotiable rule, on par with the Language Lock, No Phantom Actions, and Project Isolation above.**

**The problem it prevents:** At pipeline activation, the assistant uses the user's long-term / cross-project memory (e.g., a past research direction, target journal, or review topic from previous projects) to pre-fill configuration options or scope questions — even though the current workspace may have no project and the user expects a fresh start. This contaminates a new project with stale context and violates the "fresh start" expectation.

**The binding rule:**
1. **At activation, consult ONLY the workspace.** When the pipeline starts (Step 0 / Step 0.5), the ONLY sources of context are: (a) the current workspace's `projects/` directory (existing QueryStrategist projects) and (b) the user's explicit input in the current session (entry command, answers to configuration questions, direction sentence).
2. **NEVER pre-fill from long-term memory.** The assistant MUST NOT use the user's long-term research background, past project topics, target journals, or any cross-project memory to pre-fill configuration options, to hint at scope directions, or to "help" the user describe their research direction. No "基于你的长期研究背景，我已预填…" type of behavior.
3. **Fresh workspace = fresh start.** If `projects/` is empty (or contains no real project), treat the session as a brand-new project: ask the user for all configuration dimensions (Step 0) and the direction sentence (Step 1) from scratch, with no borrowed defaults.
4. **Scope questions come from the user.** In Scope Definer, the direction sentence and all substantive scope dimensions must come from the user's current-session answers — never inferred from long-term memory and merely presented for rubber-stamping.
5. This rule binds every sub-module call across Steps 0–2.

---

## Hard Rule — Bash Sandbox Consistency & Safe File Persistence

**This is a MANDATORY operational guard, on par with the Language Lock, No Phantom Actions, and Project Isolation above. It is the global fix for the "run hangs / deliverable file ends up empty" failure mode observed in real runs.**

**The two failure modes it prevents:**

1. **Sandbox / real-FS split-brain.** Bash runs sandboxed by default. A file written by a *normal (sandboxed)* Bash call (`cat > file`, `python -c "open('file','w')"`) lands in a **throwaway sandbox FS layer** that is invisible to: (a) a later `dangerouslyDisableSandbox: true` Bash call, and (b) the Read / Write / Edit tools (which always use the **real** FS). The result is a "successful" write no other command or tool can see → silently produces a missing or **0-byte** file. The sibling file that *was* written via a non-sandboxed call survives, while the sandboxed one vanishes — a classic split-brain.
2. **Bash command-length cap (~1.5–2 KB).** Embedding multi-KB content (a long markdown report, large JSON, or a big inline Python block) inside a Bash heredoc (`cat <<'EOF'` / `python <<'PYEOF'`) causes the command to be **truncated mid-stream** — the closing delimiter is never sent → shell error `unexpected EOF while looking for matching ''`. The agent tends to *retry the same failing pattern*, which looks like "running a long time without completing" but is actually doing no useful work.

**The binding rule:**
1. **Be consistent about the sandbox.** For ANY Bash command that reads/writes files under the workspace (`projects/<id>/`, or the workspace root), use `dangerouslyDisableSandbox: true` **every time**. Never mix sandboxed and non-sandboxed Bash in the same task. Preferred alternative: use the **Read / Write / Edit tools** for file I/O (they always hit the real FS and have no length cap), and reserve Bash for pure compute / external commands.
2. **Never inline multi-KB content in Bash.** If you need to generate a large file (report, JSON, code), **write a generator script via the Write tool** (no length cap), then run it with a short Bash command (`python gen.py`). Keep inline Bash commands < 1.5 KB; if unavoidable, split with `cat >>` chunks or a temp file.
3. **Write-then-verify.** After any step that writes a deliverable, immediately verify the file exists with **byte size > 0** (e.g. `wc -c file`). A 0-byte file is the signature of the two bugs above — never assume a write succeeded; never proceed silently past an empty output.
4. This rule binds every sub-module call across Steps 0–2.

---

## Entry Command
The user initiates the pipeline with:

> ""Start QueryStrategist.""
> ""开始文献检索""
> ""启动检索策略""
> ""建检索式""

**Step 0 启动行为（重要）**：入口指令触发后，主 Skill 第一步读取 `setup_wizard/SKILL.sub.md` 并执行（Step 0）。Step 0 配置写作类型（综述/研究论著/学位论文/开题报告/基金申请/调研报告/自定义）、目标语言、目标期刊、时间跨度、中文补充等。详见 Setup Wizard 子模块。

Alternatively, the user can specify a research direction directly:

> ""Start QueryStrategist. My research direction is: [topic]""
> ""开始文献检索，我的研究方向是：[topic]""

## Workflow

### State Machine Definition
The main Skill maintains an internal state that tracks:
- **Current Step**: Which module is active (0–2).
- **Step Status**: `pending`, `in_progress`, `awaiting_confirmation`, `completed`, `skipped`, `failed`.
- **User Context**: All confirmed outputs from previous steps (configuration profile, scope document, folder paths, confirmed topic).

### Sequential Execution Logic
For each step, the main Skill:
1. **Check preconditions**: Ensure all required inputs from previous steps are available.
2. **Invoke the sub-module**: Read the corresponding `SKILL.sub.md`, pass the relevant context, and execute its defined workflow (or call the registered independent Skill if installed — see 子模块执行机制).
3. **Present output**: Display the sub-module's output to the user in a clear, summarized format.
4. **Pause for confirmation**: At every decision gate, stop and wait for the user's explicit response. Do not proceed until the user confirms.
5. **Record state**: Mark the step as `completed` and log the outputs for downstream use.

### Decision Gates (Mandatory Pause Points)
The main Skill MUST pause and wait for user confirmation at the following gates (G0–G2). Confirmation prompts are given in the user's **interaction language** (detected in Step 0 and locked per the Hard Language Lock). The table below shows English and Chinese reference versions; use the one matching the user's language (or translate the prompt into any other language the user is writing in):

| Gate | After Step | English Prompt | Chinese Prompt |
|:---|:---|:---|:---|
| G0 | Setup Wizard (Step 0) | "Configuration confirmed. Proceed to Scope Definer?" | "配置已确认。是否继续进入范围界定（Scope Definer）？" |
| G1 | Scope Definer (Step 1) | "Scope confirmed. Proceed to Search Strategist V1?" | "范围已确认。是否继续进入检索策略（Search Strategist V1）？" |
| G2 | Search Strategist V1 (Step 2) | "Search strategy pack delivered (scope card + queries + candidate list + usage guide). Confirm to complete the pipeline, or request adjustments?" | "检索策略包已交付（范围卡 + 检索式 + 候选清单 + 使用说明）。确认完成流水线，还是需要调整？" |

### Pipeline Step Map (0–2)

| Step | Sub-Module | Required Input from Previous | Status |
|:---|:---|:---|:---:|
| 0 | Setup Wizard | None (entry point) | ✅ 已实现 |
| 1 | Scope Definer | Configuration Profile | ✅ 已实现 |
| 2 | Search Strategist V1 | Scope Document | ✅ 已实现 |

> **终点（Step 2 完成后）**：Search Strategist V1 交付**检索策略包**作为最终交付物：`scope_card.md`（范围卡）+ `query_pack.md`（6 库检索式合集，每库查全式 A + 查准式 B）+ `candidate_list.csv/.md`（文献候选清单）+ `usage_guide.md`（使用说明）。用户在 G2 确认后流水线结束。

### Error Handling
If a sub-module encounters an error or cannot complete:
1. **Log the error**: Record which step failed and any available error details.
2. **Notify the user**: Present the error clearly and offer three options:
   - `Retry`: Re-run the current step.
   - `Skip`: Skip this step and continue (only if the step is optional or can be completed later).
   - `Abort`: Terminate the pipeline.
3. **Respect user decision**: Do not proceed until the user chooses an option.

### Pipeline Context Schema (Central Definition)

**Purpose:** All fields shared between steps are defined here. Each downstream module's Input Requirements section MUST reference this schema by field name.

| Field | Type | Producer (Step) | Consumer Steps | Description |
|:---|:---|:---:|:---|:---|
| `config` | object | 0 — Setup Wizard | 1, 2 | Project Configuration Profile: `interaction_language` (ISO 639-1, auto-detected in Step 0), target language, writing type (综述/研究论著/学位论文/开题报告/基金申请/调研报告/自定义), journal tier, time span, CN supplements |
| `active_project_id` | string | 0 — Setup Wizard | all | 当前激活的项目 ID。 |
| `active_project_dir` | string | 0 — Setup Wizard | all | 当前激活项目目录（相对工作区根）。**所有下游文件读写与记忆操作仅限此目录**，见「项目隔离」硬规则。 |
| `scope` | object | 1 — Scope Definer | 2 | Search Scope Confirmation Document (core direction, 3 keyword tiers, explicit exclusions, priority rules) |
| `search_strategy_pack_path` | string | 2 — Search Strategist V1 | final | Path to the delivered search strategy pack (scope_card.md + query_pack.md + candidate_list + usage_guide.md) |
| `v1_report_path` | string | 2 — Search Strategist V1 | — | Path to Literature Collection Report V1 (.md)，作为检索策略包的候选清单来源 |

> **CRITICAL — Data Flow Principle (harvested ≠ corpus):**
> - **API 收割的文献只是"候选参考清单"，不是语料。** AI 通过 API / 检索式收割到的元数据（标题、作者、DOI、期刊、年份）**经常包含虚构、错位或拼错的内容**，**不能直接当作可信事实**。
> - **下载决策权完全在用户。** Search Strategist V1 只负责把候选清单（含检索式、下载链接、OA 状态）呈现给用户；由用户自行核对、筛选、决定下载哪些 PDF。**AI 不替用户自动下载，也不替用户决定纳入。**
> - **检索策略包是终点交付物，不再串联下游选题。** 用户据此自行到各平台验证检索式、下载文献。综述选题与大纲等下游写作环节由用户自行决定工具与流程。
> - **违反此原则的代价：** 把 AI 虚构的文献当事实写进论文 → 事实错误乃至学术不端。因此"人是最终把关者（human-in-the-loop）"是硬性红线，不可被任何"自动化便利"绕过。

> **Deliverable:** The pipeline output is a **search strategy pack** — scope card + multi-platform query pack (6 databases, each with recall-optimized A and precision-optimized B) + candidate literature list (deduped metadata + OA status + DOI links) + usage guide. Every produced artifact carries source-citation anchors for full traceability.

### Completion
After the final step (Search Strategist V1, Step 2) — once the user confirms the search strategy pack at G2 — the main Skill outputs a completion summary in the user's **interaction language** (detected in Step 0, locked per the Hard Language Lock). The reference versions below are in English and Chinese; translate into any other language the user is writing in:
> **English:** "QueryStrategist pipeline complete (Steps 0–2). Search strategy pack delivered: scope card + 6-database queries + candidate list + usage guide. Thank you for using QueryStrategist!"
> **Chinese:** "QueryStrategist 流水线已完成（Step 0–2）。检索策略包已交付：范围卡 + 6 库检索式 + 文献候选清单 + 使用说明。感谢使用 QueryStrategist！"

## Output Format

### Pipeline Status Display
After each step, the main Skill displays a concise status update (use Chinese labels when entry is Chinese, English labels otherwise):

**English version:**

===== QueryStrategist Pipeline Status (Steps 0–2) =====
Steps:  ██████░░░░  (2/3 completed)
Current: Step 2 – Search Strategist V1
Status: in_progress

Completed:
  ✅ Step 0 – Setup Wizard
  ✅ Step 1 – Scope Definer
  ✅ Step 2 – Search Strategist V1 (awaiting G2 strategy pack confirmation)
Next: deliver search strategy pack after confirmation
==============================================

**Chinese version:**

===== QueryStrategist 流水线状态（Step 0–2）=====
进度:  ██████░░░░  (2/3 已完成)
当前: 第 2 步 – 检索策略 V1
状态: 执行中

已完成:
  ✅ 第 0 步 – 配置
  ✅ 第 1 步 – 范围界定
  ✅ 第 2 步 – 检索策略 V1（等待 G2 检索策略包确认）
下一步: 确认后交付检索策略包
==============================================

## Important Notes
- If the user specifies a research direction in the entry command (e.g., ""Start QueryStrategist. My direction is: deep learning for medical image segmentation""), the main Skill feeds this direction directly into Step 0 Setup Wizard and Step 1 Scope Definer as pre-populated context, rather than asking the user to restate it.
- The main Skill does not execute any sub-module's internal logic itself out of context; it reads and executes the sub-module's `SKILL.sub.md` instructions (or delegates via Skill tool if installed) and reports the results. If a sub-module's file is missing, the main Skill informs the user and asks whether to skip or pause until it is available.
- The user can abort at any time by saying ""stop pipeline"" or ""abort"".
- The user can skip backward to redo any completed step by saying ""re-run Step X"".
- **Scope:** QueryStrategist delivers the Step 0–2 pipeline (Setup Wizard → Scope Definer → Search Strategist V1); the final deliverable is a **search strategy pack** (scope card + queries + candidate list + usage guide). The pipeline ends here — downstream review-topic/outline generation is out of scope.

## 目录结构（SCP 单包形态）

```
querystrategist/                    # 上架目录（文件夹内含 SKILL.md，作为单个 Skill 上传）
├── SKILL.md                        # 主 Skill（本文件，唯一入口，承担编排器职责）
├── README.md                       # 提交文档
├── RUN.md                          # 运行手册
├── LICENSE                         # MIT
├── setup_wizard/                   # Step 0 子模块（指令: setup_wizard/SKILL.sub.md）
├── scope_definer/                  # Step 1 子模块
├── search_strategist_v1/           # Step 2 子模块（含 assets/search_strategy_pack_template.md）
├── query_crafter/                  # 6 平台检索式总控子模块
├── wos_query_crafter/  scopus_query_crafter/  ieee_query_crafter/
├── google_scholar_query_crafter/  cnki_query_crafter/  wanfang_query_crafter/
├── literature_harvester/           # API 收割子模块（OpenAlex 收割 + Crossref 验证）
└── _shared_tools/                  # 共享工具（ensure_tool.py / validate_skills.py / build_ppt.py）
```

每个子模块目录均含 `SKILL.sub.md`（SCP 单包形态；本地独立安装时改回 `SKILL.md`）+ 骨架 `scripts/` `references/` `assets/`。
