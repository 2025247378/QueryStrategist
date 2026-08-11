# QueryStrategist · 智能文献检索策略生成器（Step 0–2）

> **定位**：基于 LLM 的交互式文献检索系统，通过结构化提问把模糊科研意图转化为高精度专业检索策略。面向综述、研究论著、学位论文、开题报告、基金申请、调研报告等各类文献写作场景。
> **核心价值**：一句话模糊意图 → 6 大数据库精准检索式 + API 收割的文献候选清单，即拿即用。不是帮你搜，是帮你把「搜的策略」做对。
> **版本**：4.6.0（2026-08-11）

---

## 1. 解决的问题

各类文献写作的检索起步阶段有三大痛点，本套件（Step 0–2）精准覆盖：

1. **意图模糊难转检索式**：从"我想研究 X 在 Y 中的应用"到可执行的高级检索式，跨度大、靠人工拼关键词易漏易滥（Step 1 Scope Definer）。
2. **跨库检索式构建重复**：WoS / Scopus / IEEE / Google Scholar / CNKI / 万方 6 库语法各异，逐库构建耗时数天（Step 2 Search Strategist V1 · Search A）。
3. **检索策略缺依据**：候选文献常凭经验筛，缺少跨库收割的量化覆盖与 OA 状态佐证（Step 2 Search Strategist V1 · Search B）。

本套件用**人机协作（human-in-the-loop）**回应：AI 承担规模化执行（关键词收敛、检索式生成、跨库收割），人类在关键决策门拍板（配置 G0 / 范围 G1 / 检索策略交付 G2），最终交付**可复制粘贴的检索策略包**。

---

## 2. 方案概述

流水线由状态机主控（根 `SKILL.md`，即主 Skill / 编排器）按 **Step 0–2** 顺序串联 3 个子模块，每步结束设强制人工确认门（G0–G2）。开发仓库使用本地安装形态（子模块为 `SKILL.md`）；`build_scp_package.py` 会生成 SCP 单包形态（根入口保留 `SKILL.md`，子模块转换为 `SKILL.sub.md`）。

| Step | 子 Skill | 关键产出 | 主导方 |
|:--:|:--|:--|:--:|
| 0 | Setup Wizard | 项目配置 + 写作类型 + 目标语言/期刊 + 时间跨度 | 人机协作 |
| 1 | Scope Definer | 三级关键词体系 + 排除项 + 优先级 | 人机协作 |
| 2 | Search Strategist V1 | 6 库检索式（查全 A + 查准 B）+ API 自动收割（OpenAlex 收割 + Crossref 按 DOI 逐条验证去幻觉） | AI 主导 |

**本提交终点 = Step 2 后的「检索策略包」**：范围界定卡 + 多平台检索式合集 + 文献候选清单 + 使用说明。它诚实交付「AI 最擅长的检索策略生成」，把写作决策留给研究者。

---

## 3. 核心设计

1. **意图 → 策略的结构化转化**：Scope Definer 通过结构化提问把模糊研究方向收敛为「对象层 + 必需技术锚点/支持方法 + 任务层 + 排除项」，并为中文数据库保留独立中文词表，再机械化为 6 库高级检索式——杜绝靠直觉拼关键词。
2. **按写作类型调策略权重**：综述查全优先、研究论著查准优先、开题/基金兼顾新颖性，不同写作类型对应不同的检索式版本与候选清单排序——LLM 比数据库自带 Query Builder 强的地方。
3. **双通道检索**：Search A 产出可手填的 6 库检索式，Search B 调公开 API 自动收割元数据，两条通道互为校验。
4. **人机闸门（负责任 AI）**：3 个强制决策门（G0–G2），AI 只呈客观事实与策略，范围与检索策略确认始终由人类掌握。
5. **零密钥、去幻觉的 API 收割**：Literature Harvester 以 **OpenAlex 为唯一收割源**（无 key），**Crossref 按 DOI 逐条回查验证**（title 相似度≥0.8 且年份差≤1），验证不通过的疑似幻觉/错配条目直接标记 `dropped` 剔除，从机制上杜绝 AI 编造文献混入候选清单。
6. **API 配额守卫（MANDATORY）**：收割脚本内置分端点请求预算、429 熔断、Retry-After 上限、响应缓存、dry-run 与失败统计。
7. **跨源去重与相关性护栏**：收割层做跨库元数据归一、DOI 去重；高噪声语料按领域相关词过滤，显著提升信噪比。

---

## 4. 交付物（检索策略包）

流程终点（G2 确认后）产出**检索策略包**，全部落盘于 `projects/<id>/`，标准模板见 `search_strategist_v1/assets/search_strategy_pack_template.md`：

