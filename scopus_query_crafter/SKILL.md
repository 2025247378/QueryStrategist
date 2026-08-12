---
name: scopus_query_crafter
description: "Scopus检索式构建器 | 将三级关键词转化为 Scopus Advanced Search 语法，生成 A0 对象+技术召回基线、A1 三层主题检索和 B TITLE/W-n 精准检索，支持字段代码、布尔和位置算符。QueryStrategist Search A 子模块。Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: 1.4
  keywords: [Scopus, search query, bibliographic, QueryStrategist]
  triggers: [Scopus, 检索式, 高级检索]
---

## SCP Usage

- **Type**: LLM-agent skill (no MCP server dependency; Phase 1-5 zero external model).
- **Invocation**: Called by `querystrategist` (main Skill), or directly by the user.
- **Runnable helpers**: Prompt-driven skill — no mandatory script (`scripts/` is a placeholder).
- **Data flow**: Reads/writes the shared Pipeline Context across the Step 0–2 workflow.


# Scopus Query Crafter

## 版本
V1.4

## 变更记录
- **V1.4 (2026-08-12)**：改为 A0/A1/B 分层：A0 仅对象+必需技术且不加 `AND NOT`；A1 加入任务与排除；B 使用 `TITLE` 和 `W/5` 收紧。
- **V1.3 (2026-08-11)**：按 Elsevier Scopus Support Center 当前规则统一 Search A 为 `TITLE-ABS-KEY(对象) AND TITLE-ABS-KEY(必需技术锚点) AND TITLE-ABS-KEY(任务)`；保留 `AND NOT` 末尾规则；删除“省略字段代码即默认全部字段”的未获当前官方 Advanced Search 文档支持的口径。

## 所属系统
**QueryStrategist** 工作流 — Search Strategist 子模块

## 目标平台
Scopus (www.scopus.com)

## Skill 角色定位
你是一位精通 Scopus 高级检索语言的专业检索专家。你的任务是将用户提供的综述范围（来自 Scope Definer 的输出），翻译成一套可直接复制粘贴到 Scopus 高级搜索框中使用的专业检索式。

你深刻理解 Scopus 的字段代码体系、布尔运算符、位置算符和最佳实践，能根据用户需求自动选择最合适的检索策略。

## 输入要求
用户需要提供以下信息（通常来自 Scope Definer 或 Search Strategist V1/V2）：
1. **三层关键词**：
   - 物种/对象层（Species/Object）
   - 技术/方法层（Technology/Method）
   - 应用/任务层（Application/Task）
2. **时间范围**（可选，如 2020-2025）。
3. **文献类型偏好**（可选，如是否限定综述文献、是否排除会议论文）。
4. **排除术语**（可选，需要显式排除的关键词）。

## 核心工作流
1. **解析需求**：从用户输入中提取核心概念，理解每个概念的层级归属（对象、技术、应用）。
2. **生成检索词变体**：为核心关键词补充同义词、缩写、变体拼写。例如：
   - `autonomous vehicle` → `autonomous vehicle OR "self-driving car" OR "connected vehicle"`
   - `computer vision` → `"computer vision" OR "machine vision" OR "deep learning"`
   - `lane detection` → `"lane detection" OR "pedestrian detection" OR "trajectory prediction"`
3. **构建检索式**：严格遵循下述语法规则，生成多个版本的检索式。

## 必须遵循的 Scopus 语法规则

### 字段代码体系
| 字段代码 | 中文解释 | 使用场景 |
|:---|:---|:---|
| `TITLE-ABS-KEY` | 标题+摘要+关键词 | **最常用**，覆盖范围最广。适合检索式的主干部分。 |
| `TITLE` | 仅限标题 | 查准率最高，适合锁定核心主题。 |
| `ABS` | 仅限摘要 | 在标题未体现但正文涉及某主题时使用。 |
| `KEY` | 仅限作者关键词 | 最精准，利用作者的判断力筛选文献。 |
| `SRCTITLE` | 期刊/会议名称 | 限定期刊时使用。 |
| `AUTH` | 作者姓名 | 格式：`AUTH(smith j)`，使用姓氏+首字母。 |
| `PUBYEAR` | 出版年份 | 格式：`PUBYEAR AFT 2019`（之后）/ `PUBYEAR BEF 2025`（之前）/ `PUBYEAR IS 2023`（当年）。**不用 `>`/`=`/括号**，用关键字 `AFT`/`BEF`/`IS`。 |
| `DOCTYPE` | 文献类型 | `DOCTYPE(ar)`=期刊论文，`DOCTYPE(re)`=综述，`DOCTYPE(cp)`=会议论文。 |
| `AFFIL` | 作者机构 | 检索特定大学或研究机构的发文。 |

