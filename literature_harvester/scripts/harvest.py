"""
    harvest.py — QueryStrategist · 文献元数据收割器（两源版 V2.4）
=============================================================
Search B 通道：OpenAlex 收割 + Crossref 逐条验证（去幻觉）。

数据源:
    - OpenAlex  https://api.openalex.org/works         (无需 key，收割主源)
    - Crossref  https://api.crossref.org/works/{doi}   (无需 key，按 DOI 逐条验证)

设计原则（与 Search Strategist V1「收割 ≠ 语料」红线一致）:
    OpenAlex 返回的元数据可能含幻觉/错配（错误标题、作者、年份、DOI）。
    每条带 DOI 的记录回查 Crossref 验证 title/year 一致性：
      - 验证通过   → verified（可信，进入候选清单）
      - 验证不通过 → dropped（疑似幻觉/错配，剔除并说明原因）
      - 无 DOI     → unverified（无法交叉验证，保留供人工参考）
    因此本脚本输出既含「收割结果」也含「验证结论」，防止 AI 幻觉元数据
    被直接当作语料喂给下游。

    OA 状态（V2.1）：收割时经 `select=open_access` 一次请求附带
    is_oa / oa_status，不再逐篇回查 OpenAlex open_access——零额外 API 调用、
    零额外错误点（原 enrich_oa.py 回查方案已废弃删除）。

容错: 每个环节独立 try/except，单点失败只记录 *_error，绝不整体崩溃。

用法:
    python harvest.py --query "organ-on-a-chip drug toxicity" --out harvest.json
    python harvest.py --query "..." --mailto you@example.com
    python harvest.py --query "..." --no-verify            # 跳过 Crossref 验证

依赖（首次运行自动安装，无需手动 pip）:
    requests==2.32.5   OpenAlex / Crossref 双源必需
    离线/自管环境可设 HARVEST_NO_BOOTSTRAP=1 关闭自动安装；
    或运行 `python harvest.py --check-deps` 预检。
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import urlencode
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# 依赖自举：首次运行若无第三方依赖则自动安装，确保「一键跑通、节省用户时间」
# ---------------------------------------------------------------------------
def ensure_deps(auto_install=True):
    """检查并（按需）自动安装第三方依赖。返回 (missing, installed) 两个列表。

    仅安装已知安全、纯 Python 的包：
      - requests : OpenAlex / Crossref 双源必需
    auto_install=False 时只检测不安装（供 --check-deps 使用）。
    安装前会清除可能指向本地死代理的 *_PROXY 环境变量，避免 pip 卡在 Connection refused。
    """
    required = [
        ("requests", "requests==2.32.5"),
    ]
    missing = []
    for mod, pkg in required:
        try:
            __import__(mod)
        except Exception:
            missing.append(pkg)
    if not missing or not auto_install:
        return missing, []
    env = dict(os.environ)
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "all_proxy", "ALL_PROXY"):
        env.pop(k, None)
    installed = []
    for pkg in missing:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", pkg],
                env=env,
            )
            installed.append(pkg)
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"[warn] 自动安装依赖失败: {pkg} ({e})\n")
    return missing, installed


# 第三方依赖以惰性方式加载：先自举安装，再导入，确保同进程内可用
requests = None


def _load_third_party():
    """在 ensure_deps() 之后加载第三方模块（可能刚被自动安装）。"""
    global requests
    try:
        import requests as _r
        globals()["requests"] = _r
    except Exception:
        globals()["requests"] = None


# 导入模块时只探测现有依赖，不执行 pip 或网络操作。
_load_third_party()


UA_BASE = "QueryStrategist-Harvester/2.2"


class RequestBudgetExceeded(RuntimeError):
    """请求预算耗尽或端点熔断。"""


class RequestBudget:
    """管理单次运行的端点请求预算与连续 429 熔断状态。"""

    def __init__(self, limits=None):
        self.limits = {
            "openalex": int(os.environ.get("HARVEST_OPENALEX_BUDGET", "120")),
            "crossref": int(os.environ.get("HARVEST_CROSSREF_BUDGET", "60")),
        }
        if limits:
            self.limits.update({k: int(v) for k, v in limits.items() if v is not None})
        self.used = {key: 0 for key in self.limits}
        self.consecutive_429 = {key: 0 for key in self.limits}
        self.circuit_open = {key: False for key in self.limits}

    def reserve(self, endpoint):
        if self.circuit_open.get(endpoint):
            raise RequestBudgetExceeded(f"{endpoint} 端点已因连续 429 熔断")
        if self.used.get(endpoint, 0) >= self.limits.get(endpoint, 0):
            raise RequestBudgetExceeded(
                f"{endpoint} 请求预算已用尽（{self.used[endpoint]}/{self.limits[endpoint]}）"
            )
        self.used[endpoint] = self.used.get(endpoint, 0) + 1

    def record(self, endpoint, status):
        if status == 429:
            self.consecutive_429[endpoint] = self.consecutive_429.get(endpoint, 0) + 1
            if self.consecutive_429[endpoint] >= 3:
                self.circuit_open[endpoint] = True
        else:
            self.consecutive_429[endpoint] = 0

    def summary(self):
        return {
            endpoint: {
                "used": self.used.get(endpoint, 0),
                "limit": self.limits.get(endpoint, 0),
                "consecutive_429": self.consecutive_429.get(endpoint, 0),
                "circuit_open": self.circuit_open.get(endpoint, False),
            }
            for endpoint in self.limits
        }


_ACTIVE_BUDGET = None
_ACTIVE_CACHE_DIR = None


def _endpoint_for_url(url):
    return "crossref" if "api.crossref.org" in url else "openalex"


def _cache_path(url, params):
    if not _ACTIVE_CACHE_DIR:
        return None
    query = urlencode(sorted((str(k), str(v)) for k, v in (params or {}).items()))
    key = hashlib.sha256(f"{url}?{query}".encode("utf-8")).hexdigest()
    return os.path.join(_ACTIVE_CACHE_DIR, f"{key}.json")


def _read_cache(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_cache(path, payload):
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = f"{path}.{os.getpid()}.tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    os.replace(temp, path)


def _abstract_text(work):
    """Reconstruct OpenAlex's inverted-index abstract for local filtering."""
    inverted = work.get("abstract_inverted_index") or {}
    positions = [position for indexes in inverted.values() for position in indexes]
    if not positions:
        return ""
    words = [""] * (max(positions) + 1)
    for word, indexes in inverted.items():
        for position in indexes:
            words[position] = word
    return " ".join(words)


