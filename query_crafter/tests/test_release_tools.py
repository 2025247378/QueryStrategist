import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "_shared_tools" / "scripts" / "build_scp_package.py"
SPEC = importlib.util.spec_from_file_location("build_scp_package", MODULE_PATH)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class ReleaseToolTests(unittest.TestCase):
    def test_ignore_excludes_runtime_and_secret_files_but_keeps_example(self):
        ignored = BUILDER._ignore(Path("."), [
            ".env", ".env.example", "harvest-demo.json", "candidate_list.csv",
            "normal.md", "private.pem",
        ])
        self.assertIn(".env", ignored)
        self.assertNotIn(".env.example", ignored)
        self.assertIn("harvest-demo.json", ignored)
        self.assertIn("candidate_list.csv", ignored)
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


if __name__ == "__main__":
    unittest.main()
