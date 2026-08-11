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

输出: JSON {platform: query_string_or_list}；Google Scholar 在长词表下返回互补查询列表。
      --variants 时输出 {platform: [{variant,label,query}, ...]} 分层组合；IEEE 按
      Command Search 按每个 search clause 校验 25-term 上限并生成 A/B/C/D/E 变体。
"""
import argparse
import json
import re


def _join_terms(terms, op=" OR "):
    """Join English terms; quote phrases but keep simple words lemmatizable."""
    terms = [t.strip() for t in terms if t.strip()]
    out = []
    for term in terms:
        if term.startswith('"') and term.endswith('"'):
            out.append(term)
        elif re.fullmatch(r"[A-Za-z0-9*?$]+", term):
            out.append(term)
        else:
            out.append(f'"{term}"')
    return " OR ".join(out)


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
# Search A 默认 broad=True：领域、必需技术锚点、任务三概念强制共现；
# 每个概念组内部用 OR 扩展召回。


def _tier_groups(tiers):
    """把三层关键词各自 OR 成组，返回非空组列表。"""
    return [_join_terms(terms) for terms in _search_tiers(tiers) if terms]


def _search_tiers(tiers):
    """Return object, required technology anchor, and application tiers.

    `tier2_required_anchor` is optional and lets Scope Definer distinguish the
    indispensable technology from supporting methods such as machine learning.
    Legacy scopes fall back to the complete Tier 2 list.
    """
    t1 = _tier(tiers, "tier1_species_object", "tier1")
    t2 = (
        tiers.get("tier2_required_anchor")
        or tiers.get("required_anchor_terms")
        or _tier(tiers, "tier2_technology_method", "tier2")
    )
    t3 = _tier(tiers, "tier3_application_task", "tier3")
    return t1, t2, t3


def _validate_required_tiers(tiers, context="scope"):
    """Fail fast when Search A cannot enforce its three required concepts."""
    labels = ("tier1 object", "tier2 required technology anchor", "tier3 task")
    for label, terms in zip(labels, _search_tiers(tiers)):
        if not any(str(term).strip() for term in (terms or [])):
            raise ValueError(f"{context} is missing required {label} terms")


def _broad_and(groups, wrap):
    """Search A: require every supplied concept tier; broaden within tiers."""
    gs = [g for g in groups if g]
    return " AND ".join(wrap(g) for g in gs)


def build_wos(tiers, exclusions, warnings=None, broad=True):
    """Web of Science 高级检索式（官方格式，Search A 默认宽泛）。

    官方语法要点（Clarivate / CASRAI 文档）：
      - 字段标识用 TS=（Topic=标题+摘要+作者关键词+Keywords Plus），多词短语必须加引号。
      - 布尔算符 AND/OR/NOT 必须全大写；同层同义词用 OR 并括号分组：TS=("a" OR "b")。
      - broad（Search A）：TS=(领域层) AND TS=(必需技术锚点) AND TS=(应用层)。
      - 排除用单个 NOT TS=(...) 把多个排除概念 OR 在一起，避免 (NOT A)(NOT B) 歧义。
      - 排除项必须是英文；非 ASCII（中文）描述无法被 WoS 匹配，需翻译或跳过。
    """
    groups = _tier_groups(tiers)
    w = lambda g: f"TS=({g})"
    if broad:
        core = _broad_and(groups, w)
    else:
        t1, t2, t3 = _search_tiers(tiers)
        core = (
            f"TI=({_join_terms(t1)}) AND "
            f"TS=(({_join_terms(t2)}) NEAR/10 ({_join_terms(t3)}))"
        )
    ex_terms = _guard_exclusions(exclusions, warnings, "wos", allow_cjk=False)
    ex_clause = f" NOT TS=({_fmt_excl_terms(ex_terms)})" if ex_terms else ""
    return core + ex_clause


def build_scopus(tiers, exclusions, warnings=None, broad=True):
    groups = _tier_groups(tiers)
    w = lambda g: f"TITLE-ABS-KEY({g})"
    if broad:
        core = _broad_and(groups, w)
    else:
        t1, t2, t3 = _search_tiers(tiers)
        core = (
            f"TITLE({_join_terms(t1)}) AND "
            f"TITLE-ABS-KEY(({_join_terms(t2)}) W/5 ({_join_terms(t3)}))"
        )
    ex_terms = _guard_exclusions(exclusions, warnings, "scopus", allow_cjk=False)
    if ex_terms:
        core += " AND NOT " + w(_fmt_excl_terms(ex_terms))
    return core


IEEE_MAX_SEARCH_TERMS = 25
IEEE_MAX_WILDCARDS = 10


def _ieee_clean_terms(terms):
    """去空、去重并保留原始顺序。"""
    out = []
    seen = set()
    for term in terms or []:
        value = str(term).strip()
        if value and value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _ieee_tiers(tiers):
    t1, t2, t3 = _search_tiers(tiers)
    return (
        _ieee_clean_terms(t1),
        _ieee_clean_terms(t2),
        _ieee_clean_terms(t3),
    )


def _ieee_quote(term):
    """Format one IEEE value without disabling stemming for simple words."""
    value = re.sub(r"\s+", " ", str(term).strip())
    if value.startswith('"') and value.endswith('"'):
        return value
    if '"' in value:
        raise ValueError(f"IEEE search term contains an unmatched quote: {term!r}")
    if re.fullmatch(r"[A-Za-z0-9*?]+", value):
        return value
    return f'"{value}"'


def _ieee_group(terms, field=None):
    """构造 IEEE OR 组；字段限定必须逐项重复，禁止 field:(A OR B)。"""
    values = []
    for term in terms:
        value = _ieee_quote(term)
        values.append(f'"{field}":{value}' if field else value)
    return f"({' OR '.join(values)})" if values else ""


def _ieee_clause_term_counts(query):
    """Count consecutive terms in each clause, as defined by IEEE Search Tips.

    Boolean/proximity operators end a clause. Words inside an exact phrase are
    counted conservatively as consecutive terms; field names do not count.
    """
    token_re = re.compile(
        r'"[^"\r\n]+"\s*:|"[^"\r\n]*"|'
        r'\bONEAR/\d+\b|\bNEAR/\d+\b|\bAND\b|\bOR\b|\bNOT\b|[()]|[^\s()]+',
        re.IGNORECASE,
    )
    counts = []
    current = 0
    for token in token_re.findall(query or ""):
        upper = token.upper()
        if upper in {"AND", "OR", "NOT"} or re.fullmatch(
            r"(?:NEAR|ONEAR)/\d+", upper
        ):
            if current:
                counts.append(current)
                current = 0
            continue
        if token in {"(", ")"} or re.fullmatch(r'"[^"\r\n]+"\s*:', token):
            continue
        value = token[1:-1] if token.startswith('"') and token.endswith('"') else token
        current += len(re.findall(r"[A-Za-z0-9*?]+", value))
    if current:
        counts.append(current)
    return counts


def _ieee_query_term_count(query):
    """Backward-compatible helper returning the largest IEEE search clause."""
    counts = _ieee_clause_term_counts(query)
    return max(counts, default=0)


def _ieee_validate_query(query):
    """Validate official Command Search constraints used by the generator."""
    if query.count('"') % 2:
        raise ValueError("IEEE query has unbalanced quotation marks")
    if query.count("(") != query.count(")"):
        raise ValueError("IEEE query has unbalanced parentheses")
    if re.search(r'"[^"\r\n]+"\s*:\s*\(', query):
        raise ValueError("IEEE field names cannot directly contain a parenthesized OR group")
    counts = _ieee_clause_term_counts(query)
    if any(count > IEEE_MAX_SEARCH_TERMS for count in counts):
        raise ValueError("IEEE query contains a search clause over the 25-term limit")

    wildcard_count = query.count("*") + query.count("?")
    if wildcard_count > IEEE_MAX_WILDCARDS:
        raise ValueError("IEEE query exceeds the 10-wildcard limit")
    for prefix in re.findall(r"(?<![A-Za-z0-9])([A-Za-z0-9]*)(?=[*?])", query):
        if len(prefix) < 3:
            raise ValueError("IEEE wildcards require at least three preceding characters")
    return query


def _ieee_split_queries(group_specs, exclusions, warnings=None):
    """Build one complete query and validate each IEEE search clause."""
    groups = [(_ieee_clean_terms(terms), field)
              for terms, field in group_specs if _ieee_clean_terms(terms)]
    if not groups:
        return []

    ex_terms = _guard_exclusions(exclusions, warnings, "ieee", allow_cjk=False)
    exclusion_query = _fmt_excl_terms(ex_terms)
    parts = [_ieee_group(terms, field) for terms, field in groups]
    query = " AND ".join(part for part in parts if part)
    if exclusion_query:
        query += f" NOT ({exclusion_query})"
    return [_ieee_validate_query(query)]


def _ieee_core_queries(tiers, exclusions, warnings=None, field=None):
    t1, t2, t3 = _ieee_tiers(tiers)
    specs = [(t1, field), (t2, field), (t3, field)]
    return _ieee_split_queries(specs, exclusions, warnings)


def build_ieee(tiers, exclusions, warnings=None, broad=True):
    """Generate one complete IEEE query; validate official clause constraints."""
    field = None if broad else "Document Title"
    queries = _ieee_core_queries(tiers, exclusions, warnings, field)
    return queries[0] if queries else ""


def _ieee_add_variants(rows, code, label, queries):
    total = len(queries)
    for index, query in enumerate(queries, 1):
        suffix = f"_{index}" if total > 1 else ""
        part = f"（拆分 {index}/{total}）" if total > 1 else ""
        rows.append({"variant": f"{code}{suffix}", "label": f"{label}{part}", "query": query})


def _ieee_proximity_queries(tiers, exclusions):
    t1, t2, t3 = _ieee_tiers(tiers)
    if not t2 or not t3:
        return []

    ex_terms = _guard_exclusions(exclusions, None, "ieee", allow_cjk=False)
    exclusion_query = _fmt_excl_terms(ex_terms)
    proximity = f"({_ieee_group(t2)} NEAR/10 {_ieee_group(t3)})"
    base = f"{_ieee_group(t1)} AND {proximity}" if t1 else proximity
    if exclusion_query:
        base += f" NOT ({exclusion_query})"
    ordered = base.replace(" NEAR/10 ", " ONEAR/10 ")
    return [_ieee_validate_query(base), _ieee_validate_query(ordered)]


def _ieee_variants(scope, tiers, exclusions, warnings):
    rows = []
    broad = _ieee_core_queries(tiers, exclusions, warnings, field=None)
    precise = _ieee_core_queries(tiers, exclusions, None, field="Document Title")
    _ieee_add_variants(rows, "broad", "IEEE A·宽泛检索（All Metadata）", broad)
    _ieee_add_variants(rows, "precise", "IEEE B·标题高精度检索", precise)

    publication_titles = (
        scope.get("ieee_publication_titles")
        or scope.get("target_conferences")
        or scope.get("target_publications")
        or []
    )
    if isinstance(publication_titles, str):
        publication_titles = [publication_titles]
    t1, t2, _ = _ieee_tiers(tiers)
    if publication_titles:
        conference = _ieee_split_queries(
            [(t1, None), (t2, None), (publication_titles, "Publication Title")],
            exclusions,
            None,
        )
        _ieee_add_variants(rows, "conference", "IEEE C·会议/出版物定向", conference)

    proximity = _ieee_proximity_queries(tiers, exclusions)
    labels = ["IEEE D1·无序邻近检索（NEAR）", "IEEE D2·有序邻近检索（ONEAR）"]
    for index, query in enumerate(proximity):
        rows.append({"variant": f"proximity_{index + 1}", "label": labels[index], "query": query})

    review = _ieee_split_queries(
        [(t1, None), (t2, None), (["review", "survey"], None)],
        exclusions,
        None,
    )
    _ieee_add_variants(rows, "review", "IEEE E·综述导向", review)
    return rows


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


def _gs_group_chunks(raw_terms, max_len):
    """Split a synonym tier into complete parenthesized groups."""
    terms = [_gs_term(t) for t in raw_terms if str(t).strip()]
    if not terms:
        return []
    chunks, current = [], []
    for term in terms:
        candidate = current + [term]
        if len(f"({' OR '.join(candidate)})") <= max_len:
            current = candidate
            continue
        if not current:
            raise ValueError(f"Google Scholar term exceeds group budget: {term}")
        chunks.append(f"({' OR '.join(current)})")
        current = [term]
    if current:
        chunks.append(f"({' OR '.join(current)})")
    return chunks


def _gs_search_a_queries(tiers):
    """Return complementary Search A queries without silently dropping terms."""
    t1, t2, t3 = _search_tiers(tiers)
    group_sets = [
        _gs_group_chunks(t1, 75),
        _gs_group_chunks(t2, 90),
        _gs_group_chunks(t3, 87),
    ]
    active = [groups for groups in group_sets if groups]
    if not active:
        return []
    queries = [""]
    for groups in active:
        queries = [" ".join(p for p in (base, group) if p)
                   for base in queries for group in groups]
    if any(len(query) > 256 for query in queries):
        raise ValueError("internal error: Google Scholar query exceeds 256 characters")
    return list(dict.fromkeys(queries))


def _gs_variants(tiers, exclusions, warnings):
    """Generate complementary, anchor-preserving Google Scholar queries."""
    queries = _gs_search_a_queries(tiers)
    total = len(queries)
    rows = []
    for index, query in enumerate(queries, 1):
        suffix = f"_{index}" if total > 1 else ""
        label = f"宽泛互补检索 {index}/{total}" if total > 1 else "宽泛检索"
        rows.append({"variant": f"broad{suffix}", "label": label, "query": query})
    if queries:
        for kind in ("review", "survey"):
            candidate = f"{queries[0]} intitle:{kind}"
            if len(candidate) <= 256:
                rows.append({
                    "variant": f"review_{kind}",
                    "label": f"综述导向（标题含 {kind}）",
                    "query": candidate,
                })
    if exclusions and warnings is not None:
        warnings.append(("google_scholar",
                         ["exclusions omitted to preserve all three core concepts"]))
    return rows


def build_google_scholar(tiers, exclusions, warnings=None, broad=True):
    """Google Scholar 检索式（符合 Google Scholar 官方算符）。

    官方算符（Google Scholar Help / 图书馆指南）：
      - 空格 = AND；OR 必须大写；"短语" 精确匹配；-词 排除（连字符前留空格）；
        intitle: 限定标题词；AROUND(n) 邻近检索。
      - 查询长度硬上限 256 字符（超出被截断！），故须精简。
    修复点：
      1) 三类概念组之间使用空格（隐式 AND），组内同义词使用 OR。
      2) 单字关键词不加引号（省字符）；排除串过长（易超 256），对 Scholar 省略排除，
         改由用户在 Scholar 界面或下游数据库过滤（已在 warnings 提示）。
      3) 用 _gs_or_group 逐词累加构造，严格控制在 256 字符内且括号/引号始终平衡。
    """
    t1, t2, t3 = _search_tiers(tiers)
    domain_terms = [_gs_term(t) for t in t1 if str(t).strip()]
    tech_terms = [_gs_term(t) for t in t2 if str(t).strip()]
    app_terms = [_gs_term(t) for t in t3 if str(t).strip()]
    if broad:
        queries = _gs_search_a_queries(tiers)
        base = queries[0] if queries else ""
    else:
        # precise：领域 AND 技术 AND 应用（三层各自成 OR 组）
        domain_grp = _gs_or_group(domain_terms, 256)
        budget2 = 256 - len(domain_grp) - 1
        tech_grp = _gs_or_group(tech_terms, budget2) if budget2 > 0 else ""
        budget3 = 256 - len(domain_grp) - (len(tech_grp) + 1 if tech_grp else 0) - 1
        app_grp = _gs_or_group(app_terms, budget3) if budget3 > 0 else ""
        base = " ".join(p for p in (domain_grp, tech_grp, app_grp) if p)
    q = base
    # Scholar 256 上限：排除串过长，省略排除（用户可在 UI 过滤；已提示）
    if exclusions and warnings is not None:
        warnings.append(("google_scholar",
                         ["exclusions omitted to preserve all three core concepts"]))
    return q


def build_cnki(tiers, exclusions, warnings=None, broad=True):
    def field_or(field, terms):
        joined = " OR ".join(f"{field}='{str(t).strip()}'" for t in terms)
        return f"({joined})" if len(terms) > 1 else joined
    t1, t2, t3 = _search_tiers(tiers)
    if broad:
        g1 = field_or("SU", t1)
        g2 = field_or("SU", t2)
        g3 = field_or("SU", t3)
    else:
        g1 = field_or("TI", t1)
        g2 = field_or("SU", t2)
        g3 = field_or("TI", t3)
    groups = [g for g in (g1, g2, g3) if g]
    core = " AND ".join(groups)
    ex_terms = [f"SU='{str(e).strip()}'" for e in exclusions if str(e).strip()]
    if ex_terms:
        core += f" NOT ({' OR '.join(ex_terms)})"
    return core


def build_wanfang(tiers, exclusions, warnings=None, broad=True):
    def wf_term(term, precise=False):
        value = str(term).strip()
        return f'"{value}"' if precise or re.search(r"\s|[()]", value) else value

    def wf_or(terms, precise=False):
        values = [wf_term(t, precise) for t in terms if str(t).strip()]
        joined = " OR ".join(values)
        return f"({joined})" if len(values) > 1 else joined

    t1, t2, t3 = _search_tiers(tiers)
    g1 = wf_or(t1, precise=not broad)
    g2 = wf_or(t2, precise=not broad)
    g3 = wf_or(t3, precise=not broad)
    groups = [g for g in (g1, g2, g3) if g]
    core = " AND ".join(groups)
    ex_terms = [wf_term(e) for e in exclusions if str(e).strip()]
    if ex_terms:
        core += f" NOT ({' OR '.join(ex_terms)})"
    if len(core) > 800:
        raise ValueError("Wanfang Professional Search expression exceeds 800 characters")
    return core


BUILDERS = {
    "wos": build_wos,
    "scopus": build_scopus,
    "ieee": build_ieee,
    "google_scholar": build_google_scholar,
    "cnki": build_cnki,
    "wanfang": build_wanfang,
}


def _strategy_priority(writing_type):
    value = str(writing_type or "").lower()
    if any(term in value for term in ("研究论著", "实验研究", "research")):
        return "precision-priority"
    if any(term in value for term in ("开题", "基金", "proposal", "grant")):
        return "novelty-priority"
    if any(term in value for term in ("综述", "review")):
        return "review-priority"
    return "balanced"


def _chinese_enabled(value):
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    return normalized not in ("", "no", "false", "0", "否", "不需要")


def generate(scope, platforms=None, warnings=None):
    """Return Search A queries; Scholar uses a complementary query list."""
    tiers = scope.get("keyword_tiers", {})
    exclusions = scope.get("explicit_exclusions", [])
    zh_tiers = scope.get("keyword_tiers_zh") or tiers
    zh_exclusions = scope.get("explicit_exclusions_zh") or exclusions
    _validate_required_tiers(tiers)
    if scope.get("keyword_tiers_zh"):
        _validate_required_tiers(zh_tiers, "keyword_tiers_zh")
    if platforms is None:
        platforms = list(BUILDERS.keys())
    out = {}
    for p in platforms:
        if p in BUILDERS:
            platform_tiers = zh_tiers if p in {"cnki", "wanfang"} else tiers
            platform_exclusions = zh_exclusions if p in {"cnki", "wanfang"} else exclusions
            if p in {"cnki", "wanfang"} and not scope.get("keyword_tiers_zh") \
                    and warnings is not None:
                warnings.append((p, ["keyword_tiers_zh missing; using primary-language tiers"]))
            if p == "google_scholar":
                out[p] = _gs_search_a_queries(platform_tiers)
                if platform_exclusions and warnings is not None:
                    warnings.append((
                        "google_scholar",
                        ["exclusions omitted to preserve all three core concepts"],
                    ))
            else:
                out[p] = BUILDERS[p](platform_tiers, platform_exclusions, warnings)
    return out


# 各平台「综述导向」追加片段（限定 review/survey 类文献），用各库原生语法。
# 用于 generate_variants 的 review 角度。
_REVIEW_SUFFIX = {
    "wos": ' AND (TS=("review" OR "survey"))',
    "scopus": ' AND (TITLE-ABS-KEY("review" OR "survey") OR (LIMIT-TO(DOCTYPE,"re")))',
    "ieee": ' AND ("review" OR "survey")',
    "google_scholar": ' (intitle:review OR intitle:survey)',
    "cnki": " AND (SU='综述' OR SU='survey')",
    "wanfang": ' AND (综述 OR survey)',
}


def _build_review_query(platform, builder, tiers, exclusions, suffix):
    """Place review criteria before the platform's final exclusion clause."""
    query = builder(tiers, [], None) + suffix
    if not exclusions:
        return query
    if platform == "wos":
        terms = _guard_exclusions(exclusions, None, "wos", allow_cjk=False)
        return query + (f" NOT TS=({_fmt_excl_terms(terms)})" if terms else "")
    if platform == "scopus":
        terms = _guard_exclusions(exclusions, None, "scopus", allow_cjk=False)
        return query + (
            f" AND NOT TITLE-ABS-KEY({_fmt_excl_terms(terms)})" if terms else ""
        )
    if platform == "cnki":
        terms = [f"SU='{str(term).strip()}'" for term in exclusions if str(term).strip()]
        return query + (f" NOT ({' OR '.join(terms)})" if terms else "")
    if platform == "wanfang":
        terms = [str(term).strip() for term in exclusions if str(term).strip()]
        return query + (f" NOT ({' OR '.join(terms)})" if terms else "")
    return query