def _get(url, params, headers=None, timeout=20, max_retries=4, user_agent=None):
    """带预算、缓存、429 熔断与有上限退避的 JSON GET。"""
    if requests is None:
        raise RuntimeError("缺少依赖 requests，请先 pip install requests")
    endpoint = _endpoint_for_url(url)
    cache = _cache_path(url, params)
    cached = _read_cache(cache)
    if cached is not None:
        return cached
    ua = user_agent or UA_BASE
    h = {"User-Agent": ua}
    if headers:
        h.update(headers)
    last_err = None
    for attempt in range(max_retries):
        try:
            if _ACTIVE_BUDGET is not None:
                _ACTIVE_BUDGET.reserve(endpoint)
            r = requests.get(url, params=params, headers=h, timeout=timeout)
            if _ACTIVE_BUDGET is not None:
                _ACTIVE_BUDGET.record(endpoint, r.status_code)
            # 400/403/404 等客户端错误 — 重试也无效，直接退出
            if 400 <= r.status_code < 500 and r.status_code != 429:
                r.raise_for_status()  # 不会走到 return 之后，直接抛 HTTPError
            if r.status_code in (429, 500, 502, 503, 504):
                last_err = f"HTTP {r.status_code}"
                retry_after = r.headers.get("Retry-After")
                try:
                    retry_after = float(retry_after)
                except (TypeError, ValueError):
                    retry_after = 0
                wait = min(20, max(retry_after, min(40, 2 * (2 ** attempt))))
                if _ACTIVE_BUDGET is not None and _ACTIVE_BUDGET.circuit_open.get(endpoint):
                    raise RequestBudgetExceeded(f"{endpoint} 连续 3 次 429，已熔断")
                print(f"  [retry {attempt+1}/{max_retries}] {last_err}，{wait}s 后重试…", flush=True)
                if os.environ.get("HARVEST_NO_SLEEP") != "1":
                    time.sleep(wait)
                continue
            r.raise_for_status()
            payload = r.json()
            _write_cache(cache, payload)
            return payload
        except requests.RequestException as e:
            # 区分：如果是 4xx（不含 429）的 HTTPError，不再重试
            if isinstance(e, requests.HTTPError) and e.response is not None:
                sc = e.response.status_code
                if 400 <= sc < 500 and sc != 429:
                    raise RuntimeError(f"客户端错误 HTTP {sc}（不重试）: {e}")
            last_err = str(e)
            wait = min(40, 2 * (2 ** attempt))
            print(f"  [retry {attempt+1}/{max_retries}] {e}，{wait}s 后重试…", flush=True)
            if os.environ.get("HARVEST_NO_SLEEP") != "1":
                time.sleep(wait)
    raise RuntimeError(f"请求失败（已重试 {max_retries} 次）: {last_err}")