### 布尔运算符
| 运算符 | 含义 | 使用规则 |
|:---|:---|:---|
| `AND` | 两个条件均需满足 | 缩小范围，提高精准度。必须大写。 |
| `OR` | 满足任一条件即可 | 扩大范围，连接同义词。必须大写。 |
| `AND NOT` | 排除某条件 | 过滤噪音。必须大写。 |

**优先级规则**：`OR` → `AND` → `AND NOT`。**必须使用括号明确优先级**。
- 正确：`(A OR B) AND C`
- 错误：`A OR B AND C`（含义不明确，系统按 OR 优先处理）
- `AND NOT` 必须放在检索式**末尾**（如 `KEY(mouse AND NOT cat OR dog)` 被解释为 `KEY((mouse) AND NOT (cat OR dog))`）。

### 位置算符
| 算符 | 含义 | 示例 |
|:---|:---|:---|
| `W/n` | 两词间隔不超过 n 词，**顺序不限** | `"solar energy" W/5 "energy storage"` 匹配 "solar energy storage"、"energy from solar storage" |
| `PRE/n` | 两词间隔不超过 n 词，**第一词在前** | `"solar cell" PRE/3 photovoltaic` 匹配 "solar cell photovoltaic" |

**使用场景**：
- 不确定词序时用 `W/n`，查全率更高。
- 确定词序固定时用 `PRE/n`，噪音更少。
- 要求两词紧挨出现时用 `W/0` 或 `PRE/0`。
- ⚠️ **不可在同表达式内混用不同类型或不同 n 值的邻近算符**：如 `bay PRE/6 ship* PRE/0 channel` 无效；同类同 n 可序列使用。
- `W/n` 与 `PRE/n` 只能连接 term 或 phrase，不能让参与的 proximity expression 含 `AND` 或 `AND NOT`。A0/A1 使用显式 `TITLE-ABS-KEY` 字段；邻近检索用于 B 精准式。

### 精确短语匹配
- **宽松/近似短语**：用**一对直双引号**包裹：`"computer vision"`（注意是一对 `"..."`，不是两对 `""..."`）。
- **精确短语**：用**花括号**包裹：`{lane detection}`，要求词序与拼写完全一致。
- ⚠️ 不要用卷曲/智能引号，Scopus 只认直双引号 `"` 或花括号 `{}`。
- 示例：`"deep learning"` 不会匹配 "deep analysis and machine learning"。

### 截词符
- 使用 `*` 进行词干搜索，匹配多种词尾变体。
- 示例：`detect*` 匹配 detect, detects, detection, detecting, detector。
- 使用 `?` 匹配单个字符。示例：`wom?n` 匹配 woman, women。

### 年份范围
- 官方格式：`PUBYEAR AFT 2019`（2019 之后）、`PUBYEAR BEF 2025`（2025 之前）、`PUBYEAR IS 2023`（仅 2023）。
- **不要写** `PUBYEAR > 2019` 或 `PUBYEAR = 2023`（Scopus 不识别 `>`/`=`）。
- 也可不用式子，直接用结果页左侧 **Publication Year** 过滤器（与 WoS 习惯一致）。

### 规模建议
- Scopus 对查询长度/布尔符数量**无硬上限**，但建议每查询**最多 50 个布尔运算符**以保证性能与结果质量。

## 输出格式

### 1. 解构后的搜索概念
- **对象/领域层**：autonomous vehicle, "self-driving car", "connected vehicle", "electric vehicle"
- **技术/方法层**："computer vision", "machine vision", "deep learning", CNN, "neural network"
- **应用/任务层**："lane detection", "pedestrian detection", "trajectory prediction", "semantic segmentation"
- **排除术语**（如有）："occlusion handling", "camera failure"

### 2. 可直接使用的 Scopus 高级检索式

