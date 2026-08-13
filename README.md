# QueryStrategist（文献检索策略师）

> QueryStrategist（文献检索策略师）是一款面向科研人员的交互式文献检索 Skill。你只需提供研究方向，它会通过结构化提问明确研究对象、技术方法、任务指标和排除范围，生成适用于 Web of Science、Scopus、IEEE Xplore、Google Scholar、CNKI 和万方的可复制高级检索式。经授权后，还可通过 OpenAlex 收集候选文献，并使用 Crossref 核验 DOI。最终交付范围卡、六库检索式、候选文献清单和使用说明，适用于综述、论文、学位论文、开题报告和基金申请。
>
> **版本**：v1.3.1（2026-08-13）

---

## 1. 解决的问题

各类文献写作的检索起步阶段有三大痛点，本套件（Step 0–2）精准覆盖：

1. **意图模糊难转检索式**：从"我想研究 X 在 Y 中的应用"到可执行的高级检索式，跨度大、靠人工拼关键词易漏易滥（Step 1 Scope Definer）。
2. **跨库检索式构建重复**：WoS / Scopus / IEEE / Google Scholar / CNKI / 万方 6 库语法各异，逐库构建耗时数天（Step 2 Search Strategist V1 · Search A）。
3. **检索策略缺依据**：候选文献常凭经验筛，缺少跨库收割的量化覆盖与 OA 状态佐证（Step 2 Search Strategist V1 · Search B）。

本套件用**人机协作（human-in-the-loop）**回应：AI 承担规模化执行（关键词收敛、检索式生成、跨库收割），人类在关键决策门拍板（配置 G0 / 范围 G1 / 检索策略交付 G2），最终交付**可复制粘贴的检索策略包**。

---

## 2. 方案概述

流水线由状态机主控（根 `SKILL.md`，即主 Skill / 编排器）按 **Step 0–2** 顺序串联 3 个子模块，每步结束设强制人工确认门（G0–G2）。本仓库采用可直接发布的单包结构：根 `SKILL.md` 是唯一入口，11 个子模块以 `SKILL.sub.md` 保存并由主 Skill 读取执行。

| Step | 子 Skill | 关键产出 | 主导方 |
|:--:|:--|:--|:--:|
| 0 | Setup Wizard | 项目配置 + 写作类型 + 目标语言/期刊 + 时间跨度 | 人机协作 |
| 1 | Scope Definer | 三级关键词体系 + 排除项 + 优先级 | 人机协作 |
| 2 | Search Strategist V1 | 6 库检索式（查全 A + 查准 B）+ API 自动收割（OpenAlex 收割 + Crossref 按 DOI 逐条验证去幻觉） | AI 主导 |

**本提交终点 = Step 2 后的「检索策略包」**：范围界定卡 + 多平台检索式合集 + 文献候选清单 + 使用说明。它诚实交付「AI 最擅长的检索策略生成」，把写作决策留给研究者。

---

## 3. 核心设计

1. **意图 → 策略的结构化转化**：Scope Definer 通过结构化提问把模糊研究方向收敛为「对象层 + 必需技术锚点/支持方法 + 任务层 + 排除词分级」，并为中文数据库保留独立中文词表，再机械化为 6 库高级检索式。宽泛排除词默认降级为人工筛选提示，避免 `NOT` 误杀。
2. **按写作类型调策略权重**：综述查全优先、研究论著查准优先、开题/基金兼顾新颖性，不同写作类型对应不同的检索式版本与候选清单排序——LLM 比数据库自带 Query Builder 强的地方。
3. **双通道检索**：Search A 产出可手填的 6 库检索式；Search B 在用户明确授权后调用公开 API 自动收割元数据，两条通道互为校验。拒绝联网授权时 Search A 仍正常交付。
4. **人机闸门（负责任 AI）**：3 个强制决策门（G0–G2），AI 只呈客观事实与策略，范围与检索策略确认始终由人类掌握。
5. **零密钥、需授权、去幻觉的 API 收割**：联网前只请求一次授权，说明将访问 `api.openalex.org` 与 `api.crossref.org`；不下载全文，标准流程使用 Crossref 匿名公共池且不提交个人信息。验证不通过的疑似幻觉/错配条目标记 `dropped` 剔除。
6. **API 配额守卫（MANDATORY）**：收割脚本内置分端点请求预算、429 熔断、Retry-After 上限、响应缓存、dry-run 与失败统计。
7. **受控梯度收割与先去重后验证**：Search B 默认执行 2-3 个 OpenAlex 梯度查询，每个 20-25 条；合并后按 DOI 或标题+年份去重，再对唯一 DOI 调用 Crossref。结果不足时由用户决定是否追加一次扩展查询。
8. **六库 Query QA**：统一检查括号、引号、平台字段、Google Scholar 长度、IEEE clause、宽泛排除词、技术锚点与 review-only 风险，输出 `PASS/WARNING/FAIL`；`FAIL` 阻断交付。