- **`scope_card.md/.html` — 范围界定卡**：三级关键词体系（Tier1 对象 / Tier2 必需技术锚点与支持方法 / Tier3 任务）+ 中英文排除项 + 写作类型 + 策略权重（查全/查准/新颖性）。
- **`query_pack.md/.html` — 多平台检索式合集**：6 库高级检索式，每库给「查全式 A + 平台专属查准式 B」双版本；IEEE 另保留会议定向、NEAR/ONEAR 邻近和综述导向变体（C/D1/D2/E）。检索式使用代码块保存，HTML 渲染不改写其内容。
- **`candidate_list.csv/.md/.html` — 文献候选清单**：API 收割去重元数据（标题/作者/期刊/年份/DOI）+ OA 状态 + 可点击 DOI 链接 + 来源标注；CSV 和 Markdown 使用 UTF-8 BOM，便于 Windows 和 Excel 直接打开。
- **`usage_guide.md/.html` — 使用说明**：每个检索式填入哪个平台的哪个输入框、预期命中量级、如何调宽/调窄、按写作类型的检索建议。

> **检索策略包继承上游上下文**：所有内容均收敛自 Step 0–2 的真实选择（写作类型配置 → 范围界定 → 检索与收割 → 门控确认），禁止凭空生成；每个字段标注上游出处（`【继承自 …】`），无出处条目标记【待补】并向用户确认。详情见模板文件第 0 节「上游上下文继承总纲」。

---

## 5. 使用方式

- **完整流程**：调用根 `SKILL.md`（主 Skill），Step 0 先配置写作类型与目标语言/期刊，Step 1 收敛范围（G1 确认），Step 2 双通道检索并交付检索策略包（G2 确认）。子模块按「读取 `SKILL.md` → 执行」机制调用（SCP 单包形态下为 `SKILL.sub.md`）。
- **单步使用**：任一子模块可单独执行（如直接要某数据库检索式，读取对应 `xxx_query_crafter/SKILL.md` 执行；只做范围界定，直接读 `scope_definer/SKILL.md`）。子模块均可作为独立 Skill 被直接调用。

---

## 6. 目录结构（本提交）

```
QueryStrategist/
├── LICENSE                                  # MIT
├── README.md                                # 本文件
├── RUN.md                                   # 运行入口与代码清单
├── SKILL.md                                 # 主 Skill（编排器根入口）
├── setup_wizard/                            # Step 0  写作类型 + 配置（指令: SKILL.md）
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
└── _shared_tools/                           # 共享工具（ensure_tool.py / validate_skills.py / build_ppt.py）
```

> 每个子模块目录均含 `SKILL.md`（本地安装形态，可直接注册为独立 Skill）及所需资源。SCP 发布包由 `python _shared_tools/scripts/build_scp_package.py --destination <以 _SCP 结尾的发布目录> --force` 显式覆盖生成；构建结果包含 `BUILD_MANIFEST.json`，不再手工同步副本。

---

## 7. 工具与依赖

| 工具 / 库 | 用途 | 许可证 |
|---|---|---|
| 内置 LLM Agent | 全流程推理 | — |
| python-pptx | 生成功能介绍 PPT（`_shared_tools/scripts/build_ppt.py`） | MIT |
| openpyxl | 表格导出 | MIT |
| SJR 数据集 | 期刊质量评分（策展映射；不随仓库分发） | CC BY-NC 4.0 |
| OpenAlex API | 文献元数据收割（主源，无 key） | 各自服务条款 |
| Crossref REST API | 按 DOI 逐条验证（title/year 一致性） | Crossref 服务条款 |

---

## 8. 第三方能力与出处声明

- **OpenAlex / Crossref**：`literature_harvester` 使用 OpenAlex 开放 API 收割文献元数据（主源，无需 key），并用 Crossref REST API 按 DOI 逐条回查验证（title 相似度≥0.8 且年份差≤1）。两者均为开放学术 API，无需申请密钥；验证层用于剔除 AI 幻觉/错配条目，落实「收割 ≠ 语料」红线。
- **SJR 期刊数据集**：来源于 SCImago，许可证 CC BY-NC 4.0（不可商用），故不随本仓库分发；本套件对语料内期刊使用**策展四分位映射**（透明、可核）。

---

## 9. 局限与展望

- **交付闭环**：本工具交付「可追溯的检索策略包」——研究者可直接把检索式填入各平台、按候选清单下载文献；所有检索策略均绑定真实范围界定与收割记录。
- **收割 ≠ 语料**：API 收割的元数据仅作候选清单，绝不自动进入下游当作全文语料；需用户自行下载验证。
- **检索策略需平台验证**：检索式命中量级为预估，最终以各数据库实际检索结果为准；AI 不替用户做纳入决定。
- **发布前验收**：真实平台语法验收清单见 `PLATFORM_ACCEPTANCE.md`；脚本单元测试不替代在 WoS、Scopus、IEEE Xplore、Google Scholar、CNKI、万方官网中的粘贴验证。
- **阅读兼容性**：最终 Markdown/CSV 统一为 UTF-8 BOM，并生成内嵌样式的离线 HTML。建议普通阅读优先打开 `.html`，需要编辑或复用时再打开 `.md`。
- **当前边界**：本版本已经包含按写作类型调节检索策略权重；后续扩展仍须坚守「收割 ≠ 语料」与「人类把关」两条红线。

---

## 10. 许可证

本套件 Skill 源码以 **MIT** 授权（见 `LICENSE`）。外部依赖与数据文件的许可证见第 7、8 节；SJR 为 CC BY-NC 4.0（不可商用），不随仓库分发。