def harvest_openalex(query, per_platform=20, min_year=None, max_year=None):
    """OpenAlex 简单检索（search= 全字段匹配），返回标准文献列表。

    收割时通过 `select=open_access` 一次性附带 OA 状态（is_oa / oa_status），
    不再逐篇回查 OpenAlex open_access（V2.1：零额外 API 调用、零额外错误点）。
    """
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": per_platform,
        "select": "title,display_name,authorships,publication_year,doi,cited_by_count,id,primary_location,open_access",
    }
    if min_year or max_year:
        filters = []
        if min_year:
            filters.append(f"from_publication_date:{int(min_year)}-01-01")
        if max_year:
            filters.append(f"to_publication_date:{int(max_year)}-12-31")
        params["filter"] = ",".join(filters)
    data = _get(url, params)
    out = []
    for w in data.get("results", []):
        authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])][:8]
        oa = w.get("open_access") or {}
        out.append({
            "title": w.get("title") or w.get("display_name"),
            "authors": authors,
            "year": w.get("publication_year"),
            "doi": w.get("doi"),
            "cited_by_count": w.get("cited_by_count"),
            "url": w.get("primary_location", {}).get("landing_page_url") or w.get("id"),
            "source": "openalex",
            "is_oa": oa.get("is_oa"),
            "oa_status": oa.get("oa_status"),
        })
    return out


