# 检索策略包模板（Search Strategy Pack）

> 本模板定义 QueryStrategist 流水线终点（Step 2 / G2 确认后）交付的**检索策略包**标准结构。
> 包含四项相互衔接的逻辑交付物，全部落盘于 `projects/<id>/`。
> 所有字段必须标注上游出处（`【继承自 …】`），禁止凭空生成；无出处条目标记【待补】并向用户确认。
> Markdown 是可编辑源文件，HTML 是默认阅读入口；CSV 和 Markdown 统一使用 UTF-8 BOM。

## 交付格式与编码硬规则

1. 输出 `scope_card.md/.html`、`query_pack.md/.html`、`candidate_list.csv/.md/.html`、`usage_guide.md/.html`。
2. HTML 必须由 `_shared_tools/scripts/render_deliverables.py` 从同名 Markdown 生成，不得维护第二套内容。
3. Markdown 和 CSV 写为 UTF-8 BOM；所有文本严格 UTF-8 解码，不得出现 U+FFFD（`�`）。
4. 最终文件使用 `[已验证]`、`[待人工核验]`、`[已剔除]`、`[注意]` 等纯文本状态，不使用 Emoji。
5. 检索式必须放在 fenced code block 中，不得放进 Markdown 表格；渲染前后逐字一致。

---

## 第 0 节 上游上下文继承总纲（MANDATORY）

检索策略包的所有内容均须收敛自 Step 0–2 的真实选择，不得凭空生成。

| 上游来源 | 产出 | 继承到检索策略包的位置 |
|---|---|---|
| Step 0 Setup Wizard | `project_meta.json`（写作类型 / 目标语言 / 目标期刊 / 时间跨度 / 中文补充） | `scope_card.md` 的写作类型与策略权重；`query_pack.md` 的检索式语言；`candidate_list` 的语言筛选；`usage_guide.md` 的按类型建议 |
| Step 1 Scope Definer | 三级关键词体系 + 排除项 + 优先级（`scope_definition.md`） | `scope_card.md` 的关键词与排除项；`query_pack.md` 的检索式构建依据 |
| Step 2 Search Strategist V1 | Search A 检索式 + Search B 收割结果（`harvest_v1.json`） | `query_pack.md` 的检索式合集；`candidate_list` 的文献元数据 |
| 门控决策记录 | G0–G2 用户确认内容 | `scope_card.md` 的「确认记录」；策略包一致性校验 |

**5 条继承硬规则**：
1. **禁止凭空生成**：任何字段找不到上游出处时标记【待补】并向用户确认，不得编造。
2. **语言继承**：检索式语言由 Step 0 目标语言决定；说明性文字用交互语言（跟随用户）。
3. **范围继承**：`scope_card.md` 的排除项必须与 Step 1 一致；与排除项冲突的文献不得进入候选清单。
4. **写作类型策略权重继承**：`query_pack.md` 的查全/查准版本偏好、`candidate_list` 的排序方式均由 Step 0 写作类型决定。
5. **一致性锁**：四份文件互引一致（范围卡的关键词 = 检索式的构建依据 = 候选清单的筛选口径）。

**生成后校验清单**：
- [ ] 可追溯：每个字段都标了 `【继承自 …】` 或【待补】
- [ ] 语言：检索式语言 = 目标语言；说明 = 交互语言
- [ ] 范围：排除项与 Step 1 一致
- [ ] 互锁：四份文件口径一致
- [ ] 待补项：所有【待补】已向用户确认或说明
- [ ] 落盘：四份文件均已写入 `projects/<id>/`
- [ ] 编码：Markdown/CSV 为 UTF-8 BOM，所有文件不含 U+FFFD
- [ ] 阅读：四份 Markdown 均已生成同名离线 HTML
- [ ] 保真：`query_pack.md` 与 `query_pack.html` 中检索式逐字一致

---

## 1. `scope_card.md` — 范围界定卡

