"""Normalize QueryStrategist deliverables and render readable offline HTML."""

import argparse
import html
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path


WORKBENCH_PATH = Path(__file__).with_name("html_workbench.py")
WORKBENCH_SPEC = importlib.util.spec_from_file_location(
    "querystrategist_html_workbench", WORKBENCH_PATH
)
WORKBENCH = importlib.util.module_from_spec(WORKBENCH_SPEC)
WORKBENCH_SPEC.loader.exec_module(WORKBENCH)


DEFAULT_MARKDOWN = (
    "scope_card.md",
    "query_pack.md",
    "candidate_list.md",
    "usage_guide.md",
)
DEFAULT_CSV = ("candidate_list.csv",)
BILINGUAL_SIDECARS = {
    "scope_card": "scope_card.i18n.json",
    "usage_guide": "usage_guide.i18n.json",
}

PROSE_REPLACEMENTS = {
    "✅": "[已验证]",
    "⚠️": "[注意]",
    "⚠": "[注意]",
    "❌": "[已剔除]",
    "→": "->",
    "≥": ">=",
    "≤": "<=",
    "—": "-",
    "–": "-",
}


def _read_utf8(path):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig", errors="strict")
    if "\ufffd" in text:
        raise ValueError(f"replacement character U+FFFD found in {path}")
    return text


def normalize_markdown(text):
    """Replace fragile display glyphs in prose while preserving fenced code."""
    lines = []
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            lines.append(line)
            continue
        if not in_code:
            for source, target in PROSE_REPLACEMENTS.items():
                line = line.replace(source, target)
        lines.append(line)
    if in_code:
        raise ValueError("unclosed fenced code block")
    return "\n".join(lines).rstrip() + "\n"


def _inline(text):
    value = html.escape(text, quote=True)
    value = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        value,
    )
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    return value


def _is_table_separator(line):
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells)


def _table_cells(line):
    return [
        cell.replace(r"\|", "|").strip()
        for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))
    ]


def _markdown_tables(markdown_text):
    """Return Markdown tables as (headers, rows) pairs."""
    lines = markdown_text.splitlines()
    tables = []
    index = 0
    while index + 1 < len(lines):
        if lines[index].startswith("|") and _is_table_separator(lines[index + 1]):
            headers = _table_cells(lines[index])
            index += 2
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                row = _table_cells(lines[index])
                rows.append(row + [""] * (len(headers) - len(row)))
                index += 1
            tables.append((headers, rows))
            continue
        index += 1
    return tables


def _section_paragraph(markdown_text, heading_pattern):
    lines = markdown_text.splitlines()
    for index, line in enumerate(lines):
        heading = re.match(r"^#{1,6}\s+(.+)$", line)
        if not heading or not re.search(heading_pattern, heading.group(1), re.I):
            continue
        paragraphs = []
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if not stripped:
                if paragraphs:
                    break
                continue
            if re.match(r"^#{1,6}\s+|^\||^```|^>|^[-*]\s+|^\d+\.\s+|^---$", stripped):
                break
            paragraphs.append(stripped)
        if paragraphs:
            return " ".join(paragraphs)
    return ""


def _configuration(markdown_text):
    values = {}
    for headers, rows in _markdown_tables(markdown_text):
        if len(headers) < 2:
            continue
        first = headers[0].strip().lower()
        second = headers[1].strip().lower()
        if first not in {"field", "dimension", "配置项", "字段"} and second not in {
            "value",
            "selection",
            "值",
            "选择",
        }:
            continue
        for row in rows:
            if len(row) >= 2 and row[0].strip():
                values[row[0].strip().lower()] = row[1].strip()
    return values


def _find_header(headers, terms):
    normalized = [header.strip().lower() for header in headers]
    for index, value in enumerate(normalized):
        if any(term in value for term in terms):
            return index
    return -1


def _candidate_summary(markdown_text):
    tables = _markdown_tables(markdown_text)
    if not tables:
        return {"candidate_count": 0, "verified_count": 0, "oa_count": 0}
    headers, rows = max(tables, key=lambda item: len(item[1]))
    status_index = _find_header(headers, ("verification", "status", "验证", "状态"))
    oa_index = _find_header(headers, ("oa", "开放获取"))
    verified = 0
    open_access = 0
    for row in rows:
        status = row[status_index].lower() if 0 <= status_index < len(row) else ""
        if (
            "unverified" not in status
            and "待人工" not in status
            and ("verified" in status or "已验证" in status)
        ):
            verified += 1
        oa = row[oa_index].lower() if 0 <= oa_index < len(row) else ""
        if not any(term in oa for term in ("非oa", "closed", "false")) and any(
            term in oa for term in ("oa", "gold", "green", "hybrid", "bronze", "open")
        ):
            open_access += 1
    return {
        "candidate_count": len(rows),
        "verified_count": verified,
        "oa_count": open_access,
    }