def harvest_openalex_filtered(species_terms, tech_terms, feed_terms,
                               per_platform=25, min_year=2016, max_year=None,
                               exclude_terms=None):
    """OpenAlex 字段限定搜索 — 三块强制共现，大幅提升精确率。

    使用 `filter=title_and_abstract.search:` 确保物种词 ∩ 技术词 ∩ 应用词
    同时出现在同一记录中（逗号分隔多个 filter 键 = AND 逻辑）。

    OpenAlex filter 语法规则（违反任一即 HTTP 400）:
        - 不支持括号 ()
        - 多词短语必须加引号，如 "computer vision"
        - 单 token 可裸写，如 transformer
        - | 为 OR（组内），逗号为 AND（组间）
        - sort=relevance_score 必须配 search= 参数，仅 filter= 时传它会 400
        - ⚠️ 文本搜索过滤器（title_and_abstract.search）不支持任何排除写法：
          `-` 前缀静默失效、`!` 前缀直接 HTTP 400（"Search filters do not support the ! operator"）。
          因此排除词必须在**本地**过滤（见 exclude_terms 参数），不能在 API 层做。

    Args:
        species_terms: 物种/对象词列表  (e.g. ["cat","dog","bird"])
        tech_terms:    技术/方法词列表  (e.g. ["computer vision","deep learning"])
        feed_terms:    应用/投喂词列表  (e.g. ["precision feeding","feed ration"])
        per_platform:  每页返回数量 (默认 25)
        min_year:      最早发表年份 (默认 2016)
        exclude_terms: 排除词列表；**在本地后置过滤**（OpenAlex 文本搜索过滤器不支持
                       任何排除语法：`-` 静默失效、`!` 直接 400，见函数 docstring 语法规则）。
                       匹配逻辑：title 或 abstract 含任一排除词的记录被剔除。

    Returns: 标准文献列表 (同 harvest_openalex 格式)
    """
    def _grp(terms):
        """将一个词列表转为 OpenAlex filter 可接受的 OR 组。
        每个词都加引号以确保多词短语安全。"""
        return "|".join(f'"{t}"' for t in terms)

    # 三块 filter: 物种 ∩ 技术 ∩ 应用
    filt = (f'title_and_abstract.search:{_grp(species_terms)},'
            f'title_and_abstract.search:{_grp(tech_terms)},'
            f'title_and_abstract.search:{_grp(feed_terms)},'
            f'from_publication_date:{min_year}-01-01')
    if max_year:
        filt += f",to_publication_date:{int(max_year)}-12-31"

    params = {
        "filter": filt,
        "per_page": per_platform,
        "select": "title,display_name,authorships,publication_year,doi,cited_by_count,id,primary_location,open_access,abstract_inverted_index",
    }
    data = _get("https://api.openalex.org/works", params)
    out = []
    for w in data.get("results", []):
        # 排除词本地后置过滤：OpenAlex 文本搜索过滤器不支持 API 层排除（- 静默失效 / ! 400）。
        if exclude_terms:
            searchable = " ".join((
                str(w.get("title") or w.get("display_name") or ""),
                _abstract_text(w),
            )).casefold()
            if any(str(term).casefold() in searchable for term in exclude_terms):
                continue
        authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])][:8]
        oa = w.get("open_access") or {}
        out.append({
            "title": w.get("title") or w.get("display_name"),
            "authors": authors,
            "year": w.get("publication_year"),
            "doi": w.get("doi"),
            "cited_by_count": w.get("cited_by_count"),
            "url": w.get("primary_location", {}).get("landing_page_url") or w.get("id"),
            "source": "openalex",
            "is_oa": oa.get("is_oa"),
            "oa_status": oa.get("oa_status"),
        })
    return out


# ---------------------------------------------------------------------------
# Crossref 逐条验证（V2.0 新增 — 去幻觉核心）
# ---------------------------------------------------------------------------
def _extract_doi(doi_value):
    """把 OpenAlex 的 doi 字段（完整 URL，如 https://doi.org/10.1007/s12345-024-00001-2）提取为裸 DOI。

    Crossref REST API 的按 DOI 查询端点接受裸 DOI（10.xxxx/yyyy），
    带前缀的完整 URL 会导致 404。"""
    if not doi_value:
        return None
    s = str(doi_value).strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "https://dx.doi.org/", "http://dx.doi.org/"):
        if s.lower().startswith(prefix):
            s = s[len(prefix):]
            break
    s = s.rstrip("/")
    return s or None


def _norm_title(title):
    """标题归一化：小写、去标点、压缩空白，用于跨源模糊匹配。"""
    if not title:
        return ""
    t = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", str(title).lower())
    return " ".join(t.split())


