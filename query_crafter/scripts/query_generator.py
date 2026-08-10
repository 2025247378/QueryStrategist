"""
query_generator.py — QueryStrategist · 多平台检索式生成器
=========================================================
把 Scope Definer 产出的三级关键词体系 (tier1 对象 / tier2 技术 / tier3 应用)
+ 排除项，机械化为 6 大数据库的高级检索式。

用法:
    # 从 scope JSON 生成全部平台检索式
    python query_generator.py --scope scope.json --all

    # 只生成 WoS
    python query_generator.py --scope scope.json --platforms wos

    # 直接从命令行给关键词
    python query_generator.py --t1 "organ-on-a-chip" --t2 "microfluidics" --ex "diagnosis"

scope.json 结构:
    {
      "keyword_tiers": {
        "tier1_species_object": ["organ-on-a-chip", "microfluidic organoid"],
        "tier2_technology_method": ["microfluidics", "3D bioprinting"],
        "tier3_application_task": ["drug toxicity screening"]
      },
      "explicit_exclusions": ["disease diagnosis", "in vivo animal"]
    }

输出: JSON {platform: query_string}（generate，单条宽泛式，向后兼容）。
      --variants 时输出 {platform: [{variant,label,query}, ...]} 分层组合（宽泛/精准/多角度）。
"""
import argparse
import json
import sys


def _join_terms(terms, op=" OR "):
    """同层关键词用 OR 连接，并加引号。"""
    terms = [t.strip() for t in terms if t.strip()]
    return " OR ".join(f'"{t}"' for t in terms)


def _tier(tiers, key, fallback=""):
    return tiers.get(key, []) or tiers.get(fallback, [])


# ---------- 排除项英文化映射（中文描述 -> 英文检索片段）----------
# 适用：英文数据库（WoS/Scopus/IEEE/Google Scholar）不能出现非 ASCII 排除词，
# 否则 WoS 会原样搜索该中文字符串 -> 0 命中 -> 排除失效且含全角括号等脏字符。
# 这里把 scope 里常见的中文排除描述映射到等价的英文布尔片段。
EXCLUSION_EN_MAP = {
    "非视觉投喂法（声学、RFID、称重等）": 'acoustic* OR RFID OR "weighing" OR "load cell" OR "feeding station"',
    "非投喂水产应用（病害检测、水质监测、计数等）": '"disease detection" OR "water quality" OR counting OR "stock assessment"',
    "非水产投喂（畜禽、大田农业等）": 'livestock OR poultry OR "precision agriculture" OR crop',
    "纯硬件制造（摄像头/传感器硬件设计与制造）": '"sensor manufacturing" OR "camera hardware" OR "hardware design"',
    # 短键（子串匹配兜底）
    "非视觉投喂法": 'acoustic* OR RFID OR "weighing" OR "load cell"',
    "非投喂水产应用": '"disease detection" OR "water quality" OR counting',
    "非水产投喂": 'livestock OR poultry OR "precision agriculture"',
    "纯硬件制造": '"sensor manufacturing" OR "camera hardware" OR "hardware design"',
}


def _is_ascii(s):
    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def _translate_exclusion(e):
    e = (e or "").strip()
    if e in EXCLUSION_EN_MAP:
        return EXCLUSION_EN_MAP[e]
    for k, v in EXCLUSION_EN_MAP.items():
        if k in e:
            return v
    return None


def _guard_exclusions(exclusions, warnings, platform, allow_cjk=False):
    """英文库过滤非 ASCII 排除词（翻译或跳过并告警）；中文库 allow_cjk=True 保留原样。"""
    kept, skipped = [], []
    for e in exclusions:
        e = (e or "").strip()
        if not e:
            continue
        if _is_ascii(e):
            kept.append(e)
        elif allow_cjk:
            kept.append(e)
        else:
            tr = _translate_exclusion(e)
            if tr:
                kept.append(tr)
            else:
                skipped.append(e)
    if skipped and warnings is not None:
        warnings.append((platform, skipped))
    return kept


