---
name: scope_definer
description: "QueryStrategist 范围界定模块 | 从研究方向自动构建对象、技术、任务、中文词表和排除词分级，默认采用安全的宽范围策略。主题明确时不逐项提问，只展示一次范围卡并在 G1 让用户选择直接生成或调整；仅当对象或核心技术无法识别时，允许一次批量澄清。"
license: MIT
metadata:
  skill-author: PanY
  version: v1.6.1
  keywords: [research scope, keyword tiers, exclusions, fast confirmation, QueryStrategist]
  triggers: [研究范围, 范围界定, 关键词体系, scope]
---

# Scope Definer

## 目标

把研究方向转化为可执行的宽范围检索结构，同时把启动前交互压缩为一次 G1 确认。自动推断用于扩大召回，不得自动制造会误杀结果的硬限制。

## 输入

- Step 0 `config`
- `research_direction`
- 用户当前会话中明确给出的对象、技术、任务和排除范围

`research_direction` 缺失时返回 Step 0，只询问这一项。

## Step 1：自动构建范围

从研究方向生成：

1. `tier1_object`：研究对象及常用同义词、上下位词。
2. `tier1_recall_anchor`：可用于 A0 扩召回的对象中心词。
3. `tier2_required_anchor`：没有它就偏离主题的核心技术。
4. `tier2_supporting_method`：模型、算法、仪器或分析方法，只作支持词，不强制进入所有检索式。
5. `tier3_task`：品质、性能、检测、分级、溯源等应用任务。
6. `tier3_recall_anchor`：任务层的宽泛召回词。
7. `keyword_tiers_zh`：供 CNKI、万方使用的中文词表。

范围优先保持宽泛。若某个方法只是常见实现而非研究主题，不得升级为 `tier2_required_anchor`。

## Step 2：排除词安全策略

排除项分为：

- `strong_exclusions`：仅包含用户明确要求排除的具体短语，可进入 `NOT`。
- `soft_exclusions`：系统推断的可能无关方向，只用于人工筛选提示。
- `risky_exclusions`：过宽词、主题核心词或可能误杀相关文献的词，默认不进入检索式。
- `query_exclusions`：只能从用户明确的 `strong_exclusions` 中选取。

用户未明确给出排除项时，`strong_exclusions` 和 `query_exclusions` 必须为空。不得因为常识判断自动写入 `NOT`。

## Step 3：最小澄清规则

主题同时具备可识别对象和核心技术时，不提任何范围问题，直接生成范围确认文档。

只有以下情况允许澄清：

- 研究方向只有宽泛领域，没有对象。
- 无法区分核心技术与支持方法。
- 同一句话存在互斥任务解释，选择不同会明显改变检索词。

将所有缺失项合并为一次问题，最多询问三个维度；不得逐项进行多轮问答。若用户选择“保持宽泛”，采用不加硬限制的方案继续。

## Step 4：生成范围确认文档

输出简洁的 **Review Scope Confirmation Document**：

```markdown
# 研究范围确认

## 研究方向
[用户原文]

## 关键词层级
- Tier 1 对象：[...]
- Tier 1 召回锚点：[...]
- Tier 2 必需技术锚点：[...]
- Tier 2 支持方法：[...]
- Tier 3 任务：[...]
- Tier 3 召回锚点：[...]
- 中文词表：[...]

## 排除策略
- 强排除：[用户明确项；无则“无”]
- 弱排除：[筛选提示]
- 风险排除：[默认不进入 NOT]
- 实际进入 NOT：[仅确认的强排除；无则“无”]

## 默认覆盖策略
- 数据库：Web of Science、Scopus、IEEE Xplore、Google Scholar、CNKI、万方
- 检索层级：A0、A1、B，另附综述补充式
- 时间：不限年份主检索，提供近 10/5/2 年筛选
```

每个字段记录 `user_explicit` 或 `system_inferred_safe` 来源。

## G1：唯一前置人工确认

展示范围文档后只询问一次：

- `直接生成完整策略包`：确认范围并进入 Search Strategist V1。
- `调整范围`：用户指出需要修改的字段；只修改指定字段后再次展示差异并确认。

无交互工具时在聊天中列出两个编号选项。不得在 G1 前追加七项配置问题，也不得把 Search B 联网授权合并进 G1。

## 输出契约

向下游传递：

```json
{
  "research_direction": "...",
  "keyword_tiers": {
    "tier1_object": [],
    "tier1_recall_anchor": [],
    "tier2_required_anchor": [],
    "tier2_supporting_method": [],
    "tier3_task": [],
    "tier3_recall_anchor": []
  },
  "keyword_tiers_zh": {},
  "strong_exclusions": [],
  "soft_exclusions": [],
  "risky_exclusions": [],
  "query_exclusions": [],
  "scope_sources": {},
  "g1_status": "confirmed"
}
```

将文档保存在活动项目目录。G1 未确认前不得启动 Search A 或 Search B。