```
# 范围界定卡

## 写作类型与策略权重
- 写作类型：【继承自 Step 0】（综述 / 研究论著 / 学位论文 / 开题报告 / 基金申请 / 调研报告 / 自定义）
- 策略权重：【按写作类型】
  - 综述：查全优先（检索式以宽式 A 为主，候选按相关度+期刊质量排）
  - 研究论著：查准优先（精准式 B 为主，候选按相关度排）
  - 开题/基金：兼顾新颖性（时间窗含近 2 年，标注高被引与潜在空白）
  - 学位论文/调研报告：查全+查准均衡

## 三级关键词体系
- Tier 1（对象）：【继承自 Step 1】
- Tier 2（技术/方法）：【继承自 Step 1】
- Tier 3（应用/场景）：【继承自 Step 1】

## 排除项
- 【继承自 Step 1】

## 优先级规则
- 【继承自 Step 1】

## 确认记录
- G0 配置确认：【时间/内容】
- G1 范围确认：【时间/内容】
```

---

## 2. `query_pack.md` — 多平台检索式合集

```
# 多平台检索式合集

> 每库给「查全式 A（高召回）+ 平台专属查准式 B（高精确）」双版本；IEEE 另保留 C（会议/出版物定向）、D1/D2（NEAR/ONEAR）和 E（综述导向）变体。
> 策略权重按写作类型调整（见 scope_card.md）。

## Web of Science
- 查全式 A：【继承自 Step 2 Search A】
- 查准式 B：【继承自 Step 2 Search A】
- 语法要点：

## Scopus
- 查全式 A：
- 查准式 B：

## IEEE Xplore
- 查全式 A：
- 查准式 B：
- 会议/出版物定向 C（有真实目标名称时）：
- 无序邻近 D1（NEAR）：
- 有序邻近 D2（ONEAR）：
- 综述导向 E：

## Google Scholar
- 查全式 A：
- 查准式 B：

## CNKI（中文补充）
- 查全式 A：
- 查准式 B：

## 万方（中文补充）
- 查全式 A：
- 查准式 B：

## 可调参数
- 时间跨度：【继承自 Step 0】
- 截词/邻近算符使用说明：
```

---

## 3. `candidate_list.csv` / `.md` — 文献候选清单

```
# 文献候选清单

> [注意] 候选清单、非最终语料。元数据可能含虚构/错位，需用户在平台核对后自行下载。
> 来源：Search B API 收割（OpenAlex 主源）+ Crossref 按 DOI 逐条验证（title 相似度 >= 0.8 且年份差 <= 1），已验证条目去重。

## 统计
- 总数：【N】篇
- 验证状态：verified（Crossref 验证通过）【n1】/ unverified（无 DOI 或瞬时错误）【n2】/ dropped（疑似幻觉/错配，已剔除）【n3】
- OA 状态：OA 【n4】/ 非OA 【n5】/ 未知 【n6】

## 清单（CSV 字段）
title, authors, journal, year, doi, doi_link, oa_status, source

## 排序
- 按【写作类型策略权重】：相关度 / 相关度+期刊质量 / 新颖性
```

---

## 4. `usage_guide.md` — 使用说明

```
# 使用说明

## 各库检索式填入位置
- WoS：高级检索，进入 Topic 字段
- Scopus：Advanced Search，进入 TITLE-ABS-KEY
- IEEE：Advanced Search，进入 Command Search
- Google Scholar：直接粘贴（注意 256 字符上限）
- CNKI：高级检索，进入专业检索
- 万方：高级检索，进入跨库检索

## 预期命中量级
- 查全式 A：约【N】篇（预估）
- 查准式 B：约【N】篇（预估）

## 调宽 / 调窄方法
- 调宽（增加结果）：去排除项 / 用 OR 连接同义词 / 放宽时间窗
- 调窄（减少结果）：加 AND / 用精确匹配双引号 / 缩小时间窗 / 限定字段

## 按写作类型的检索建议
- 综述：优先用查全式 A，确保覆盖度
- 研究论著：优先用查准式 B，聚焦核心方法
- 开题/基金：查准式 B + 近 2 年过滤，关注高被引与空白
- 学位论文/调研报告：查全式 A 起步，按结果量调窄

## 候选清单使用
- 顶部 OA 文献可免费下载；非 OA 需机构权限
- DOI 链接可直接点击跳转
- 核对元数据后再下载（API 收割可能有误）
```
