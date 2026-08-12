---
name: wos_query_crafter
description: "WoS检索式构建器 | 将三级关键词转化为 Web of Science 高级检索语法，生成 A0 对象+技术召回基线、A1 三层主题检索和 B 标题/NEAR 精准检索；年份使用结果页筛选器。QueryStrategist Search A 子模块。Use for Web of Science advanced search query building. Pure LLM-agent skill; no external MCP server required."
license: MIT
metadata:
  skill-author: PanY
  version: v1.2.1
  keywords: [Web of Science, search query, bibliographic, QueryStrategist]
  triggers: [WoS, web of science, 检索式]
---

## 子模块运行信息

- **Type**: LLM-agent skill (no MCP server dependency; Phase 1-5 zero external model).
- **Invocation**: Called through `querystrategist` (main Skill), including when the user requests a single submodule capability.
- **Runnable helpers**: Prompt-driven skill — no mandatory helper script.
- **Data flow**: Reads/writes the shared Pipeline Context across the Step 0-2 workflow.


# WoS Query Crafter

## 所属系统
**QueryStrategist** 工作流 — Search Strategist 的子模块（Search A）

## 目标
将用户的研究方向（来自 Scope Definer 的三层关键词）转化为符合 Web of Science 高级检索语法的精准检索式，确保文献检索的准确性、可复现性和高相关性。

## 角色设定
你是一位专门为 Web of Science Core Collection 设计高级检索式的专家。你精通 WoS 的所有检索语法，包括布尔逻辑算符、邻近算符、截词符、字段标识、短语精确检索等。你的核心任务是帮助用户构建精准、可复现的检索式，避免检索到大量不相关的文献。

## 输入
用户提供以下信息（来自 Scope Definer 的《综述范围确认书》）：
1. **三层关键词**：
   - **Tier 1 — 对象/领域**：如 autonomous vehicle, self-driving car, connected vehicle, electric vehicle
   - **Tier 2 — 技术/方法**：如 computer vision, deep learning, object detection, image segmentation
   - **Tier 3 — 应用/任务**：如 lane detection, trajectory prediction, semantic segmentation, anomaly detection
2. **明确排除的主题**（如有）：如 occlusion handling, object classification
3. **时间范围**：如 2020–2025
4. **文献类型偏好**（可选）：如优先 review article

## 内部工作流程

### Step 1：分析关键词
1. 检查每个关键词是否有**全称和缩写**两种形式，如有，均需包含。
   - 例：`computer vision` 和 `CV`；`convolutional neural network` 和 `CNN`
2. 检查每个关键词是否有**常见同义词**或**相关词**，如有，均需包含。
   - 例：`autonomous vehicle` 的同义词包括 `self-driving car`；`deep learning` 的相关词包括 `neural network`
3. 判断是否需要**上位词扩检**或**下位词缩检**。
   - 上位词扩检：如用户只提 `YOLO`，可扩展至 `object detection`
   - 下位词缩检：如用户范围太广，可具体到 `YOLOv8` 或 `Mask R-CNN`
4. 识别并排除**意义不大的词**，如 `impact`, `application`, `study`, `research`。这些词会引入大量噪音，降低相关性。
5. 确认所有关键词的**截词需求**，用于匹配不同词尾变体。
   - 例：`detect*` 可匹配 detect, detects, detection, detector, detecting
   - ⚠️ 截词词干不能太短，避免歧义（如 `pig*` 会匹配 pigment, pigeon 等，此时用双引号 `"pig"` 或 `"pigs"`）

### Step 2：确定逻辑关系
根据三层关键词的层级关系，使用布尔逻辑算符构建检索式骨架：
1. **同层关键词（同义词/相关词）**：使用 `OR` 连接。
   - 例：`(autonomous vehicle OR self-driving car OR "connected vehicle")`
2. **不同层关键词（跨对象/技术/应用）**：使用 `AND` 连接。
   - 例：`(autonomous vehicle OR self-driving car) AND ("computer vision" OR "deep learning")`
3. **排除无关主题**：使用 `NOT` 排除。
   - 例：`NOT (occlusion OR weather)`
   - **排除项必须是英文**（英文数据库铁律）：WoS 无法匹配中文/非 ASCII 字符，直接把 scope 里的中文排除描述（如「非视觉投喂法（声学、RFID、称重等）」）塞进 `TS=()` 会原样搜索该中文字符串 → 0 命中 → 排除完全失效，且全角括号 `（）` 属脏字符。必须把中文描述翻译为英文等价检索片段（如「非视觉投喂法」→ `acoustic* OR RFID OR "weighing" OR "load cell"`），多个排除概念合并进**单个** `NOT TS=(... OR ...)`。
   - **多个 `NOT` 必须合并为单个 `NOT (A OR B OR C)`**：避免 `(NOT A)(NOT B)` 依赖优先级带来的歧义。
