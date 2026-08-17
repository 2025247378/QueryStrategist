---
name: setup_wizard
description: "QueryStrategist 零配置启动模块 | 自动检测交互语言、建立或恢复项目，并用安全默认值生成完整六库检索所需配置。不得逐项询问目标语言、目标期刊、写作类型、期刊层级、时间跨度、中文补充或行业报告；用户当前消息已明确提供的偏好直接覆盖默认值。Step 0 只在缺少研究方向或需要选择已有项目时提问，G0 为内部自动校验点。"
license: MIT
metadata:
  skill-author: PanY
  version: v1.6.1
  keywords: [literature search, zero-config, setup, full coverage, QueryStrategist]
  triggers: [文献检索配置, 检索设置, setup, 开始配置]
---

# Setup Wizard

## 目标

以最少交互建立可执行项目配置。默认生成完整六库检索策略，把写作类型、期刊、时间范围和补充材料从“启动前必答题”改为“可显式覆盖的默认项”。

## 硬规则

1. 不得逐项询问以下七项：目标语言、目标期刊、写作类型、目标期刊层级、文献时间跨度、中文文献补充、行业报告补充。
2. 用户在当前消息中明确提供某项偏好时直接采用，不得重复询问。
3. 未明确提供时使用本文件定义的 `system_default`，不得把默认值描述成用户选择。
4. Search B 联网授权不属于 Step 0。此字段必须保持 `null`，仅由 Search Strategist V1 在访问 API 前询问一次。
5. G0 是内部配置完整性校验点，不是人工确认门，不得展示配置卡并等待用户确认。
6. 只有两种情况允许在 Step 0 提问：研究方向缺失；工作区存在多个项目且无法确定继续哪个项目。
7. 默认交付目录为 `projects/<active_project_id>/deliverables/`。用户已在当前消息明确给出路径时直接采用，不再询问。

## 通用检索策略

| 写作类型 | 策略权重 | 检索式偏好 | 时间策略 |
|---|---|---|---|
| 通用检索（默认） | 查全与查准均衡 | 同时交付 A0、A1、B 和综述补充式 | 主检索不限年份，提供近 10/5/2 年筛选预设 |
| 综述 | 查全优先 | A0 查漏、A1 主检索、B 定位核心 | 近 10 年 + 经典文献 |
| 研究论著/实验研究 | 查准优先 | B 优先，保留 A0/A1 | 近 5 年 |
| 学位论文 | 查全与查准均衡 | A0/A1/B 全部使用 | 近 10 年 |
| 开题报告/基金申请 | 新颖性优先 | B + 近 2 年筛选，保留 A0/A1 | 近 5 年并突出近 2 年 |
| 调研报告 | 均衡 | A0 起步，逐步调窄 | 近 5 年 |
| 自定义 | 按用户明确要求 | 仍保留完整分层检索式 | 按用户明确要求 |

无论写作类型为何，完整流水线都生成六库 A0/A1/B；写作类型只决定推荐顺序、候选排序和使用说明，不再决定是否生成某个平台或某个基础层级。

## Step 0.1：检测交互语言

从触发消息检测 `interaction_language`（ISO 639-1）。用户后续切换语言时跟随当前消息。交付 HTML 始终提供中英界面；数据库检索词使用平台原生语言：WoS、Scopus、IEEE Xplore、Google Scholar 使用英文词表，CNKI、万方使用中文词表。

## Step 0.2：建立或恢复项目

检查工作区 `projects/`：

- 没有有效项目：自动新建项目，不询问。
- 只有一个可继续项目且用户明确表示“继续”：直接恢复。
- 存在多个项目且用户未指定：只询问一次“继续哪个项目或新建项目”。项目看板最多展示一次。
- 用户明确说“新建项目”：立即新建，后续不得读取其他项目内容。

项目 ID 使用 `<topic_slug>_<YYYYMMDD>`；主题尚未提供时可暂用 `untitled_<YYYYMMDD>`，获得研究方向后再记录正式标题，不因命名再次提问。

写入工作区根 `active_project.json`，并将状态、配置和记忆限制在 `projects/<active_project_id>/`。恢复项目时复用已保存的用户显式配置，不重复执行七项配置提问；若旧配置缺少 `research_direction`、`enabled_databases`、`field_sources` 或新的时间策略字段，按本版本默认值静默补齐并标记 `system_default_migrated`，不得覆盖已有 `user_explicit` 值。