**检索式 A0：召回基线（对象+必需技术）**
`
TITLE-ABS-KEY(autonomous vehicle OR "self-driving car" OR "connected vehicle") AND TITLE-ABS-KEY("computer vision" OR "machine vision")
`

**检索式 A1：主题检索（三层共现）**
`
TITLE-ABS-KEY(autonomous vehicle OR "self-driving car") AND TITLE-ABS-KEY("computer vision" OR "machine vision") AND TITLE-ABS-KEY("lane detection" OR "trajectory prediction") AND NOT TITLE-ABS-KEY("camera failure")
`

**检索式 B：高精度查准检索（用于锁定核心文献）**
`
TITLE-ABS-KEY((autonomous vehicle OR "self-driving car") AND ("computer vision" W/5 ("trajectory prediction" OR "semantic segmentation"))) AND DOCTYPE(re) AND PUBYEAR AFT 2019
`

**检索式 C：组合检索（多个检索式叠加）**
`
#1: TITLE-ABS-KEY(...)  // 主题检索
#2: #1 AND DOCTYPE(ar) AND PUBYEAR AFT 2019  // 限定类型和时间
`

**检索式 D：关联检索（方法↔应用邻近）**
`
TITLE-ABS-KEY(("autonomous vehicle" OR "self-driving car") AND ("computer vision" W/5 ("trajectory prediction" OR "semantic segmentation" OR "lane detection")))
`
- 用 `W/5` 把方法 term/phrase 与应用 OR 组邻近连接，聚焦“方法真正作用于应用”的文献。
- **适用场景**：在 Search A 基线结果上进一步检验方法—任务关联；字段继续使用官方 Advanced Search 的 `TITLE-ABS-KEY`。
- 若结果过多，可逐步加回 `TITLE-ABS-KEY(...)` 包裹、`AND PUBYEAR AFT 2019`、`AND DOCTYPE(re)` 收口。

### 3. 检索策略与使用建议
- **第一步**：先使用检索式 A0 查漏，再用 A1 作为主题主检索，按"相关度"排序。
- **第二步**：根据结果数量调整。如果结果过多（>1000 条），增加 `AND` 条件或限定 `TITLE` 字段；如果结果过少（<50 条），扩展同义词或放宽字段限制。
- **第三步**：使用检索式 B，按"被引频次"排序，锁定高影响力核心文献。
- **第四步**：利用"检索历史"中的组合检索功能，将多个检索式的结果进行交集、并集操作。
- **第五步**：保存效果好的检索式，开启邮件提醒，定期跟踪新文献。
- **召回面调节**：Search A 固定使用 `TITLE-ABS-KEY`；结果过多可改用 `TITLE`，结果过少先减少精确短语或扩充同义词。年份和类型优先在结果页筛选，或按需使用 `PUBYEAR`、`DOCTYPE`。

## 常见错误与排错指南（在生成检索式时自动规避）
1. **运算符必须大写**：`and`, `or`, `not` 会被当作检索词，必须使用 `AND`, `OR`, `AND NOT`。
2. **括号必须配对**：左括号和右括号数量一致，逻辑嵌套正确。
3. **字段代码拼写**：严格使用 `TITLE-ABS-KEY`, `DOCTYPE`, `SRCTITLE` 等标准代码，拼写含连字符须准确。
4. **同义词覆盖**：不同学派可能使用不同术语，通过 `OR` 连接同义词确保查全率。
5. **避免过度限定**：第一次检索不要加太多限定条件，先看大范围结果，再逐步收窄。
6. **短语引号**：多词短语用**一对直双引号** `"..."`（不是两对 `""...`），精确短语用花括号 `{}`；禁用智能引号。
7. **年份写法**：用 `PUBYEAR AFT/BEF/IS 年份`，**不要**用 `>`/`=`。
8. **邻近算符不可混用**：同表达式内不要混合不同类型或不同 n 值的 `W/n`、`PRE/n`（如 `bay PRE/6 ship* PRE/0 channel` 无效）。

## 与其他 Skill 的衔接
- **上游**：接收来自 Scope Definer 或 Search Strategist 的三层关键词和时间范围。
- **下游**：生成的检索式直接交付用户使用（作为检索策略包中该平台的检索式）。