def generate_variants(scope, platforms=None, warnings=None):
    """生成平台专属检索式组合；IEEE 按官方 search-clause 上限校验。

    返回结构：{platform: [ {"variant","label","query"}, ... ]}
      - broad      : 宽泛检索（高召回）—— 领域层 AND 必需技术锚点 AND 应用层
      - precise    : 精准检索（高精确）—— 三层全 AND（broad=False）
      - angle_tech : 多角度·技术视角 —— 仅 领域层 + 技术层
      - angle_app  : 多角度·应用视角 —— 仅 领域层 + 应用层
      - review     : 多角度·综述导向 —— 宽泛式 + 各库 review/survey 限定
    多角度组合共同覆盖综述所需参考文献范围；用户自行粘贴执行并下载 PDF。
    """
    tiers = scope.get("keyword_tiers", {})
    exclusions = scope.get("explicit_exclusions", [])
    zh_tiers = scope.get("keyword_tiers_zh") or tiers
    zh_exclusions = scope.get("explicit_exclusions_zh") or exclusions
    _validate_required_tiers(tiers)
    if scope.get("keyword_tiers_zh"):
        _validate_required_tiers(zh_tiers, "keyword_tiers_zh")
    if platforms is None:
        platforms = list(BUILDERS.keys())
    out = {}
    for p in platforms:
        if p not in BUILDERS:
            continue
        platform_tiers = zh_tiers if p in {"cnki", "wanfang"} else tiers
        platform_exclusions = zh_exclusions if p in {"cnki", "wanfang"} else exclusions
        pt1 = _tier(platform_tiers, "tier1_species_object", "tier1")
        pt2 = _tier(platform_tiers, "tier2_technology_method", "tier2")
        pt3 = _tier(platform_tiers, "tier3_application_task", "tier3")
        if p == "ieee":
            out[p] = _ieee_variants(scope, platform_tiers, platform_exclusions, warnings)
            continue
        # Google Scholar 用互补列表覆盖全部任务词，每条保留三类核心概念。
        if p == "google_scholar":
            out[p] = _gs_variants(platform_tiers, platform_exclusions, warnings)
            continue
        b = BUILDERS[p]
        variants = []
        # 1) 宽泛（高召回）—— 收集排除项告警
        variants.append({
            "variant": "broad",
            "label": "宽泛检索（高召回）",
            "query": b(platform_tiers, platform_exclusions, warnings),
        })
        # 2) 精准（三层全 AND）
        variants.append({
            "variant": "precise",
            "label": "精准检索（高精确）",
            "query": b(platform_tiers, platform_exclusions, None, broad=False),
        })
        # 3) 技术视角（领域 + 技术）
        if pt2:
            sub = {"tier1_species_object": pt1, "tier2_technology_method": pt2}
            variants.append({
                "variant": "angle_tech",
                "label": "多角度·技术视角（领域+技术）",
                "query": b(sub, platform_exclusions, None),
            })
        # 4) 应用视角（领域 + 应用）
        if pt3:
            sub = {"tier1_species_object": pt1, "tier3_application_task": pt3}
            variants.append({
                "variant": "angle_app",
                "label": "多角度·应用视角（领域+应用）",
                "query": b(sub, platform_exclusions, None),
            })
        # 5) 综述导向（宽泛式 + review 限定）
        rs = _REVIEW_SUFFIX.get(p, "")
        if rs:
            rev_q = _build_review_query(
                p, b, platform_tiers, platform_exclusions, rs
            )
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
                    help="生成平台专属分层检索式组合（IEEE 含 clause 校验与邻近检索）")
    ap.add_argument("--package", action="store_true",
                    help="输出 context + queries 包，保留写作类型、时间跨度和平台启用信息")
    ap.add_argument("--writing-type", help="写作类型，用于标注查全/查准/新颖性权重")
    ap.add_argument("--min-year", type=int, help="最早发表年份（传给各数据库筛选说明）")
    ap.add_argument("--max-year", type=int, help="最晚发表年份（传给各数据库筛选说明）")
    ap.add_argument("--chinese-supplement", choices=["yes", "no"],
                    help="是否启用 CNKI + Wanfang；未指定时读取 scope.project_config/config")
    ap.add_argument("--t1", nargs="*", default=[], help="tier1 关键词")
    ap.add_argument("--t2", nargs="*", default=[], help="tier2 关键词")
    ap.add_argument("--anchor", nargs="*", default=[],
                    help="Search A 必需技术锚点；未给出时使用完整 tier2")
    ap.add_argument("--method", nargs="*", default=[],
                    help="补充方法词，不替代 Search A 的必需技术锚点")
    ap.add_argument("--t3", nargs="*", default=[], help="tier3 关键词")
    ap.add_argument("--ex", nargs="*", default=[], help="排除项")
    args = ap.parse_args()

    if args.scope:
        with open(args.scope, encoding="utf-8") as f:
            scope = json.load(f)
    elif args.t1 or args.t2 or args.anchor or args.method or args.t3 or args.ex:
        scope = {
            "keyword_tiers": {
                "tier1_species_object": args.t1,
                "tier2_technology_method": args.t2,
                "tier2_required_anchor": args.anchor,
                "tier2_supporting_method": args.method,
                "tier3_application_task": args.t3,
            },
            "explicit_exclusions": args.ex,
        }
    else:
        print("[demo] 未提供参数，使用示例 scope:\n")
        scope = _demo_scope()

    project_config = scope.get("project_config") or scope.get("config") or {}
    writing_type = args.writing_type or project_config.get("writing_type")
    time_span = project_config.get("literature_time_span") or {}
    min_year = args.min_year if args.min_year is not None else time_span.get("start")
    max_year = args.max_year if args.max_year is not None else time_span.get("end")
    chinese_value = args.chinese_supplement
    if chinese_value is None:
        chinese_value = project_config.get("chinese_language_supplement")
    if args.platforms:
        platforms = args.platforms
    elif args.all:
        platforms = None
    elif chinese_value is not None and not _chinese_enabled(chinese_value):
        platforms = ["wos", "scopus", "ieee", "google_scholar"]
    else:
        platforms = None
    if args.variants:
        result = generate_variants(scope, platforms)
        # 扁平化为可读列表
        flat = {}
        for p, vs in result.items():
            flat[p] = [{"variant": v["variant"], "label": v["label"], "query": v["query"]} for v in vs]
        payload = flat
    else:
        payload = generate(scope, platforms)
    if args.package:
        payload = {
            "context": {
                "writing_type": writing_type,
                "strategy_priority": _strategy_priority(writing_type),
                "time_span": {"start": min_year, "end": max_year},
                "chinese_supplement": _chinese_enabled(chinese_value),
                "platforms": list(payload.keys()),
            },
            "queries": payload,
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
