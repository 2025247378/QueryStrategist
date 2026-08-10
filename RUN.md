# RUN.md — QueryStrategist (Step 0–2) 运行入口

## 快速开始

1. **入口**：对任意支持 Skill 的 Agent 说「**开始文献检索**」或「**Start QueryStrategist**」。
2. **Step 0**：Setup Wizard 配置写作类型（综述/研究论著/学位论文/开题报告/基金申请/调研报告/自定义）+ 目标语言 + 目标期刊 + 时间跨度 + 中文补充（G0 确认）。
3. **Step 1**：Scope Definer 通过结构化提问收敛为三级关键词体系 + 排除项 + 优先级（G1 确认）。
4. **Step 2**：Search Strategist V1 双通道 —— Search A（Query Crafter 生成 6 平台检索式，每库查全式 A + 查准式 B）+ Search B（Literature Harvester API 收割候选清单）→ 交付**检索策略包**（最终成果）：`scope_card.md`（范围卡）+ `query_pack.md`（检索式合集）+ `candidate_list.csv/.md`（文献候选清单）+ `usage_guide.md`（使用说明）。检索策略包全部继承 Step 0–2 的上游选择与门控记录，模板见 `search_strategist_v1/assets/search_strategy_pack_template.md`（G2 确认）。

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

> 本提交形态：**本地安装形态**——子模块指令文件为 `SKILL.md`，每个子模块可被注册为独立 Skill；主 Skill 按「子模块执行机制」读取执行。若需 Skills 广场单包上架形态（整个目录作为一个 Skill 上传，子模块为 `SKILL.sub.md`），见 `E:\QueryStrategist_SCP` 与 `build_scp_package.py`。

## 关键脚本（Skill 内 `scripts/`）

| Skill | 脚本 | 用途 |
|:--|:--|:--|
| `literature_harvester` | `harvest.py` | 两源 API 收割 + Crossref 逐条验证（去幻觉；含配额守卫） |
| `query_crafter` | `query_generator.py` | 多平台检索式批量生成 |
| `_shared_tools` | `ensure_tool.py` | 开源工具检测/隔离安装（清华镜像直连） |
| `_shared_tools` | `validate_skills.py` | 套件自校验（frontmatter 合规检查；路径自动推导，可在发布包内直接运行） |
| `_shared_tools` | `build_ppt.py` | 参赛 PPT 生成（依赖 python-pptx） |

## 依赖安装

- **Python**：系统 Anaconda 或托管 Python 均可。
- **第三方包**：经 `_shared_tools/scripts/ensure_tool.py` 自动安装（先检测后安装、`--target` 隔离、镜像直连），**不要手动 `python -m venv` + `pip install`**（本环境沙箱会回滚 venv 写入）。

## 外部 API（需外网，建议直连）

- 运行收割脚本前如设置了代理环境变量，建议 `unset HTTP_PROXY HTTPS_PROXY` 走直连，避免代理不可用时导致连接失败。
- 收割脚本已内置 **API 配额守卫**：请求预算、429 熔断、Retry-After 上限（≤20s）、响应缓存、逐通路落盘、`--dry-run` 冒烟测试。命中配额优雅停止并保存部分结果。

## 已知边界

- **收割 ≠ 语料**：API 收割的元数据仅作候选下载清单，绝不自动进入下游当作全文语料；需用户自行下载验证。
- **检索策略需平台验证**：检索式命中量级为预估，最终以各数据库实际检索结果为准。
- **决策门**：G0–G2 为强制人工确认点，AI 不替人类做范围与检索策略的最终决定。