def _shorten_title(value, limit=150):
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("**", "").replace("__", "").replace("`", "")
    value = re.sub(r"\s+", " ", value).strip().rstrip("。.")
    if len(value) <= limit:
        return value
    for separator in ("。", ";", "；", ",", "，"):
        position = value.find(separator, 35, min(limit, len(value)))
        if position >= 0:
            return value[:position].rstrip()
    boundary = value.rfind(" ", 0, limit - 3)
    if boundary < limit // 2:
        boundary = limit - 3
    return value[:boundary].rstrip() + "..."


def _query_qa_status(markdown_text):
    statuses = []
    for line in markdown_text.splitlines():
        if not re.search(r"query\s*qa|总体状态|overall status|qa status", line, re.I):
            continue
        found = set(re.findall(r"\b(PASS|WARNING|FAIL)\b", line, re.I))
        if len(found) == 1:
            statuses.append(next(iter(found)).upper())
    for status in ("FAIL", "WARNING", "PASS"):
        if status in statuses:
            return status
    return "未标注"


def _build_summary(normalized_files):
    scope = normalized_files.get("scope_card", "")
    query_pack = normalized_files.get("query_pack", "")
    candidate_list = normalized_files.get("candidate_list", "")
    first_heading = re.search(r"^#\s+(.+)$", scope, re.M)
    heading_title = first_heading.group(1).strip() if first_heading else ""
    normalized_heading = heading_title.lower()
    is_generic = (
        normalized_heading.startswith("scope card")
        or normalized_heading in {"research scope", "研究范围"}
        or "范围卡" in heading_title
    )
    project_title = "" if is_generic else heading_title
    if not project_title:
        project_title = _section_paragraph(
            scope,
            r"^(confirmed scope|scope|research scope|core research direction|研究范围|范围|核心研究方向|研究方向|确认范围|已确认范围)(?:【.*】)?$",
        )
    if not project_title:
        project_title = "检索策略包"
    project_title = _shorten_title(project_title)

    config = _configuration(scope)
    writing_type = next(
        (config[key] for key in config if "writing type" in key or "写作类型" in key),
        "",
    )
    if not writing_type:
        writing_match = re.search(r"写作类型\s*[:：]\s*(?:\*\*)?([^*（(\n]+)", scope)
        writing_type = writing_match.group(1).strip() if writing_match else ""
    time_span = next(
        (
            config[key]
            for key in config
            if "time span" in key or "时间范围" in key or "时间跨度" in key
        ),
        "",
    )
    fence_count = sum(
        1 for line in query_pack.splitlines() if line.strip().startswith("```")
    )
    summary = {
        "project_title": project_title,
        "generated_on": date.today().isoformat(),
        "writing_type": writing_type,
        "time_span": time_span,
        "query_count": fence_count // 2,
        "qa_status": _query_qa_status(query_pack),
    }
    summary.update(_candidate_summary(candidate_list))
    return summary


