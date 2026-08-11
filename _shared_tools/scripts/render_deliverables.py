"""Normalize QueryStrategist deliverables and render readable offline HTML."""

import argparse
import codecs
import html
import importlib.util
import re
import sys
from pathlib import Path


WORKBENCH_PATH = Path(__file__).with_name("html_workbench.py")
WORKBENCH_SPEC = importlib.util.spec_from_file_location("querystrategist_html_workbench", WORKBENCH_PATH)
WORKBENCH = importlib.util.module_from_spec(WORKBENCH_SPEC)
WORKBENCH_SPEC.loader.exec_module(WORKBENCH)


DEFAULT_MARKDOWN = (
    "scope_card.md",
    "query_pack.md",
    "candidate_list.md",
    "usage_guide.md",
)
DEFAULT_CSV = ("candidate_list.csv",)

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
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _table_cells(line):
    return [cell.replace(r"\|", "|").strip() for cell in re.split(
        r"(?<!\\)\|", line.strip().strip("|")
    )]


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
            class_name = f' class="language-{html.escape(language)}"' if language else ""
            body.append(f"<pre><code{class_name}>{html.escape(chr(10).join(code_lines))}</code></pre>")
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines) and _is_table_separator(lines[index + 1]):
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
                table_rows.append("<tr>" + "".join(
                    f"<td>{_inline(cell)}</td>" for cell in padded[:len(headers)]
                ) + "</tr>")
            body.append(f"<div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead>"
                        f"<tbody>{''.join(table_rows)}</tbody></table></div>")
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
            body.append(f"<blockquote>{'<br>'.join(_inline(item) for item in quotes)}</blockquote>")
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
        while index < len(lines) and lines[index].strip() and not re.match(
            r"^(#{1,6})\s+|^```|^\||^>\s|^\s*[-*]\s+|^\s*\d+\.\s+|^---$",
            lines[index],
        ):
            paragraphs.append(lines[index].strip())
            index += 1
        body.append(f"<p>{_inline(' '.join(paragraphs))}</p>")

    return "".join(body)


def markdown_to_html(markdown_text, title, page_key=None, available_pages=None):
    page_key = page_key or title
    available_pages = available_pages or [page_key]
    return WORKBENCH.shell(
        title,
        _render_markdown_body(markdown_text),
        page_key,
        available_pages,
    )


def _write_bom(path, text):
    with Path(path).open("w", encoding="utf-8-sig", newline="\n") as stream:
        stream.write(text)


def process_directory(directory, markdown_names=DEFAULT_MARKDOWN, csv_names=DEFAULT_CSV):
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
    for key in available_pages:
        path = directory / f"{key}.md"
        html_path = path.with_suffix(".html")
        title = WORKBENCH.PAGE_META[key][1]
        _write_bom(html_path, markdown_to_html(
            normalized_files[key], title, key, available_pages
        ))
        processed.append(html_path)

    if available_pages:
        index_path = directory / "index.html"
        _write_bom(index_path, WORKBENCH.index_page(available_pages))
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
    parser = argparse.ArgumentParser(description="Normalize Markdown/CSV and render offline HTML")
    parser.add_argument("--directory", required=True, help="directory containing the strategy pack")
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
