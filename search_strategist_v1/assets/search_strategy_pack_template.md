# 检索策略包模板（Search Strategy Pack）

> 本模板定义 QueryStrategist 流水线终点（Step 2 / G2 确认后）交付的**检索策略包**标准结构。
> 包含四项相互衔接的逻辑交付物，默认落盘于 `projects/<active_project_id>/deliverables/`。
> 所有字段必须标注上游出处（`【继承自 …】`），禁止凭空生成；无出处条目标记【待补】并向用户确认。
> Markdown 是可编辑源文件，HTML 是默认阅读入口；CSV 和 Markdown 统一使用 UTF-8 BOM。

## 交付格式与编码硬规则

1. 输出唯一默认阅读入口 `index.html`，以及作为导出或审计备份的 `scope_card.md/.html`、`scope_card.i18n.json`、`query_pack.md/.html`、`candidate_list.csv/.md/.html`、`usage_guide.md/.html`、`usage_guide.i18n.json`。
2. HTML 必须由 `_shared_tools/scripts/render_deliverables.py` 从同名 Markdown 与双语侧车生成；不得手工维护同语言的第二套 HTML 内容。
3. Markdown 和 CSV 写为 UTF-8 BOM，双语侧车写为 UTF-8 JSON；所有文本严格 UTF-8 解码，不得出现 `U+FFFD` 替换字符。
4. 最终文件使用 `[已验证]`、`[待人工核验]`、`[已剔除]`、`[注意]` 等纯文本状态，不使用 Emoji。
5. 检索式必须放在 fenced code block 中，不得放进 Markdown 表格；渲染前后逐字一致。
6. `scope_card.i18n.json` 与 `usage_guide.i18n.json` 为必需文件，格式如下：

```json
{
  "schema_version": 1,
  "source_language": "zh 或 en，与同名 .md 一致",
  "translations": {
    "另一语言代码": "完整 Markdown 正文"
  }
}
```

7. 双语侧车只翻译标题、字段标签和说明性文字；关键词与排除词列表、平台名、A0/A1/B、检索语法、DOI 和文献元数据不得改写。中英文正文必须表达同一范围与操作规则，不得在译文中新增或删除约束。

---

## 第 0 节 上游上下文继承总纲（MANDATORY）

检索策略包的所有内容均须收敛自 Step 0–2 的真实选择，不得凭空生成。

| 上游来源 | 产出 | 继承到检索策略包的位置 |
|---|---|---|
| Step 0 Setup Wizard | `project_meta.json`（零配置默认档案 / 显式覆盖 / 六库启用列表 / 多时间窗策略） | `scope_card.md` 的写作类型与来源；`query_pack.md` 的六库覆盖和时间筛选预设；`usage_guide.md` 的按类型建议 |
| Step 1 Scope Definer | 三级关键词体系 + 排除项 + 优先级（`scope_definition.md`） | `scope_card.md` 的关键词与排除项；`query_pack.md` 的检索式构建依据 |
| Step 2 Search Strategist V1 | Search A 检索式 + Search B 网络授权记录 + 收割结果（允许时为 `harvest_v1.json`；拒绝时为 `skipped_by_user`） | `query_pack.md` 的检索式合集；`scope_card.md` 的授权记录；`candidate_list` 的文献元数据或跳过状态 |
| 门控与校验记录 | G0 自动校验、G1 范围确认、G2 交付确认 | `scope_card.md` 的「确认记录」；策略包一致性校验 |

**5 条继承硬规则**：
1. **禁止凭空生成**：任何字段找不到上游出处时标记【待补】并向用户确认，不得编造。
2. **语言继承**：检索式使用数据库原生语言（四个国际库使用英文词表，CNKI/万方使用中文词表）；`scope_card.md` 和 `usage_guide.md` 使用交互语言，并通过各自 `.i18n.json` 补齐另一语言正文。
3. **范围继承**：`scope_card.md` 的排除项必须与 Step 1 一致；与排除项冲突的文献不得进入候选清单。
4. **写作类型策略权重继承**：默认“通用检索”采用均衡策略；显式写作类型只改变推荐顺序和候选排序，不删除六库 A0/A1/B。
5. **一致性锁**：四份文件互引一致（范围卡的关键词 = 检索式的构建依据 = 候选清单的筛选口径）。