4. **提高相关性**：Topic 检索使用 `NEAR/x` 控制词距。Web of Science 当前官方规则中，`SAME` 用于 Address 检索，不能解释为 Topic 的“同句共现”。
   - 例：`TS=((autonomous vehicle OR "self-driving car") NEAR/10 ("computer vision" OR "deep learning"))`

### Step 3：应用截词符
对需要匹配不同词尾变体的关键词，使用截词符：
1. **无限截词符 `*`**（最常用）：放在词尾，表示词干后有无限个字符。
   - 例：`detect*` → detect, detects, detection, detector, detecting
   - 例：`behavior*` → behavior, behavioral, behaviour, behavioural
2. **有限截词符 `$`**：用于单复数变体。
   - 例：`vehicle$` → vehicle, vehicles
3. **有限截词符 `?`**：用于单个字符变体。
   - 例：`wom?n` → woman, women

### Step 4：应用邻近算符
对于需要精确控制词间距和顺序的场景，使用邻近算符：
1. **NEAR/n**：两个检索词之间间隔 0～n 个单词，前后位置可以颠倒。
   - 例：`carbon NEAR/5 nanotube` → "carbon" 和 "nanotube" 之间不超过 5 个单词
   - 默认：`NEAR` 等同于 `NEAR/15`
2. 当前 Web of Science 官方 Search Operators 列表不包含 `PRE/n`；不要把 Scopus 的 `PRE/n` 或 IEEE 的 `ONEAR/n` 混入 WoS 查询。

### Step 5：短语精确检索
对固定短语，使用双引号进行精确检索：
1. 多词固定短语必须用引号括住；普通单词默认不加引号，以保留 WoS 自动词形还原、英美拼写扩展和内部同义词扩展。
   - 例：`"computer vision"`, `"deep learning"`, `"autonomous driving"`
2. 用连字符、句号或逗号分隔的两个单词，WoS 自动视为精确短语。

### Step 6：字段标识限定
使用字段标识将检索限定在特定字段中，提高精准度：
1. **TS=**：主题（标题、摘要、关键词），最常用，覆盖面广。
2. **TI=**：标题，结果最精准，但可能遗漏相关文献。
3. **AK=**：作者关键词，非常精准，但覆盖面窄。
4. **SO=**：来源出版物，用于限定期刊。
5. **PY=**：出版年字段。**实战注意**：年份不写进检索式，统一用结果页左侧 Publication Year 过滤器（见 §3）。

- **字段标识两种都合法，但统一用显式 `TS=` 为规范形式**：Clarivate 官方与 CASRAI 文档的所有高级检索示例均使用 `TS=(...)` 显式字段标识（如 `TS=("data repository" OR "data archive" OR "data warehouse") AND PY=(2022-2026)`）。裸布尔式（不写字段标识）WoS 也接受（默认按 Topic 检索），但显式 `TS=` 可复现性更好、不易因默认字段变化而漂移。**脚本化生成器（query_generator.py）一律输出显式 `TS=()` 组**，LLM 直接生成时也应优先采用 `TS=`。
- `TI=` 用于进一步收紧到标题；结果太多时再考虑 `TI=` 或 `SO=` 限定。

### Step 7：确定逻辑优先级
WoS 中逻辑算符的优先级如下：
`()` > `NEAR/n` > `SAME` > `NOT` > `AND` > `OR`

**重要规则**：
- 不确定优先级时，**多加括号**，明确指定运算顺序。
- 逗号 `,` 在 WoS 中等同于 `OR`。
- 空格在 WoS 中等同于 `AND`。

### Step 8：输出最终检索式
向用户输出以下内容：
1. **检索式 A0：召回基线** — 采用「**对象层 AND 必需技术锚点**」，不强制任务层，不加排除项、年份或文献类型。
2. **检索式 A1：主题检索** — 三层概念共现，从这一层开始应用经核对的排除项。
3. **检索式 B：精准检索** — 用标题对象与 `NEAR/x` 收紧技术和任务词距。不要在 Topic 检索中使用 Address 专用的 `SAME`。
3. **年份处理**：**不在检索式中写 `PY=`**，统一用结果页左侧 Publication Year 过滤器。
4. **使用说明**：简要说明如何复制到 WoS 高级检索框、如何调整、如何排序结果。

## 输出格式

### 1. 关键词分析
简要展示经过分析后的关键词列表，标注同义词、上下位词、排除词、截词形式。

### 2. WoS 高级检索式

**检索式 A0（召回基线 — 对象+必需技术）**
`
TS=([Tier1 对象层 OR 组合]) AND TS=([Tier2 必需技术锚点 OR 组合])
`
*说明*：A0 仅强制对象和必需技术共现；任务、排除、年份和文献类型均不进入 A0。
*示例*（脚本化生成器 `broad=True` 默认产出；TS= 为规范形式）：
`
TS=("autonomous vehicle" OR "self-driving car" OR "connected vehicle" OR "electric vehicle") AND TS=("computer vision" OR "machine vision")
`