---

## 4. 交付物（检索策略包）

流程终点（G2 确认后）产出**检索策略包**，默认落盘于 `projects/<active_project_id>/deliverables/`；用户已提供路径时直接使用。标准模板见 `search_strategist_v1/assets/search_strategy_pack_template.md`：

- **`index.html` — 唯一默认阅读入口**：统一导航到范围卡、检索式、候选文献和使用说明；无需安装软件，可离线打开。其他文件作为导出和审计备份保留。

- **`scope_card.md/.html` — 范围界定卡**：三级关键词体系（Tier1 对象 / Tier2 必需技术锚点与支持方法 / Tier3 任务）+ 中英文排除词分级 + 写作类型 + 策略权重（查全/查准/新颖性）。
- **`query_pack.md/.html` — 多平台检索式合集**：6 库高级检索式和 Query QA 摘要，每库给 A0（对象+必需技术召回基线）、A1（三层主题式）和 B（平台专属精准式）；综述导向变体仅作补充，不把整体策略限制为 review-only。
- **`candidate_list.csv/.md/.html` — 文献候选清单**：API 收割去重元数据（标题/作者/期刊/年份/DOI）+ OA 状态 + 可点击 DOI 链接 + 来源标注；CSV 和 Markdown 使用 UTF-8 BOM，便于 Windows 和 Excel 直接打开。
- **`usage_guide.md/.html` — 使用说明**：每个检索式填入哪个平台的哪个输入框、预期命中量级、如何调宽/调窄、按写作类型的检索建议。

> **检索策略包继承上游上下文**：所有内容均收敛自 Step 0–2 的真实选择（写作类型配置 → 范围界定 → 检索与收割 → 门控确认），禁止凭空生成；每个字段标注上游出处（`【继承自 …】`），无出处条目标记【待补】并向用户确认。详情见模板文件第 0 节「上游上下文继承总纲」。

---

## 5. 使用方式

- **完整流程**：调用根 `SKILL.md`（主 Skill），Step 0 逐项配置写作类型与目标语言/期刊；入口已提供研究方向时只记录并复用该方向，不代填其他配置。Step 1 收敛范围（G1 确认），Step 2 在 Search B 联网前请求一次授权，再执行双通道检索并交付检索策略包（G2 确认）。拒绝授权时只跳过 Search B，Search A 与策略包继续。
- **直接模式**：可只生成六库 Search A、只生成某个平台，或调宽/调窄已有检索式。直接模式只询问生成所需的最小范围信息，不执行完整 G0–G2，不访问 OpenAlex/Crossref；各子模块仍由根 `SKILL.md` 按入口路由规则读取执行。

---

## 6. 目录结构（本提交）