def _fmt_excl_terms(terms):
    """排除词 -> OR 连接的布尔表达式（含 OR/AND 的片段已是完整布尔式，原样嵌入；单短语加引号）。"""
    out = []
    for t in terms:
        t = t.strip()
        if not t:
            continue
        if any(op in t.upper() for op in (" OR ", " AND ", " NOT ")):
            out.append(t)  # OR/AND 片段：已是引号平衡的完整布尔式，原样保留
        else:
            # 单短语：若整体被引号包裹则先去包裹再重新加（避免双引号），否则直接加引号
            if t.startswith('"') and t.endswith('"'):
                t = t[1:-1].strip()
            out.append(f'"{t}"')
    return " OR ".join(out)


# ---------- 各平台语法构建器 ----------
# Search A 默认 broad=True：高召回 —— 必含领域层(tier1) 且 (技术层 OR 应用层)，
# 不强制三层全命中，避免过窄。broad=False 时三层全 AND（精准检索 Search B 用）。

_TIER_KEYS = ["tier1_species_object", "tier1", "tier2_technology_method",
              "tier2", "tier3_application_task", "tier3"]


def _tier_groups(tiers):
    """把三层关键词各自 OR 成组，返回非空组列表。"""
    groups = []
    for k in _TIER_KEYS:
        j = _join_terms(tiers.get(k, []))
        if j:
            groups.append(j)
    return groups


def _broad_and(groups, wrap):
    """宽检索结构：wrap(g0) AND (wrap(g1) OR wrap(g2) ...)；单组则直接 wrap。"""
    gs = [g for g in groups if g]
    if not gs:
        return ""
    if len(gs) == 1:
        return wrap(gs[0])
    return f"{wrap(gs[0])} AND ({' OR '.join(wrap(g) for g in gs[1:])})"


def build_wos(tiers, exclusions, warnings=None, broad=True):
    """Web of Science 高级检索式（官方格式，Search A 默认宽泛）。

    官方语法要点（Clarivate / CASRAI 文档）：
      - 字段标识用 TS=（Topic=标题+摘要+作者关键词+Keywords Plus），多词短语必须加引号。
      - 布尔算符 AND/OR/NOT 必须全大写；同层同义词用 OR 并括号分组：TS=("a" OR "b")。
      - broad（Search A）：TS=(领域层) AND (TS=(技术层) OR TS=(应用层)) —— 高召回，不强制三层全命中。
      - 排除用单个 NOT TS=(...) 把多个排除概念 OR 在一起，避免 (NOT A)(NOT B) 歧义。
      - 排除项必须是英文；非 ASCII（中文）描述无法被 WoS 匹配，需翻译或跳过。
    """
    groups = _tier_groups(tiers)
    w = lambda g: f"TS=({g})"
    core = _broad_and(groups, w) if broad else " AND ".join(w(g) for g in groups)
    ex_terms = _guard_exclusions(exclusions, warnings, "wos", allow_cjk=False)
    ex_clause = f" NOT TS=({_fmt_excl_terms(ex_terms)})" if ex_terms else ""
    return core + ex_clause


def build_scopus(tiers, exclusions, warnings=None, broad=True):
    groups = _tier_groups(tiers)
    w = lambda g: f"TITLE-ABS-KEY({g})"
    core = _broad_and(groups, w) if broad else " AND ".join(w(g) for g in groups)
    ex_terms = _guard_exclusions(exclusions, warnings, "scopus", allow_cjk=False)
    if ex_terms:
        core += " AND NOT " + w(_fmt_excl_terms(ex_terms))
    return core