**生成后校验清单**：
- [ ] 可追溯：每个字段都标了 `【继承自 …】` 或【待补】
- [ ] 语言：国际库使用英文词表、中文库使用中文词表；范围卡与使用说明同时具备 `zh`、`en` 正文；检索式页与候选清单页的结构化界面文字可切换中英文
- [ ] 范围：排除项与 Step 1 一致
- [ ] 互锁：四份文件口径一致
- [ ] 待补项：所有【待补】已向用户确认或说明
- [ ] 落盘：四项逻辑交付物及两个双语侧车均已写入 `projects/<active_project_id>/deliverables/` 或用户明确指定的目录
- [ ] 编码：Markdown/CSV 为 UTF-8 BOM，双语侧车为有效 UTF-8 JSON，所有文件不含 U+FFFD
- [ ] 阅读：四份 Markdown 均已生成同名离线 HTML
- [ ] 入口：`index.html` 可导航到四份内容页，页面无外部资源请求
- [ ] 交互：检索式可复制；候选清单可搜索、筛选、排序；四份内容页均可切换中英文界面或正文；关闭 JavaScript 后主 Markdown 原文仍完整
- [ ] 保真：`query_pack.md` 与 `query_pack.html` 中检索式逐字一致；候选文献题名、作者、期刊、年份和 DOI 在切换前后保持唯一且不变
- [ ] 授权：Search B 网络授权状态已记录；拒绝时未伪造空收割成功

---

## 1. `scope_card.md` — 范围界定卡

同时生成 `scope_card.i18n.json`，提供以下范围卡完整正文的另一语言版本。写作类型等受控配置值必须使用标准中英对应（例如“综述”与“Review”）；自定义值、关键词、排除词和确认记录中的事实值必须与主 Markdown 逐项一致，不得自行翻译或改写。

```
# 范围界定卡

## 写作类型与策略权重
- 写作类型：【继承自 Step 0】（通用检索 / 综述 / 研究论著 / 学位论文 / 开题报告 / 基金申请 / 调研报告 / 自定义）
- 策略权重：【按写作类型】
  - 通用检索：查全与查准均衡（A0/A1/B 全部交付，A1 为推荐起步）
  - 综述：查全优先（检索式以宽式 A 为主，候选按相关度+期刊质量排）
  - 研究论著：查准优先（精准式 B 为主，候选按相关度排）
  - 开题/基金：兼顾新颖性（时间窗含近 2 年，标注高被引与潜在空白）
  - 学位论文/调研报告：查全+查准均衡

## 三级关键词体系
- Tier 1（对象）：【继承自 Step 1】
- Tier 2（技术/方法）：【继承自 Step 1】
- Tier 3（应用/场景）：【继承自 Step 1】

## 排除项
- 强排除（可进入 `NOT`）：【继承自 Step 1 `strong_exclusions`】
- 弱排除（人工筛选提示）：【继承自 Step 1 `soft_exclusions`】
- 风险排除（默认不进入检索式）：【继承自 Step 1 `risky_exclusions`】
- 实际写入检索式的排除项：【继承自 Step 1 `query_exclusions`】

## 优先级规则
- 【继承自 Step 1】

## 确认记录
- G0 自动配置校验：【时间/`auto_passed`；不需要人工确认】
- G1 范围确认：【时间/内容】
- Search B 网络授权：【允许 / 拒绝；时间】（该操作授权不计入 G0–G2）
```

---

## 2. `query_pack.md` — 多平台检索式合集