```
QueryStrategist/
├── LICENSE                                  # MIT
├── VERSION                                  # 当前正式版本
├── BUILD_MANIFEST.json                      # 发布文件完整性清单
├── README.md                                # 本文件
├── RUN.md                                   # 运行入口与代码清单
├── SKILL.md                                 # 主 Skill（编排器根入口）
├── setup_wizard/                            # Step 0  写作类型 + 配置（指令: SKILL.sub.md）
├── scope_definer/                           # Step 1  三级关键词 + 排除项
├── search_strategist_v1/                    # Step 2  双通道检索（终点）
├── query_crafter/                           # 检索式总控（6 平台）
├── wos_query_crafter/                       # Web of Science
├── scopus_query_crafter/                    # Scopus
├── ieee_query_crafter/                      # IEEE Xplore
├── google_scholar_query_crafter/            # Google Scholar
├── cnki_query_crafter/                      # 中国知网（中文补充）
├── wanfang_query_crafter/                   # 万方（中文补充）
├── literature_harvester/                    # API 收割 + 验证（OpenAlex 收割 / Crossref 逐条验证）
└── _shared_tools/                           # 运行与校验脚本
```

> `E:\QueryStrategist` 是唯一正式仓库和唯一发布源。GitHub、比赛源码包与后续 SCP 上架均应取自同一版本的本目录，不再生成或维护第二份发布副本。SCP 页面正文以根 `SKILL.md` 为来源；`README.md` 面向 GitHub 用户和比赛评审说明项目结构、运行方式与边界。正式发布内容不包含测试目录、测试数据或 Python 缓存。

---

## 7. 工具与依赖

| 工具 / 库 | 用途 | 许可证 |
|---|---|---|
| 内置 LLM Agent | 全流程推理 | — |
| openpyxl | 表格导出 | MIT |
| SJR 数据集 | 期刊质量评分（策展映射；不随仓库分发） | CC BY-NC 4.0 |
| OpenAlex API | 文献元数据收割（主源，无 key） | 各自服务条款 |
| Crossref REST API | 按 DOI 逐条验证（title/year 一致性） | Crossref 服务条款 |

---

## 8. 第三方能力与出处声明

- **OpenAlex / Crossref**：`literature_harvester` 获得用户授权后访问 `api.openalex.org` 收割文献元数据，并访问 `api.crossref.org` 按 DOI 逐条回查验证。两者均无需申请密钥；标准流程不下载全文、不提交个人信息。
- **SJR 期刊数据集**：来源于 SCImago，许可证 CC BY-NC 4.0（不可商用），故不随本仓库分发；本套件对语料内期刊使用**策展四分位映射**（透明、可核）。

---

## 9. 局限与展望

- **交付闭环**：本工具交付「可追溯的检索策略包」——研究者可直接把检索式填入各平台、按候选清单下载文献；所有检索策略均绑定真实范围界定与收割记录。
- **收割 ≠ 语料**：API 收割的元数据仅作候选清单，绝不自动进入下游当作全文语料；需用户自行下载验证。
- **检索策略需平台验证**：检索式命中量级为预估，最终以各数据库实际检索结果为准；AI 不替用户做纳入决定。
- **发布前验收**：自动校验不替代真实平台验证；正式使用前仍需在 WoS、Scopus、IEEE Xplore、Google Scholar、CNKI、万方官网分别粘贴检索式，确认语法解析和命中量符合预期。
- **阅读兼容性**：最终 Markdown/CSV 统一为 UTF-8 BOM，并生成内嵌样式的离线 HTML。建议普通阅读优先打开 `.html`，需要编辑或复用时再打开 `.md`。
- **交互体验**：检索式页面支持六库标签页与一键复制；候选清单支持本地搜索、验证状态/OA/年份筛选和表头排序；所有功能均无 CDN、无外部网络依赖，关闭 JavaScript 后原始内容仍完整可读。
- **当前边界**：本版本已经包含按写作类型调节检索策略权重；后续扩展仍须坚守「收割 ≠ 语料」与「人类把关」两条红线。

---

## 10. 许可证

本套件 Skill 源码以 **MIT** 授权（见 `LICENSE`）。外部依赖与数据文件的许可证见第 7、8 节；SJR 为 CC BY-NC 4.0（不可商用），不随仓库分发。