def build_ieee(tiers, exclusions, warnings=None, broad=True):
    groups = _tier_groups(tiers)
    field = '"Abstract"' if broad else '"Document Title"'
    w = lambda g: f'{field}:({g})'
    core = _broad_and(groups, w) if broad else " AND ".join(w(g) for g in groups)
    q = f"(({core}))" if core else ""
    ex_terms = _guard_exclusions(exclusions, warnings, "ieee", allow_cjk=False)
    if ex_terms:
        q += " AND NOT (" + _fmt_excl_terms(ex_terms) + ")"
    return q


def _gs_term(t):
    """Google Scholar 词项：仅多词短语加引号（单字无引号，省字符且召回更广）。"""
    t = str(t).strip()
    return f'"{t}"' if ' ' in t else t


def _gs_or_group(terms, max_len):
    """构造 (t1 OR t2 OR ...) 形式，在 max_len 内尽量塞入最多词项；
    逐词累加，保证括号/引号始终平衡；预算不足放不下首项时返回空组（不溢出）。"""
    if not terms:
        return ""
    grp = "("
    first = True
    for t in terms:
        addition = t if first else " OR " + t
        if len(grp + addition + ")") <= max_len:
            grp += addition
            first = False
        else:
            break
    if first:  # 预算过小连首项都放不下——返回空组，不强行溢出
        return ""
    return grp + ")"