def verify_by_doi(doi, expected_title, expected_year, mailto=None):
    """按 DOI 回查 Crossref REST API（/works/{doi}），验证 OpenAlex 记录是否真实存在且元数据一致。

    Args:
        doi:            裸 DOI（如 "10.1007/s12345-024-00001-2"）
        expected_title: OpenAlex 记录的标题
        expected_year:  OpenAlex 记录的年份
        mailto:         可选，Crossref polite 池标识邮箱

    Returns:
        (ok: bool, detail: dict)
        ok=True  验证通过：Crossref 中该 DOI 真实存在，且标题相似度 ≥0.8、
                 年份差 ≤1（容忍出版年先后偏差）。
        ok=False 验证失败：title 或 year 明显不一致（疑似幻觉/错配）。
        detail: {"crossref_title", "crossref_year", "similarity", "reason"}
        reason: "match" | "title_mismatch" | "year_mismatch"
    """
    url = f"https://api.crossref.org/works/{doi}"
    params = {}
    ua = UA_BASE
    if mailto:
        params["mailto"] = mailto
        ua = f"{UA_BASE} (mailto:{mailto})"
    data = _get(url, params=params, user_agent=ua)
    msg = data.get("message", {})
    cr_title = (msg.get("title") or [None])[0]
    cr_year = None
    issued = msg.get("issued", {}).get("date-parts", [[None]])
    if issued and issued[0]:
        cr_year = issued[0][0]
    sim = 0.0
    if cr_title and expected_title:
        sim = SequenceMatcher(None, _norm_title(expected_title), _norm_title(cr_title)).ratio()
    year_ok = True
    if expected_year is not None and cr_year is not None:
        year_ok = abs(int(expected_year) - int(cr_year)) <= 1
    if sim >= 0.8 and year_ok:
        return True, {
            "crossref_title": cr_title,
            "crossref_year": cr_year,
            "similarity": round(sim, 3),
            "reason": "match",
        }
    return False, {
        "crossref_title": cr_title,
        "crossref_year": cr_year,
        "similarity": round(sim, 3),
        "reason": "title_mismatch" if sim < 0.8 else "year_mismatch",
    }


def verify_openalex_results(papers, mailto=None, skip_verify=False):
    """批量验证 OpenAlex 收割结果（去幻觉核心）。

    逐条处理:
      - 无 DOI           → unverified（保留，标记 verification="unverified"）
      - 有 DOI + 验证通过 → verified
      - 有 DOI + 验证失败 → dropped（附 reason: title_mismatch / year_mismatch）
      - 单条验证瞬时异常（网络/429/404） → 不武断判死，标记 verify_error 保留供人工参考

    Returns: (kept, dropped)
        kept    中每条含 verification 字段（verified / unverified / verify_error）
        dropped 中每条含 verification="dropped" + reason
    """
    if skip_verify:
        for p in papers:
            p["verification"] = "skipped"
        return list(papers), []
    kept, dropped = [], []
    for p in papers:
        doi = _extract_doi(p.get("doi"))
        if not doi:
            p["verification"] = "unverified"
            p["verification_note"] = "无 DOI，无法用 Crossref 交叉验证"
            kept.append(p)
            continue
        try:
            ok, detail = verify_by_doi(doi, p.get("title"), p.get("year"), mailto=mailto)
            if ok:
                p["verification"] = "verified"
                p["verification_detail"] = detail
                kept.append(p)
            else:
                p["verification"] = "dropped"
                p["verification_detail"] = detail
                dropped.append(p)
        except Exception as e:
            # 404 = DOI 在 Crossref 不存在 → 判定 dropped；其余瞬时错误保留
            if "HTTP 404" in str(e) or "404" in str(e):
                p["verification"] = "dropped"
                p["verification_detail"] = {
                    "crossref_title": None, "crossref_year": None,
                    "similarity": 0.0, "reason": "doi_not_found",
                }
                dropped.append(p)
            else:
                p["verification"] = "verify_error"
                p["verification_note"] = str(e)
                kept.append(p)
    return kept, dropped