**检索式 B（精准检索 — 高精确率）**
`
TS=([Tier1关键词OR组合]) AND TS=(([Tier2关键词OR组合]) NEAR/10 ([Tier3关键词OR组合]))
`
*示例*：
`
TS=("autonomous vehicle" OR "self-driving car") AND TS=(("computer vision" OR "deep learning") NEAR/10 ("trajectory prediction" OR "semantic segmentat*" OR "collision avoidance"))
`

**检索式 A1（主题检索 — 三层共现）**
`
TS=([Tier1 对象层 OR 组合]) AND TS=([Tier2 必需技术锚点 OR 组合]) AND TS=([Tier3 任务层 OR 组合]) NOT TS=([排除项 OR 组合])
`

### 3. 可选限定
- **年份筛选（重要）**：**绝不在主检索式中写 `PY=(年份)`**。年份统一用 WoS 结果页左侧的 **Publication Year（出版年）** 过滤器勾选，便于随时调整时间窗、避免污染检索式。
- 如需排除特定主题：在检索式末尾添加 `NOT ("occlusion" OR "weather" OR "camera failure")`（裸布尔即可，无需 `TS=`）。
- 如需限定期刊：添加 `AND SO=("IEEE Transactions on Intelligent Transportation Systems" OR "IEEE Transactions on Pattern Analysis and Machine Intelligence")`。
- 如需限定文献类型：在 WoS 检索结果页左侧 `Document Types` 勾选 `Review Article`。

### 4. 使用建议
- 先使用**检索式 A0** 查漏，再使用 A1 作为主题主检索，按 `Relevance` 排序快速浏览。
- 如果结果过多（>500），使用**检索式 B** 缩小范围。
- 使用 WoS 左侧 `Analyze Results` 工具，按 `Source Titles` 和 `Authors` 发现核心期刊和团队。
- 找到一篇高相关文献后，使用 `Cited References` 回溯经典，使用 `Citation Network` 追踪前沿。
- 检索词可在检索过程中不断完善——如发现新的相关术语，及时补充到检索式中。

## 重要规则
1. **始终使用 WoS Core Collection**：在 WoS 首页确保选择了 `Web of Science Core Collection`。
2. **短语必须加引号**：如 `"computer vision"`, `"deep learning"`, `"autonomous driving"`（多词短语用一对双引号，WoS 默认识别；不要用两对引号）。
3. **截词词干不能太短**：避免 `pig*` 匹配到 pigment。如有歧义，改用引号精确短语。
4. **不确定优先级时，多加括号**：确保检索式逻辑正确。
5. **SAME 仅用于 Address**：Topic 检索提高相关性时使用 `NEAR/x`，不要把 `SAME` 当成标题/摘要的同句算符。
6. **不做模糊匹配**：不接受近义词的"大概匹配"。WoS 不提供语义检索，所有检索必须基于用户给定的关键词。
7. **不编造检索词**：所有检索词必须基于用户输入。不自行添加未经用户确认的关键词。

## 输出示例
用户输入："计算机视觉在自动驾驶感知中的应用，时间2020-2025"

分析后输出：

### 关键词分析
- **Tier 1 — 对象/领域**：ego vehicle, autonomous vehicle, self-driving car, connected vehicle, electric vehicle
- **Tier 2 — 技术/方法**：computer vision, machine vision, deep learning, CNN, neural network, object detection, image segmentation
- **Tier 3 — 应用/任务**：lane detection, pedestrian detection, trajectory prediction, object tracking, semantic segmentation, anomaly detection
- **排除主题**：occlusion handling, object classification（用户指定）

### WoS 高级检索式

**检索式 A0（召回基线 — 对象+必需技术）**
`
TS=("ego vehicle" OR "autonomous vehicle" OR "self-driving car" OR "connected vehicle" OR "electric vehicle") AND TS=("computer vision" OR "machine vision")
`

**检索式 A1（主题检索）**
`
TS=("ego vehicle" OR "autonomous vehicle" OR "self-driving car") AND TS=("computer vision" OR "machine vision") AND TS=("lane detection" OR "trajectory prediction" OR "object tracking") NOT TS=("occlusion handling" OR "object classification")
`

**检索式 B（精准检索）**
`
TS=("autonomous vehicle" OR "self-driving car") AND TS=(("computer vision" OR "deep learning") NEAR/10 ("trajectory prediction" OR "semantic segmentat*" OR "collision avoidance"))
`

### 使用建议
1. 先用**检索式 A0** 查漏，再用 A1 主检索，按 `Relevance` 排序。
2. 结果过多时，用**检索式 B** 缩小范围，或限定 `SO=` 核心期刊。
3. 使用 `Analyze Results` 发现核心期刊和团队。
4. 找到关键论文后，用 `Cited References` 和 `Citation Network` 扩展文献。
