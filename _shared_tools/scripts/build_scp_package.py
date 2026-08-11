"""从 QueryStrategist 开发包构建 SCP 单包发布目录。"""

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
from pathlib import Path


EXCLUDED_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".cache",
    "projects",
}
EXCLUDED_PATTERNS = (
    ".env",
    ".env.*",
    "harvest*.json",
    "literature_collection*.json",
    "literature_collection*.md",
    "candidate_list.*",
    "scope_card.*",
    "query_pack.*",
    "usage_guide.*",
    "BUILD_MANIFEST.json",
)


def _ignore(_directory, names):
    return {
        name
        for name in names
        if (
            name != ".env.example"
            and (
                name in EXCLUDED_NAMES
                or any(fnmatch.fnmatchcase(name, pattern) for pattern in EXCLUDED_PATTERNS)
                or name.endswith((".pyc", ".pyo", ".log", ".token", ".key", ".pem"))
            )
        )
    }


def _validate_paths(source, destination):
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_dir() or not (source / "SKILL.md").is_file():
        raise ValueError(f"源目录不是 QueryStrategist 包: {source}")
    if source == destination or source in destination.parents:
        raise ValueError("目标目录不能等于源目录或位于源目录内部")
    if not destination.name.lower().endswith("_scp"):
        raise ValueError("为防误删，目标目录名必须以 _SCP 结尾")
    return source, destination


def _convert_subskills(stage):
    converted = 0
    for child in stage.iterdir():
        if not child.is_dir() or child.name.startswith(".") or child.name == "_shared_tools":
            continue
        local_skill = child / "SKILL.md"
        if local_skill.is_file():
            local_skill.replace(child / "SKILL.sub.md")
            converted += 1
    return converted


def _write_manifest(stage):
    files = []
    for path in sorted(stage.rglob("*")):
        if not path.is_file() or path.name == "BUILD_MANIFEST.json":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": path.relative_to(stage).as_posix(), "sha256": digest})
    version_path = stage / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else None
    (stage / "BUILD_MANIFEST.json").write_text(
        json.dumps({"version": version, "files": files}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build(source, destination, force=False):
    source, destination = _validate_paths(Path(source), Path(destination))
    stage = destination.with_name(f"{destination.name}.staging")
    if stage.exists():
        raise FileExistsError(f"构建暂存目录已存在，请先人工处理: {stage}")
    shutil.copytree(source, stage, ignore=_ignore)

    converted = _convert_subskills(stage)
    if converted != 11:
        shutil.rmtree(stage)
        raise RuntimeError(f"子模块转换数量异常: 期望 11，实际 {converted}")
    if not (stage / "SKILL.md").is_file():
        shutil.rmtree(stage)
        raise RuntimeError("staging 缺少根 SKILL.md")
    _write_manifest(stage)

    if destination.exists() and not force:
        shutil.rmtree(stage)
        raise FileExistsError(f"目标目录已存在；如需覆盖请显式传 --force: {destination}")
    backup = destination.with_name(f"{destination.name}.backup")
    if destination.exists():
        if backup.exists():
            shutil.rmtree(stage)
            raise FileExistsError(
                f"检测到上次发布备份仍存在，请先人工确认并处理: {backup}"
            )
        os.replace(destination, backup)
        try:
            os.replace(stage, destination)
        except Exception:
            if destination.exists():
                shutil.rmtree(destination)
            os.replace(backup, destination)
            raise
        shutil.rmtree(backup)
    else:
        os.replace(stage, destination)
    return destination, converted


def main():
    parser = argparse.ArgumentParser(description="构建 QueryStrategist SCP 单包")
    default_source = Path(__file__).resolve().parents[2]
    parser.add_argument("--source", default=str(default_source))
    parser.add_argument("--destination", required=True)
    parser.add_argument("--force", action="store_true",
                        help="显式允许覆盖已有 _SCP 目标目录")
    args = parser.parse_args()
    destination, converted = build(args.source, args.destination, force=args.force)
    print(f"built: {destination}")
    print(f"converted_subskills: {converted}")


if __name__ == "__main__":
    main()
