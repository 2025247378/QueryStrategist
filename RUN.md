# RUN.md — QueryStrategist (Step 0–2) 运行入口

版本：v1.4.2（以根目录 VERSION 为准）

## 快速开始

1. **入口**：对任意支持 Skill 的 Agent 说「**开始文献检索**」或「**Start QueryStrategist**」。
2. **Step 0**：Setup Wizard 逐项配置写作类型（综述/研究论著/学位论文/开题报告/基金申请/调研报告/自定义）+ 目标语言 + 目标期刊 + 时间跨度 + 中文补充（G0 确认）。入口已提供研究方向时只记录并复用方向，不得代填其他配置或直接跳到 G0。
3. **Step 1**：Scope Definer 通过结构化提问收敛为三级关键词体系（对象层 + 必需技术锚点/支持方法 + 任务层）+ 中英文排除词分级 + 优先级（G1 确认）。只有确认的强排除进入 `NOT`。
4. **Step 2**：Search Strategist V1 双通道 —— Search A（六库 A0/A1/B 与 Query QA，`FAIL` 必须修复）+ Search B（联网授权后执行 2-3 个 OpenAlex 梯度查询，每个 20-25 条，合并去重后再由 Crossref 验证）→ 交付**检索策略包**。拒绝联网授权时只跳过 Search B。默认目录为 `projects/<active_project_id>/deliverables/`，默认只在聊天展示摘要，并优先打开唯一入口 `index.html`；审计模式才完整展开。

## 目录清单

```
QueryStrategist/
├── README.md                    # 提交文档
├── RUN.md                       # 本文件
├── LICENSE                      # MIT
├── VERSION                      # 当前正式版本
├── BUILD_MANIFEST.json          # 发布文件完整性清单
├── SKILL.md                     # 主 Skill（Step 0–2 状态机入口，唯一 SKILL.md）
├── setup_wizard/                # Step 0（指令: SKILL.sub.md）
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
└── _shared_tools/               # 运行与校验脚本
```

## 关键脚本（Skill 内 `scripts/`）

| Skill | 脚本 | 用途 |
|:--|:--|:--|
| `literature_harvester` | `harvest.py` | 两源 API 收割 + Crossref 逐条验证（去幻觉；含联网授权与配额守卫） |
| `query_crafter` | `query_generator.py` | 多平台检索式批量生成 |
| `_shared_tools` | `ensure_tool.py` | 开源工具检测/隔离安装（清华镜像直连） |
| `_shared_tools` | `validate_skills.py` | 套件自校验（frontmatter 合规检查；路径自动推导，可在发布包内直接运行） |
| `_shared_tools` | `validate_pipeline_state.py` | 项目配置与流水线状态结构校验 |
| `_shared_tools` | `render_deliverables.py` | Markdown/CSV 编码规范化并生成离线 HTML |

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