def _gs_variants(t1, t2, t3, exclusions, warnings):
    """Google Scholar 专用 5 变体：受 256 字符硬上限约束，单条查询无法容纳全部词项，
    故把技术/应用词项切分为互补的两半，保证 5 条彼此不同且共同覆盖 领域+技术+应用+综述。
    """
    domain_terms = [_gs_term(t) for t in t1 if str(t).strip()]
    tech_terms = [_gs_term(t) for t in t2 if str(t).strip()]
    app_terms = [_gs_term(t) for t in t3 if str(t).strip()]
    dg = _gs_or_group(domain_terms, 256)
    mid = lambda lst: (lst[: (len(lst) + 1) // 2], lst[(len(lst) + 1) // 2:])
    tech_a, tech_b = mid(tech_terms)
    app_a, app_b = mid(app_terms)
    out = []
    # 1) 宽泛：领域 + (技术前半 OR 应用前半)
    ta = _gs_or_group(list(tech_a) + list(app_a), 256 - len(dg) - 1)
    out.append(("broad", "宽泛检索（高召回·技术+应用抽样）", " ".join(x for x in (dg, ta) if x)))
    # 2) 精准：领域 + (技术后半 OR 应用后半) —— 与 broad 互补，合起来覆盖全部
    tb = _gs_or_group(list(tech_b) + list(app_b), 256 - len(dg) - 1)
    out.append(("precise", "精准检索（技术+应用补充抽样）", " ".join(x for x in (dg, tb) if x)))
    # 3) 技术视角：领域 + 全部技术词
    tg = _gs_or_group(tech_terms, 256 - len(dg) - 1)
    out.append(("angle_tech", "多角度·技术视角（全部技术词）", " ".join(x for x in (dg, tg) if x)))
    # 4) 应用视角：领域 + 全部应用词
    ag = _gs_or_group(app_terms, 256 - len(dg) - 1)
    out.append(("angle_app", "多角度·应用视角（全部应用词）", " ".join(x for x in (dg, ag) if x)))
    # 5) 综述导向：领域 + 技术前半 + intitle review/survey
    rt = _gs_or_group(list(tech_a) + ["intitle:review", "intitle:survey"], 256 - len(dg) - 1)
    out.append(("review", "多角度·综述导向（限定 review/survey）", " ".join(x for x in (dg, rt) if x)))
    if exclusions and warnings is not None:
        warnings.append(("google_scholar",
                         ["exclusions omitted (256-char limit); apply via Scholar UI or other DBs"]))
    return [{"variant": v[0], "label": v[1], "query": v[2]} for v in out]


def build_google_scholar(tiers, exclusions, warnings=None, broad=True):
    """Google Scholar 检索式（符合 Google Scholar 官方算符）。

    官方算符（Google Scholar Help / 图书馆指南）：
      - 空格 = AND；OR 必须大写；"短语" 精确匹配；-词 排除（连字符前留空格）；
        intitle: 限定标题词；AROUND(n) 邻近检索。
      - 查询长度硬上限 256 字符（超出被截断！），故须精简。
    修复点：
      1) 旧代码把 tier1 全部短语用空格 AND 连接（"a" "b" "c" 全须命中）→ 极窄，仅 ~15 条。
         改为：领域层(tier1) 用 OR 组合，技术+应用层(tier2+tier3) 用 OR 组合，空格 AND。
      2) 单字关键词不加引号（省字符）；排除串过长（易超 256），对 Scholar 省略排除，
         改由用户在 Scholar 界面或下游数据库过滤（已在 warnings 提示）。
      3) 用 _gs_or_group 逐词累加构造，严格控制在 256 字符内且括号/引号始终平衡。
    """
    t1 = tiers.get("tier1_species_object", []) or tiers.get("tier1", [])
    t2 = tiers.get("tier2_technology_method", []) or tiers.get("tier2", [])
    t3 = tiers.get("tier3_application_task", []) or tiers.get("tier3", [])
    domain_terms = [_gs_term(t) for t in t1 if str(t).strip()]
    tech_terms = [_gs_term(t) for t in t2 if str(t).strip()]
    app_terms = [_gs_term(t) for t in t3 if str(t).strip()]
    if broad:
        domain_grp = _gs_or_group(domain_terms, 256)
        ta_terms = tech_terms + app_terms
        budget = 256 - len(domain_grp) - 1  # 留空格
        ta_grp = _gs_or_group(ta_terms, budget) if budget > 0 else ""
        base = " ".join(p for p in (domain_grp, ta_grp) if p)
    else:
        # precise：领域 AND 技术 AND 应用（三层各自成 OR 组）
        domain_grp = _gs_or_group(domain_terms, 256)
        budget2 = 256 - len(domain_grp) - 1
        tech_grp = _gs_or_group(tech_terms, budget2) if budget2 > 0 else ""
        budget3 = 256 - len(domain_grp) - (len(tech_grp) + 1 if tech_grp else 0) - 1
        app_grp = _gs_or_group(app_terms, budget3) if budget3 > 0 else ""
        base = " ".join(p for p in (domain_grp, tech_grp, app_grp) if p)
    q = base
    if len(q) > 256:
        q = q[:256]
    # Scholar 256 上限：排除串过长，省略排除（用户可在 UI 过滤；已提示）
    if exclusions and warnings is not None:
        warnings.append(("google_scholar",
                         ["exclusions omitted (256-char limit); apply via Scholar UI or other DBs"]))
    return q


def build_cnki(tiers, exclusions, warnings=None, broad=True):
    def su_or(terms):
        joined = " OR ".join(f"SU='{t}'" for t in terms)
        return f"({joined})" if len(terms) > 1 else joined
    g1 = su_or(tiers.get("tier1_species_object", []) or tiers.get("tier1", []))
    g2 = su_or(tiers.get("tier2_technology_method", []) or tiers.get("tier2", []))
    g3 = su_or(tiers.get("tier3_application_task", []) or tiers.get("tier3", []))
    groups = [g for g in (g1, g2, g3) if g]
    core = f"{groups[0]} AND ({' OR '.join(groups[1:])})" if broad and len(groups) >= 2 \
           else " AND ".join(groups)
    for e in exclusions:  # 中文库，保留中文排除词
        if str(e).strip():
            core += f" AND NOT SU='{e.strip()}'"
    return core


def build_wanfang(tiers, exclusions, warnings=None, broad=True):
    def zw_or(terms):
        joined = " OR ".join(f'主题:("{t}")' for t in terms)
        return f"({joined})" if len(terms) > 1 else joined
    g1 = zw_or(tiers.get("tier1_species_object", []) or tiers.get("tier1", []))
    g2 = zw_or(tiers.get("tier2_technology_method", []) or tiers.get("tier2", []))
    g3 = zw_or(tiers.get("tier3_application_task", []) or tiers.get("tier3", []))
    groups = [g for g in (g1, g2, g3) if g]
    core = f"{groups[0]} AND ({' OR '.join(groups[1:])})" if broad and len(groups) >= 2 \
           else " AND ".join(groups)
    for e in exclusions:  # 中文库，保留中文排除词
        if str(e).strip():
            core += f' AND NOT 主题:("{e.strip()}")'
    return core


BUILDERS = {
    "wos": build_wos,
    "scopus": build_scopus,
    "ieee": build_ieee,
    "google_scholar": build_google_scholar,
    "cnki": build_cnki,
    "wanfang": build_wanfang,
}


def generate(scope, platforms=None, warnings=None):
    """返回 {platform: query_string}（单条宽泛式，向后兼容）。warnings 收集排除项告警。"""
    tiers = scope.get("keyword_tiers", {})
    exclusions = scope.get("explicit_exclusions", [])
    if platforms is None:
        platforms = list(BUILDERS.keys())
    out = {}
    for p in platforms:
        if p in BUILDERS:
            out[p] = BUILDERS[p](tiers, exclusions, warnings)
    return out


# 各平台「综述导向」追加片段（限定 review/survey 类文献），用各库原生语法。
# 用于 generate_variants 的 review 角度。
_REVIEW_SUFFIX = {
    "wos": ' AND (TS=("review" OR "survey"))',
    "scopus": ' AND (TITLE-ABS-KEY("review" OR "survey") OR (LIMIT-TO(DOCTYPE,"re")))',
    "ieee": ' AND ("review" OR "survey")',
    "google_scholar": ' (intitle:review OR intitle:survey)',
    "cnki": " AND (SU='综述' OR SU='survey')",
    "wanfang": ' AND (主题:("综述" OR "survey"))',
}


def generate_variants(scope, platforms=None, warnings=None):
    """为每个平台生成 3–5 个不同层次检索式组合，覆盖宽泛/精准/多角度。

    返回结构：{platform: [ {"variant","label","query"}, ... ]}
      - broad      : 宽泛检索（高召回）—— 领域层 AND (技术层 OR 应用层)
      - precise    : 精准检索（高精确）—— 三层全 AND（broad=False）
      - angle_tech : 多角度·技术视角 —— 仅 领域层 + 技术层
      - angle_app  : 多角度·应用视角 —— 仅 领域层 + 应用层
      - review     : 多角度·综述导向 —— 宽泛式 + 各库 review/survey 限定
    多角度组合共同覆盖综述所需参考文献范围；用户自行粘贴执行并下载 PDF。
    """
    tiers = scope.get("keyword_tiers", {})
    exclusions = scope.get("explicit_exclusions", [])
    if platforms is None:
        platforms = list(BUILDERS.keys())
    t1 = tiers.get("tier1_species_object", []) or tiers.get("tier1", [])
    t2 = tiers.get("tier2_technology_method", []) or tiers.get("tier2", [])
    t3 = tiers.get("tier3_application_task", []) or tiers.get("tier3", [])
    out = {}
    for p in platforms:
        if p not in BUILDERS:
            continue
        # Google Scholar 受 256 字符硬上限约束，用专用互补切分生成 5 条不同变体
        if p == "google_scholar":
            out[p] = _gs_variants(t1, t2, t3, exclusions, warnings)
            continue
        b = BUILDERS[p]
        variants = []
        # 1) 宽泛（高召回）—— 收集排除项告警
        variants.append({
            "variant": "broad",
            "label": "宽泛检索（高召回）",
            "query": b(tiers, exclusions, warnings),
        })
        # 2) 精准（三层全 AND）
        variants.append({
            "variant": "precise",
            "label": "精准检索（高精确）",
            "query": b(tiers, exclusions, None, broad=False),
        })
        # 3) 技术视角（领域 + 技术）
        if t2:
            sub = {"tier1_species_object": t1, "tier2_technology_method": t2}
            variants.append({
                "variant": "angle_tech",
                "label": "多角度·技术视角（领域+技术）",
                "query": b(sub, exclusions, None),
            })
        # 4) 应用视角（领域 + 应用）
        if t3:
            sub = {"tier1_species_object": t1, "tier3_application_task": t3}
            variants.append({
                "variant": "angle_app",
                "label": "多角度·应用视角（领域+应用）",
                "query": b(sub, exclusions, None),
            })
        # 5) 综述导向（宽泛式 + review 限定）
        rs = _REVIEW_SUFFIX.get(p, "")
        if rs:
            if p == "google_scholar":
                # Scholar 256 上限：把 review 词项并入 tech/app OR 组，增量构造保证 <=256
                domain_terms = [_gs_term(t) for t in t1 if str(t).strip()]
                ta_terms = [_gs_term(t) for t in (list(t2) + list(t3)) if str(t).strip()] \
                           + ["intitle:review", "intitle:survey"]
                dg = _gs_or_group(domain_terms, 256)
                budget = 256 - len(dg) - 1
                taq = _gs_or_group(ta_terms, budget) if budget > 0 else ""
                rev_q = dg + (" " + taq if taq else "")
            else:
                rev_q = b(tiers, exclusions, None) + rs
            variants.append({
                "variant": "review",
                "label": "多角度·综述导向（限定 review/survey）",
                "query": rev_q,
            })
        out[p] = variants
    return out


def _demo_scope():
    return {
        "keyword_tiers": {
            "tier1_species_object": ["organ-on-a-chip", "microfluidic organoid"],
            "tier2_technology_method": ["microfluidics", "3D bioprinting"],
            "tier3_application_task": ["drug toxicity screening"],
        },
        "explicit_exclusions": ["disease diagnosis", "in vivo animal"],
    }


def main():
    ap = argparse.ArgumentParser(description="QueryStrategist 多平台检索式生成器")
    ap.add_argument("--scope", help="scope JSON 文件路径")
    ap.add_argument("--platforms", nargs="+", help="指定平台 (wos scopus ieee google_scholar cnki wanfang)")
    ap.add_argument("--all", action="store_true", help="生成全部 6 个平台")
    ap.add_argument("--variants", action="store_true",
                    help="生成每平台 3-5 个分层检索式组合（宽泛/精准/多角度）")
    ap.add_argument("--t1", nargs="*", default=[], help="tier1 关键词")
    ap.add_argument("--t2", nargs="*", default=[], help="tier2 关键词")
    ap.add_argument("--t3", nargs="*", default=[], help="tier3 关键词")
    ap.add_argument("--ex", nargs="*", default=[], help="排除项")
    args = ap.parse_args()

    if args.scope:
        with open(args.scope, encoding="utf-8") as f:
            scope = json.load(f)
    elif args.t1 or args.t2 or args.t3 or args.ex:
        scope = {
            "keyword_tiers": {
                "tier1_species_object": args.t1,
                "tier2_technology_method": args.t2,
                "tier3_application_task": args.t3,
            },
            "explicit_exclusions": args.ex,
        }
    else:
        print("[demo] 未提供参数，使用示例 scope:\n")
        scope = _demo_scope()

    platforms = None if (args.all or not args.platforms) else args.platforms
    if args.variants:
        result = generate_variants(scope, platforms)
        # 扁平化为可读列表
        flat = {}
        for p, vs in result.items():
            flat[p] = [{"variant": v["variant"], "label": v["label"], "query": v["query"]} for v in vs]
        print(json.dumps(flat, ensure_ascii=False, indent=2))
    else:
        result = generate(scope, platforms)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