def _render_markdown_body(markdown_text):
    """Render the controlled Markdown subset used by QueryStrategist outputs."""
    lines = markdown_text.splitlines()
    body = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index >= len(lines):
                raise ValueError("unclosed fenced code block")
            class_name = (
                f' class="language-{html.escape(language)}"' if language else ""
            )
            body.append(
                f"<pre><code{class_name}>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            index += 1
            continue

        if (
            line.startswith("|")
            and index + 1 < len(lines)
            and _is_table_separator(lines[index + 1])
        ):
            headers = _table_cells(line)
            index += 2
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append(_table_cells(lines[index]))
                index += 1
            head = "".join(f"<th>{_inline(cell)}</th>" for cell in headers)
            table_rows = []
            for row in rows:
                padded = row + [""] * (len(headers) - len(row))
                table_rows.append(
                    "<tr>"
                    + "".join(
                        f"<td>{_inline(cell)}</td>" for cell in padded[: len(headers)]
                    )
                    + "</tr>"
                )
            body.append(
                f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
                f"<tbody>{''.join(table_rows)}</tbody></table></div>"
            )
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            body.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if stripped == "---":
            body.append("<hr>")
            index += 1
            continue

        if line.startswith("> "):
            quotes = []
            while index < len(lines) and lines[index].startswith(">"):
                quotes.append(lines[index].lstrip("> "))
                index += 1
            body.append(
                f"<blockquote>{'<br>'.join(_inline(item) for item in quotes)}</blockquote>"
            )
            continue

        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while index < len(lines) and re.match(r"^\s*[-*]\s+", lines[index]):
                item = re.sub(r"^\s*[-*]\s+", "", lines[index])
                items.append(f"<li>{_inline(item)}</li>")
                index += 1
            body.append(f"<ul>{''.join(items)}</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while index < len(lines) and re.match(r"^\s*\d+\.\s+", lines[index]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[index])
                items.append(f"<li>{_inline(item)}</li>")
                index += 1
            body.append(f"<ol>{''.join(items)}</ol>")
            continue

        paragraphs = [stripped]
        index += 1
        while (
            index < len(lines)
            and lines[index].strip()
            and not re.match(
                r"^(#{1,6})\s+|^```|^\||^>\s|^\s*[-*]\s+|^\s*\d+\.\s+|^---$",
                lines[index],
            )
        ):
            paragraphs.append(lines[index].strip())
            index += 1
        body.append(f"<p>{_inline(' '.join(paragraphs))}</p>")

    return "".join(body)


def _normalize_language(value):
    normalized = str(value or "").strip().lower().replace("_", "-")
    if normalized.startswith("zh"):
        return "zh"
    if normalized.startswith("en"):
        return "en"
    raise ValueError(f"unsupported bilingual content language: {value!r}")


def _load_bilingual_content(directory, page_key, source_markdown):
    sidecar_name = BILINGUAL_SIDECARS.get(page_key)
    if not sidecar_name:
        return None, None
    sidecar_path = Path(directory) / sidecar_name
    if not sidecar_path.is_file():
        return None, None
    try:
        payload = json.loads(_read_utf8(sidecar_path))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {sidecar_path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"{sidecar_path} must use schema_version 1")
    source_language = _normalize_language(payload.get("source_language"))
    translations = payload.get("translations")
    if not isinstance(translations, dict) or not translations:
        raise ValueError(f"{sidecar_path} must contain a non-empty translations object")
    documents = {source_language: source_markdown}
    for language, markdown_text in translations.items():
        normalized_language = _normalize_language(language)
        if normalized_language == source_language:
            raise ValueError(
                f"{sidecar_path} repeats source language {source_language!r}"
            )
        if not isinstance(markdown_text, str) or not markdown_text.strip():
            raise ValueError(
                f"{sidecar_path} translation {language!r} must be non-empty Markdown"
            )
        normalized_markdown = normalize_markdown(markdown_text)
        if not re.search(r"^#\s+\S", normalized_markdown, re.M):
            raise ValueError(
                f"{sidecar_path} translation {language!r} must contain an H1 heading"
            )
        documents[normalized_language] = normalized_markdown
    if set(documents) != {"zh", "en"}:
        raise ValueError(
            f"{sidecar_path} must provide both Chinese and English content"
        )
    return {
        "source_language": source_language,
        "documents": documents,
    }, sidecar_path


def _render_page_body(markdown_text, bilingual_content=None):
    if not bilingual_content:
        return _render_markdown_body(markdown_text)
    source_language = bilingual_content["source_language"]
    panels = []
    for language in (source_language, "zh" if source_language == "en" else "en"):
        source = ' data-content-source="true"' if language == source_language else ""
        hidden = "" if language == source_language else " hidden"
        panels.append(
            f'<section class="document-language-panel" data-content-lang="{language}"'
            f"{source}{hidden}>"
            f"{_render_markdown_body(bilingual_content['documents'][language])}</section>"
        )
    return "".join(panels)


def markdown_to_html(
    markdown_text,
    title,
    page_key=None,
    available_pages=None,
    summary=None,
    bilingual_content=None,
):
    page_key = page_key or title
    available_pages = available_pages or [page_key]
    return WORKBENCH.shell(
        title,
        _render_page_body(markdown_text, bilingual_content),
        page_key,
        available_pages,
        summary=summary,
    )


def _write_bom(path, text):
    with Path(path).open("w", encoding="utf-8-sig", newline="\n") as stream:
        stream.write(text)


def process_directory(
    directory, markdown_names=DEFAULT_MARKDOWN, csv_names=DEFAULT_CSV
):
    directory = Path(directory).resolve()
    processed = []
    normalized_files = {}
    for name in markdown_names:
        path = directory / name
        if not path.is_file():
            continue
        normalized = normalize_markdown(_read_utf8(path))
        _write_bom(path, normalized)
        normalized_files[path.stem] = normalized
        processed.append(path)

    available_pages = [key for key in WORKBENCH.PAGE_META if key in normalized_files]
    summary = _build_summary(normalized_files)
    for key in available_pages:
        path = directory / f"{key}.md"
        html_path = path.with_suffix(".html")
        title = WORKBENCH.PAGE_META[key][1]
        bilingual_content, sidecar_path = _load_bilingual_content(
            directory, key, normalized_files[key]
        )
        _write_bom(
            html_path,
            markdown_to_html(
                normalized_files[key],
                title,
                key,
                available_pages,
                summary,
                bilingual_content,
            ),
        )
        processed.append(html_path)
        if sidecar_path:
            processed.append(sidecar_path)

    if available_pages:
        index_path = directory / "index.html"
        _write_bom(index_path, WORKBENCH.index_page(available_pages, summary))
        processed.append(index_path)
    for name in csv_names:
        path = directory / name
        if not path.is_file():
            continue
        text = _read_utf8(path)
        _write_bom(path, text)
        processed.append(path)
    if not processed:
        raise FileNotFoundError(f"no deliverables found in {directory}")
    return processed


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Normalize Markdown/CSV and render offline HTML"
    )
    parser.add_argument(
        "--directory", required=True, help="directory containing the strategy pack"
    )
    args = parser.parse_args(argv)
    try:
        processed = process_directory(args.directory)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print("processed:")
    for path in processed:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