def harvest(query, per_platform=20, verify=True, mailto=None,
            min_year=None, max_year=None, cache_dir=None, budgets=None,
            species_terms=None, tech_terms=None, task_terms=None,
            exclude_terms=None, network_consent=False):
    """OpenAlex 收割 + Crossref 逐条验证（Search B 精简两源版）。

    Args:
        query:         检索词
        per_platform:  返回数量
        verify:        是否启用 Crossref 验证（默认 True）
        mailto:        Crossref polite 池标识邮箱（可选）
        network_consent: 是否已获得本次 OpenAlex/Crossref 网络访问授权

    Returns:
        {
          "query": ...,
          "openalex": [...],       # 原始收割记录（含 verification 字段）
          "verified": [...],       # Crossref 验证通过的记录（可信候选）
          "unverified": [...],     # 无 DOI / 验证瞬时失败，保留供人工参考
          "dropped": [...],        # 验证不通过（疑似幻觉/错配）
          "statistics": {...}      # 各状态计数
        }
    """
    filtered_terms = (species_terms, tech_terms, task_terms)
    if any(terms is not None for terms in filtered_terms) and not all(filtered_terms):
        raise ValueError("三层过滤必须同时提供 species_terms、tech_terms、task_terms")
    if not network_consent:
        raise PermissionError(
            "未获得网络访问授权：调用 OpenAlex/Crossref 前必须由用户明确同意"
        )
    global _ACTIVE_BUDGET, _ACTIVE_CACHE_DIR
    previous_budget, previous_cache = _ACTIVE_BUDGET, _ACTIVE_CACHE_DIR
    _ACTIVE_BUDGET = RequestBudget(budgets)
    _ACTIVE_CACHE_DIR = None if cache_dir is False else (cache_dir or os.environ.get(
        "HARVEST_CACHE_DIR", os.path.join(os.path.expanduser("~"), ".cache", "querystrategist")))
    result = {"query": query, "openalex": [], "verified": [], "unverified": [], "dropped": [], "errors": []}
    try:
        if any(terms is not None for terms in filtered_terms):
            papers = harvest_openalex_filtered(
                species_terms, tech_terms, task_terms,
                per_platform=per_platform,
                min_year=min_year if min_year is not None else 1900,
                max_year=max_year,
                exclude_terms=exclude_terms,
            )
        else:
            papers = harvest_openalex(query, per_platform, min_year=min_year, max_year=max_year)
        result["openalex"] = papers
        kept, dropped = verify_openalex_results(papers, mailto=mailto, skip_verify=not verify)
        result["dropped"] = dropped
        result["verified"] = [p for p in kept if p.get("verification") == "verified"]
        result["unverified"] = [p for p in kept if p.get("verification") != "verified"]
        result["statistics"] = {
            "harvested": len(papers),
            "verified": len(result["verified"]),
            "unverified": len(result["unverified"]),
            "dropped": len(dropped),
            "verify_enabled": bool(verify),
            "request_budget": _ACTIVE_BUDGET.summary(),
        }
    except Exception as e:
        result["openalex_error"] = str(e)
        result["errors"].append({"stage": "openalex_or_verify", "error": str(e)})
        result["statistics"] = {
            "harvested": len(result["openalex"]),
            "verified": len(result["verified"]),
            "unverified": len(result["unverified"]),
            "dropped": len(result["dropped"]),
            "verify_enabled": bool(verify),
            "request_budget": _ACTIVE_BUDGET.summary(),
        }
    finally:
        _ACTIVE_BUDGET, _ACTIVE_CACHE_DIR = previous_budget, previous_cache
    return result


def _demo(network_consent=False):
    return harvest(
        "organ-on-a-chip drug toxicity screening",
        per_platform=3,
        verify=False,
        network_consent=network_consent,
    )