```
# 多平台检索式合集

> 六库统一给出 A0（对象+必需技术召回基线）、A1（对象+必需技术+任务主题式）和 B（平台专属精准式）。A0 不加任务、排除项、年份或文献类型；排除从 A1 开始应用。IEEE 另保留 C（会议/出版物定向）、D1/D2（NEAR/ONEAR）和 E（综述导向）变体。
> 默认采用通用均衡策略；显式写作类型只调整推荐顺序和候选排序（见 scope_card.md）。
> 综述导向变体是补充查询，不是 review-only 限制；A0/A1 始终保留。

## Query QA
- 总体状态：`PASS / WARNING / FAIL`【继承自 Step 2 `_meta.query_qa`】
- 平台检查：括号、引号、字段语法、长度与 clause 限制【继承自 Step 2】
- 警告与修复记录：【继承自 Step 2】
- `FAIL` 不得进入最终交付。

## Web of Science
- 召回基线 A0（对象+必需技术）：【继承自 Step 2 Search A】
- 主题检索 A1（对象+必需技术+任务）：【继承自 Step 2 Search A】
- 精准检索 B（标题+NEAR）：【继承自 Step 2 Search A】
- 语法要点：

## Scopus
- 召回基线 A0：
- 主题检索 A1：
- 精准检索 B：

## IEEE Xplore
- 召回基线 A0（对象+技术，All Metadata）：
- 主题检索 A1（对象+技术+任务，All Metadata）：
- 标题核心检索 B（对象+技术）：
- 会议/出版物定向 C（有真实目标名称时）：
- 无序邻近 D1（NEAR）：
- 有序邻近 D2（ONEAR）：
- 综述导向 E：

## Google Scholar
- 召回基线 A0（每行独立执行，最多 6 条）：
- 主题检索 A1（每行独立执行，最多 6 条）：
- 精准检索 B：

## CNKI
- 召回基线 A0：
- 主题检索 A1：
- 精准检索 B：

## 万方
- 召回基线 A0：
- 主题检索 A1：
- 精准检索 B：

## 可调参数
- 时间策略：【继承自 Step 0；默认检索式不限年份，数据库界面提供近 10/5/2 年筛选预设】
- 截词/邻近算符使用说明：
```

---

## 3. `candidate_list.csv` / `.md` — 文献候选清单

```
# 文献候选清单

> [注意] 候选清单、非最终语料。元数据可能含虚构/错位，需用户在平台核对后自行下载。
> 来源：Search B API 收割（OpenAlex 主源）+ Crossref 按 DOI 逐条验证（title 相似度 >= 0.8 且年份差 <= 1），已验证条目去重。
> Search B status：【completed / skipped_by_user】。若为 `skipped_by_user`，说明用户未授权外部 API 访问，本文件不生成虚假的零结果统计。

## 统计
- OpenAlex 原始收割：【N】篇
- 合并去重后：【N】篇
- 去重移除：【N】篇
- 验证状态：verified（Crossref 验证通过）【n1】/ unverified（无 DOI 或瞬时错误）【n2】/ dropped（疑似幻觉/错配，已剔除）【n3】
- OA 状态：OA 【n4】/ 非OA 【n5】/ 未知 【n6】

## 清单（CSV 字段）
title, authors, journal, year, doi, doi_link, oa_status, source

## 排序
- 按【写作类型策略权重】：通用检索默认相关度；显式类型可改为相关度+期刊质量或新颖性
```

---

## 4. `usage_guide.md` — 使用说明

同时生成 `usage_guide.i18n.json`，提供以下使用说明完整正文的另一语言版本。平台名称、字段名、A0/A1/B 和检索语法保持原样。

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
- 召回基线 A0：约【N】篇（预估）
- 主题检索 A1：约【N】篇（预估）
- 精准检索 B：约【N】篇（预估）

## 调宽 / 调窄方法
- 调宽（增加结果）：去排除项 / 用 OR 连接同义词 / 放宽时间窗
- 调窄（减少结果）：加 AND / 用精确匹配双引号 / 缩小时间窗 / 限定字段

## 按写作类型的检索建议
- 通用检索：A1 作为推荐起步，A0 查漏，B 定位高相关文献；按需要切换近 10/5/2 年筛选
- 综述：先运行 A0 查漏，再以 A1 为主题主检索，最后用 B 快速定位高相关文献
- 研究论著：优先用查准式 B，聚焦核心方法
- 开题/基金：查准式 B + 近 2 年过滤，关注高被引与空白
- 学位论文/调研报告：从 A0 起步，按 A1、B 顺序调窄

## 候选清单使用
- 顶部 OA 文献可免费下载；非 OA 需机构权限
- DOI 链接可直接点击跳转
- 核对元数据后再下载（API 收割可能有误）

## 灰色文献与行业报告
- 默认提供独立检索模板，不与六库学术检索式或候选清单混合
- 只有用户明确要求时，才按政府、国际组织、行业协会或白皮书来源扩展
```
