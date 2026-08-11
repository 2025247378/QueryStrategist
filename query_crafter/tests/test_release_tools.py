import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "_shared_tools" / "scripts" / "build_scp_package.py"
STATE_VALIDATOR_PATH = Path(__file__).parents[2] / "_shared_tools" / "scripts" / "validate_pipeline_state.py"
RENDERER_PATH = Path(__file__).parents[2] / "_shared_tools" / "scripts" / "render_deliverables.py"
SPEC = importlib.util.spec_from_file_location("build_scp_package", MODULE_PATH)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
STATE_SPEC = importlib.util.spec_from_file_location("validate_pipeline_state", STATE_VALIDATOR_PATH)
STATE_VALIDATOR = importlib.util.module_from_spec(STATE_SPEC)
STATE_SPEC.loader.exec_module(STATE_VALIDATOR)
RENDERER_SPEC = importlib.util.spec_from_file_location("render_deliverables", RENDERER_PATH)
RENDERER = importlib.util.module_from_spec(RENDERER_SPEC)
RENDERER_SPEC.loader.exec_module(RENDERER)


class ReleaseToolTests(unittest.TestCase):
    def test_ignore_excludes_runtime_and_secret_files_but_keeps_example(self):
        ignored = BUILDER._ignore(Path("."), [
            ".env", ".env.example", "harvest-demo.json", "candidate_list.csv",
            "scope_card.html", "query_pack.md", "usage_guide.html",
            "normal.md", "private.pem",
        ])
        self.assertIn(".env", ignored)
        self.assertNotIn(".env.example", ignored)
        self.assertIn("harvest-demo.json", ignored)
        self.assertIn("candidate_list.csv", ignored)
        self.assertIn("scope_card.html", ignored)
        self.assertIn("query_pack.md", ignored)
        self.assertIn("usage_guide.html", ignored)
        self.assertIn("private.pem", ignored)
        self.assertNotIn("normal.md", ignored)

    def test_build_writes_manifest_and_requires_explicit_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            destination = Path(tmp) / "package_SCP"
            source.mkdir()
            (source / "SKILL.md").write_text("root", encoding="utf-8")
            (source / ".env").write_text("SECRET=do-not-copy", encoding="utf-8")
            (source / "VERSION").write_text("4.4.0", encoding="utf-8")
            for index in range(11):
                child = source / f"module_{index}"
                child.mkdir()
                (child / "SKILL.md").write_text("child", encoding="utf-8")

            BUILDER.build(source, destination)
            manifest = json.loads((destination / "BUILD_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], "4.4.0")
            self.assertFalse((destination / ".env").exists())
            self.assertTrue((destination / "module_0" / "SKILL.sub.md").exists())
            with self.assertRaises(FileExistsError):
                BUILDER.build(source, destination)
            BUILDER.build(source, destination, force=True)
            self.assertFalse(destination.with_name("package_SCP.backup").exists())

    def test_pipeline_state_validator_accepts_structured_year_span(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "projects" / "fish_20260811"
            (project / "pipeline_state").mkdir(parents=True)
            (project / "pipeline_state" / "config.json").write_text(json.dumps({
                "interaction_language": "zh",
                "target_language": "简体中文",
                "writing_type": "综述",
                "literature_time_span": {"start": 2016, "end": 2026},
            }), encoding="utf-8")
            (project / "project_meta.json").write_text(json.dumps({
                "project_id": "fish_20260811",
                "pipeline_step": "Step 0",
                "progress_pct": 5,
                "writing_type": "综述",
                "target_language": "简体中文",
            }), encoding="utf-8")
            self.assertEqual(STATE_VALIDATOR.validate_project(project), [])

    def test_deliverable_renderer_adds_bom_html_and_preserves_query_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            markdown = directory / "query_pack.md"
            markdown.write_text(
                "# 检索式\n\n⚠️ 验证状态 ≥ 1\n\n"
                "## Web of Science\n\n```text\nA ≥ B → C\n```\n\n"
                "## Scopus\n\n```text\nTITLE-ABS-KEY(fish)\n```\n",
                encoding="utf-8",
            )
            (directory / "scope_card.md").write_text(
                "# 范围卡\n\n## 三级关键词\n\n- 对象：fish\n",
                encoding="utf-8",
            )
            (directory / "candidate_list.md").write_text(
                "# 候选文献\n\n| Title | Year | Verification | OA状态 |\n"
                "|---|---|---|---|\n| Fish paper | 2025 | [已验证] verified | gold |\n",
                encoding="utf-8",
            )
            (directory / "usage_guide.md").write_text(
                "# 使用说明\n\n## WoS\n\n进入高级检索。\n",
                encoding="utf-8",
            )
            csv_path = directory / "candidate_list.csv"
            csv_path.write_text("title,status\n中文标题,verified\n", encoding="utf-8")

            processed = RENDERER.process_directory(directory)

            self.assertIn(markdown.with_suffix(".html"), processed)
            self.assertTrue(markdown.read_bytes().startswith(b"\xef\xbb\xbf"))
            normalized = markdown.read_text(encoding="utf-8-sig")
            self.assertIn("[注意] 验证状态 >= 1", normalized)
            self.assertIn("A ≥ B → C", normalized)
            rendered = markdown.with_suffix(".html").read_text(encoding="utf-8-sig")
            self.assertIn('<meta charset="utf-8">', rendered)
            self.assertIn("A ≥ B → C", rendered)
            self.assertIn('class="topbar"', rendered)
            self.assertIn('data-page="query_pack"', rendered)
            self.assertIn("复制检索式", rendered)
            self.assertNotIn("<script src=", rendered)
            self.assertNotIn("<link rel=", rendered)
            candidate_html = (directory / "candidate_list.html").read_text(encoding="utf-8-sig")
            self.assertIn("candidate-search", candidate_html)
            index_html = (directory / "index.html").read_text(encoding="utf-8-sig")
            self.assertIn("离线检索工作台", index_html)
            self.assertIn('href="query_pack.html"', index_html)
            self.assertTrue((directory / "index.html").read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertTrue(csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()
