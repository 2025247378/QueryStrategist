# RUN.md — QueryStrategist (Step 0–2) 运行入口

版本：4.7.0（以根目录 VERSION 为准）

## 快速开始

1. **入口**：对任意支持 Skill 的 Agent 说「**开始文献检索**」或「**Start QueryStrategist**」。
2. **Step 0**：Setup Wizard 配置写作类型（综述/研究论著/学位论文/开题报告/基金申请/调研报告/自定义）+ 目标语言 + 目标期刊 + 时间跨度 + 中文补充（G0 确认）。
3. **Step 1**：Scope Definer 通过结构化提问收敛为三级关键词体系（对象层 + 必需技术锚点/支持方法 + 任务层）+ 中英文排除项 + 优先级（G1 确认）。
4. **Step 2**：Search Strategist V1 双通道 —— Search A（Query Crafter 生成 6 平台检索式，每库查全式 A + 查准式 B；IEEE 另含 C/D1/D2/E 变体）+ Search B（Literature Harvester 使用对象/技术/任务三层过滤收割候选清单）→ 交付**检索策略包**。默认打开 `index.html`；检索式页面支持平台标签页和复制，候选清单支持搜索、筛选、排序。每份 Markdown 同步生成离线 HTML，CSV/Markdown 使用 UTF-8 BOM。检索策略包全部继承 Step 0–2 的上游选择与门控记录，模板见 `search_strategist_v1/assets/search_strategy_pack_template.md`（G2 确认）。

## 目录清单

```
QueryStrategist/
├── README.md                    # 提交文档
├── RUN.md                       # 本文件
├── LICENSE                      # MIT
├── SKILL.md                     # 主 Skill（Step 0–2 状态机入口，唯一 SKILL.md）
├── setup_wizard/                # Step 0（指令: SKILL.md）
├── scope_definer/               # Step 1
├── search_strategist_v1/        # Step 2（终点）
├── query_crafter/               # 检索式总控（6 平台）
├── wos_query_crafter/           # Web of Science
├── scopus_query_crafter/        # Scopus
├── ieee_query_crafter/          # IEEE Xplore
├── google_scholar_query_crafter/   # Google Scholar
├── cnki_query_crafter/          # 中国知网（中文补充）
├── wanfang_query_crafter/       # 万方（中文补充）
├── literature_harvester/        # API 收割 + 验证（OpenAlex 收割 / Crossref 逐条验证）
└── _shared_tools/               # 共享工具安装器
```

> 开发仓库为本地安装形态；运行 `python _shared_tools/scripts/build_scp_package.py --destination <以 _SCP 结尾的发布目录> --force` 可显式覆盖重建 SCP 单包形态。发布目录只保留一个根包，并生成 `BUILD_MANIFEST.json`。

## 关键脚本（Skill 内 `scripts/`）

| Skill | 脚本 | 用途 |
|:--|:--|:--|
| `literature_harvester` | `harvest.py` | 两源 API 收割 + Crossref 逐条验证（去幻觉；含配额守卫） |
| `query_crafter` | `query_generator.py` | 多平台检索式批量生成 |
| `_shared_tools` | `ensure_tool.py` | 开源工具检测/隔离安装（清华镜像直连） |
| `_shared_tools` | `validate_skills.py` | 套件自校验（frontmatter 合规检查；路径自动推导，可在发布包内直接运行） |
| `_shared_tools` | `validate_pipeline_state.py` | 项目配置与流水线状态结构校验 |
| `_shared_tools` | `render_deliverables.py` | Markdown/CSV 编码规范化并生成离线 HTML |
| `_shared_tools` | `build_ppt.py` | 参赛 PPT 生成（依赖 python-pptx；支持 `--output`） |
| `_shared_tools` | `build_scp_package.py` | 从开发源确定性重建 SCP 单包 |

## 依赖安装

- **Python**：系统 Anaconda 或托管 Python 均可。
- **第三方包**：经 `_shared_tools/scripts/ensure_tool.py` 自动安装（先检测后安装、`--target` 隔离、镜像直连），**不要手动 `python -m venv` + `pip install`**（本环境沙箱会回滚 venv 写入）。

## 外部 API（需外网，建议直连）

- 运行收割脚本前如设置了代理环境变量，建议 `unset HTTP_PROXY HTTPS_PROXY` 走直连，避免代理不可用时导致连接失败。
- 收割脚本已内置 **API 配额守卫**：OpenAlex 默认 120 次、Crossref 默认 60 次请求预算；连续 3 次 429 熔断，Retry-After 最多等待 20 秒，按请求参数缓存响应，支持 `--dry-run`、`--min-year`、`--max-year`。预算可通过 `--openalex-budget` / `--crossref-budget` 或环境变量覆盖。

## 已知边界

- **收割 ≠ 语料**：API 收割的元数据仅作候选下载清单，绝不自动进入下游当作全文语料；需用户自行下载验证。
- **检索策略需平台验证**：检索式命中量级为预估，最终以各数据库实际检索结果为准。
- **决策门**：G0–G2 为强制人工确认点，AI 不替人类做范围与检索策略的最终决定。
- **项目状态校验**：对具体项目运行 `python _shared_tools/scripts/validate_pipeline_state.py --project projects/<id>`，确认 `project_meta.json`、`pipeline_state/config.json` 和结构化年份字段完整。
