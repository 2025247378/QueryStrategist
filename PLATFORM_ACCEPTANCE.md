# QueryStrategist 4.8.0 平台验收清单

本清单用于发布前的人工验收。单元测试只验证生成器和 API 处理逻辑，不能替代各平台官网的语法解析与命中量验证。

## 固定测试输入

使用一个同时具备对象层、必需技术锚点和任务层的英文测试范围，例如：

```json
{
  "tier1_species_object": ["farmed fish", "aquaculture fish"],
  "tier2_required_anchor": ["hyperspectral imaging", "multispectral imaging"],
  "tier2_supporting_method": ["machine learning", "texture feature extraction"],
  "tier3_application_task": ["freshness assessment", "size grading", "defect detection"],
  "explicit_exclusions": ["water quality monitoring", "pathogen detection"]
}
```

生成完整结果：

```powershell
python query_crafter/scripts/query_generator.py --scope scope.json --all --variants
```

## 验收表

| 平台 | 粘贴位置 | 必查规则 | 结果记录 |
|---|---|---|---|
| WoS | Advanced Search | `TS=`、`TI=`、`NEAR/10`、布尔括号 | 待人工填写 |
| Scopus | Advanced Search | `TITLE-ABS-KEY`、`TITLE`、`W/5` | 待人工填写 |
| IEEE Xplore | Advanced Search → Command Search | A0/A1/B/C/D1/D2/E、对象召回锚点、字段重复、`NEAR/10`、`ONEAR/10`、25-term；A0 为 0 时禁止继续叠加条件 | 待人工填写 |
| Google Scholar | 主搜索框 | 256 字符、短语引号、`OR`、互补查询无漏词 | 待人工填写 |
| CNKI | 高级检索/专业检索 | 中文字段、布尔运算符、题名/主题精准式 | 待人工填写 |
| 万方 | 高级检索/专业检索 | 字段选择、精确匹配、布尔逻辑 | 待人工填写 |

## Search B 验收

无网络的 CLI 参数验收：

```powershell
python literature_harvester/scripts/harvest.py `
  --species fish `
  --technology "spectral imaging" `
  --task freshness `
  --exclude disease `
  --dry-run
```

真实 API 验收时确认：

1. 未获得授权且未传 `--network-consent` 时，脚本立即拒绝执行，不发出网络请求。
2. 获得授权后的命令显式带 `--network-consent`，且同一次运行的子查询/Retry 不重复询问。
3. 三层参数同时存在时，请求使用三个 `title_and_abstract.search` 过滤器。
4. 排除词在标题和 inverted-index 摘要本地过滤。
5. 输出包含 `verified`、`unverified`、`dropped`、`is_oa`、`oa_status`。
6. 标准流程不传 `--mailto`；拒绝授权时 Search B 标记 `skipped_by_user`，Search A 仍可交付。

## 验收记录要求

每个平台至少记录：执行日期、账号/权限条件、查询变体、是否接受语法、命中量、错误信息和截图路径。发布前将“待人工填写”替换为实际结果，或明确标注未验收。