def main():
    ap = argparse.ArgumentParser(description="QueryStrategist 文献收割器（OpenAlex + Crossref 验证）")
    ap.add_argument("--query", help="检索词")
    ap.add_argument("--species", nargs="*", default=None,
                    help="对象层词；与 --technology/--task 一起启用三层过滤")
    ap.add_argument("--technology", nargs="*", default=None,
                    help="必需技术锚点词；与 --species/--task 一起启用三层过滤")
    ap.add_argument("--task", nargs="*", default=None,
                    help="任务层词；与 --species/--technology 一起启用三层过滤")
    ap.add_argument("--exclude", nargs="*", default=None,
                    help="三层过滤模式下在标题和摘要中本地排除的词")
    ap.add_argument("--per-platform", type=int, default=20)
    ap.add_argument("--min-year", type=int, default=None, help="最早发表年份（含）")
    ap.add_argument("--max-year", type=int, default=None, help="最晚发表年份（含）")
    ap.add_argument("--verify", dest="verify", action="store_true", default=True,
                    help="启用 Crossref 逐条验证（默认开启）")
    ap.add_argument("--no-verify", dest="verify", action="store_false",
                    help="跳过 Crossref 验证（仅收割，不校验）")
    ap.add_argument("--mailto", default=None,
                    help="Crossref polite 池标识邮箱（可选，验证请求附上可获更高限速）")
    ap.add_argument("--out", help="输出 JSON 路径")
    ap.add_argument("--cache-dir", default=None, help="响应缓存目录；传 --no-cache 关闭缓存")
    ap.add_argument("--no-cache", action="store_true", help="关闭响应缓存")
    ap.add_argument("--openalex-budget", type=int, default=None, help="本次 OpenAlex 请求预算")
    ap.add_argument("--crossref-budget", type=int, default=None, help="本次 Crossref 请求预算")
    ap.add_argument("--network-consent", action="store_true",
                    help="确认用户已授权访问 api.openalex.org 和 api.crossref.org")
    ap.add_argument("--dry-run", action="store_true", help="只检查参数与预算，不发起网络请求")
    ap.add_argument("--no-bootstrap", action="store_true", default=False,
                    help="禁用自动安装依赖（依赖由用户自行管理；等价于设 HARVEST_NO_BOOTSTRAP=1，适合离线环境）")
    ap.add_argument("--check-deps", action="store_true", default=False,
                    help="仅检查/安装依赖后退出（首次使用前验证环境是否就绪，不发起任何检索）")
    args = ap.parse_args()

    tier_values = (args.species, args.technology, args.task)
    tier_mode = any(value is not None for value in tier_values)
    if tier_mode and not all(tier_values):
        ap.error("--species、--technology、--task 必须同时提供且每组至少包含一个词")
    trace_query = args.query or (
        " ".join([*args.species, *args.technology, *args.task]) if tier_mode else None
    )

    if args.check_deps:
        missing, installed = ensure_deps(auto_install=not args.no_bootstrap)
        if installed:
            print(f"[check-deps] 已自动安装缺失依赖: {', '.join(installed)}")
        if missing and not installed:
            print(f"[check-deps] 仍有缺失（自动安装失败，请手动执行 pip install {' '.join(missing)}）")
        elif not missing:
            print("[check-deps] 依赖齐全，环境就绪 ✅")
        return

    if args.dry_run:
        print(json.dumps({
            "dry_run": True,
            "query": trace_query or "<demo>",
            "tier_mode": tier_mode,
            "species": args.species,
            "technology": args.technology,
            "task": args.task,
            "exclude": args.exclude,
            "per_platform": args.per_platform,
            "min_year": args.min_year,
            "max_year": args.max_year,
            "verify": args.verify,
            "network_consent": args.network_consent,
            "budgets": {
                "openalex": args.openalex_budget or int(os.environ.get("HARVEST_OPENALEX_BUDGET", "120")),
                "crossref": args.crossref_budget or int(os.environ.get("HARVEST_CROSSREF_BUDGET", "60")),
            },
            "network_requests": 0,
        }, ensure_ascii=False, indent=2))
        return

    if not args.network_consent:
        ap.error("发起 API 请求前必须先获得用户授权，并显式传入 --network-consent")

    bootstrap_installed = []
    bootstrap_disabled = args.no_bootstrap or os.environ.get("HARVEST_NO_BOOTSTRAP") == "1"
    if requests is None and not bootstrap_disabled:
        _missing, bootstrap_installed = ensure_deps(auto_install=True)
        _load_third_party()
    if requests is None:
        raise SystemExit("缺少依赖 requests；请运行 --check-deps 或 pip install -r scripts/requirements.txt")
    if bootstrap_installed:
        print(f"[bootstrap] 首次运行已自动安装缺失依赖: {', '.join(bootstrap_installed)}")

    if args.query or tier_mode:
        result = harvest(trace_query, args.per_platform,
                         verify=args.verify, mailto=args.mailto,
                         min_year=args.min_year, max_year=args.max_year,
                         cache_dir=False if args.no_cache else args.cache_dir,
                         budgets={"openalex": args.openalex_budget,
                                  "crossref": args.crossref_budget},
                          species_terms=args.species,
                          tech_terms=args.technology,
                          task_terms=args.task,
                          exclude_terms=args.exclude,
                          network_consent=args.network_consent)
    else:
        print("[demo] 未提供 --query，使用示例检索词:\n")
        result = _demo(network_consent=args.network_consent)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写入 {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
