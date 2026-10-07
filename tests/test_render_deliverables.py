import importlib.util
import json
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "_shared_tools" / "scripts" / "render_deliverables.py"
SPEC = importlib.util.spec_from_file_location("render_deliverables", SCRIPT)
RENDERER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RENDERER)


def _write(directory, name, text):
    (directory / name).write_text(text, encoding="utf-8")


def test_process_directory_builds_embedded_index_and_archive(tmp_path):
    _write(
        tmp_path,
        "scope_card.md",
        "# Scope Card\n\n## Research Scope\n\nMedical imaging quality assessment.\n\n| Field | Value |\n| --- | --- |\n| Writing Type | Review |\n",
    )
    _write(
        tmp_path,
        "query_pack.md",
        "# Query Pack\n\n## Web of Science\n\n### A0\n\n```text\nTS=(medical imaging)\n```\n",
    )
    _write(
        tmp_path,
        "candidate_list.md",
        "# Candidate List\n\n## Candidate Literature List\n\n| No. | Title | Year | DOI | Verification Status | OA Status |\n| --- | --- | --- | --- | --- | --- |\n| 1 | Example paper | 2025 | 10.1234/example | verified | gold |\n",
    )
    _write(
        tmp_path,
        "usage_guide.md",
        "# Usage Guide\n\n## How to use\n\nPaste each query into the matching database.\n",
    )
    _write(
        tmp_path,
        "scope_card.i18n.json",
        json.dumps(
            {
                "schema_version": 1,
                "source_language": "en",
                "translations": {
                    "zh": "# 范围卡\n\n## 研究范围\n\n医学影像质量评估。\n\n| 字段 | 值 |\n| --- | --- |\n| 写作类型 | 综述 |\n"
                },
            },
            ensure_ascii=False,
        ),
    )
    _write(
        tmp_path,
        "usage_guide.i18n.json",
        json.dumps(
            {
                "schema_version": 1,
                "source_language": "en",
                "translations": {
                    "zh": "# 使用说明\n\n## 如何使用\n\n将每条检索式粘贴到对应数据库。\n"
                },
            },
            ensure_ascii=False,
        ),
    )

    processed = RENDERER.process_directory(tmp_path)
    index = (tmp_path / "index.html").read_text(encoding="utf-8-sig")
    assert "id=\"document-scope_card\"" in index
    assert "id=\"document-query_pack\"" in index
    assert "id=\"document-candidate_list\"" in index
    assert "id=\"document-usage_guide\"" in index
    assert 'href="scope_card.html"' not in index
    assert (tmp_path / RENDERER.ARCHIVE_NAME) in processed

    with zipfile.ZipFile(tmp_path / RENDERER.ARCHIVE_NAME) as archive:
        names = set(archive.namelist())
    assert "index.html" not in names
    assert RENDERER.ARCHIVE_NAME not in names
    assert "scope_card.md" in names
    assert "scope_card.html" in names
    assert "candidate_list.csv" not in names