## Step 0.3：提取显式输入

只从用户当前会话原文提取以下内容：

- `research_direction`
- 写作类型、目标期刊/层级、年份范围等明确修饰语
- 明确的平台排除要求，例如“不要中文数据库”
- 明确的行业报告需求
- 自定义交付目录

没有明确表达的字段不得从长期记忆、其他项目或常识推断为用户选择。若 `research_direction` 缺失，只询问一次研究方向；其余字段继续使用默认值。

## Step 0.4：生成零配置档案

按以下默认值生成 `config`，显式输入覆盖对应字段：

```json
{
  "research_direction": "<用户原文>",
  "research_direction_source": "user_explicit",
  "interaction_language": "zh",
  "target_language": "database-native",
  "writing_type": "通用检索",
  "target_journal": null,
  "author_guidelines_path": null,
  "journal_tier": "not-specified",
  "literature_time_span": {
    "mode": "multi_window",
    "label": "不限年份主检索 + 近10/5/2年筛选",
    "start": null,
    "end": 2026,
    "presets_years": [10, 5, 2],
    "apply_to_search_a_query": false
  },
  "enabled_databases": [
    "Web of Science",
    "Scopus",
    "IEEE Xplore",
    "Google Scholar",
    "CNKI",
    "Wanfang"
  ],
  "chinese_language_supplement": true,
  "industry_report_supplement": "template_only",
  "deliverables_dir": "projects/<active_project_id>/deliverables/",
  "network_access_consent": null,
  "field_sources": {
    "interaction_language": "detected_current_session",
    "target_language": "system_default",
    "writing_type": "system_default",
    "target_journal": "system_default",
    "journal_tier": "system_default",
    "literature_time_span": "system_default",
    "enabled_databases": "system_default",
    "chinese_language_supplement": "system_default",
    "industry_report_supplement": "system_default",
    "deliverables_dir": "system_default"
  }
}
```

运行年份替换示例中的 `2026`。用户明确提供的字段将来源改为 `user_explicit`；具体期刊只将 `journal_tier` 记为 `journal-directed`，不得自动声称其属于 Q1/Q2。用户明确排除中文数据库时才允许从 `enabled_databases` 移除 CNKI/万方并将来源记为 `user_explicit`。

行业报告默认仅在 `usage_guide` 中生成独立的灰色文献检索模板，不混入六库学术检索式和候选文献清单。只有用户明确要求时才把该字段改为 `requested`。

## Step 0.5：G0 内部自动校验

验证以下条件：

- `research_direction` 非空。
- `interaction_language`、`writing_type`、`literature_time_span` 和 `enabled_databases` 存在。
- `literature_time_span.mode` 为 `multi_window` 或 `fixed`。
- 默认交付目录位于活动项目内，或来自用户明确输入。
- `network_access_consent` 仍为 `null`。

通过后记录：

```json
{
  "g0_status": "auto_passed",
  "g0_human_confirmation_required": false,
  "step_0_status": "completed"
}
```

不得向用户提问“配置是否正确”。只用一句简短状态说明进入 Scope Definer；聊天中不展开完整配置档案。

## 输出与持久化

将配置同时写入：

- `projects/<active_project_id>/project_meta.json`
- `projects/<active_project_id>/pipeline_state/config.json`

`project_meta.json` 至少保存项目 ID、研究方向、写作类型、当前步骤、进度和更新时间。下游必须读取结构化字段，不得依赖展示标签。

## 兼容与覆盖规则

- 恢复旧项目时先执行配置迁移：补齐本版本必需字段，再运行 G0；迁移只补缺失值，不改变用户已有选择。
- `fixed` 时间范围仍使用整数 `start/end`。
- `multi_window` 允许 `start: null`，但必须有整数 `end` 和非空 `presets_years`。
- 用户后续提出“改为综述”“只看近五年”“针对某期刊优化”等请求时，更新相应字段并重新生成受影响的下游内容，不重新运行七项问答。
- 直接模式 `search_a_all`、`single_platform`、`adjust_existing` 仍由主 Skill 路由，不进入本模块。
