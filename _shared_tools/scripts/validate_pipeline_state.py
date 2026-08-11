"""Validate a QueryStrategist project configuration and persisted pipeline state."""

import argparse
import json
import sys
from pathlib import Path


CONFIG_FIELDS = (
    "interaction_language",
    "target_language",
    "writing_type",
    "literature_time_span",
)
META_FIELDS = (
    "project_id",
    "pipeline_step",
    "progress_pct",
    "writing_type",
    "target_language",
)


def _load(path, errors):
    if not path.is_file():
        errors.append(f"missing: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON: {path} ({exc})")
        return None


def validate_project(project_dir):
    """Return a list of structural errors; an empty list means valid."""
    project_dir = Path(project_dir).resolve()
    errors = []
    if not project_dir.is_dir():
        return [f"project directory does not exist: {project_dir}"]

    config = _load(project_dir / "pipeline_state" / "config.json", errors)
    meta = _load(project_dir / "project_meta.json", errors)

    if isinstance(config, dict):
        for field in CONFIG_FIELDS:
            if field not in config:
                errors.append(f"config missing field: {field}")
        span = config.get("literature_time_span")
        if not isinstance(span, dict):
            errors.append("config literature_time_span must be an object")
        else:
            start, end = span.get("start"), span.get("end")
            if not isinstance(start, int) or not isinstance(end, int):
                errors.append("config literature_time_span.start/end must be integers")
            elif start > end:
                errors.append("config literature_time_span.start must be <= end")

    if isinstance(meta, dict):
        for field in META_FIELDS:
            if field not in meta:
                errors.append(f"project_meta missing field: {field}")
        progress = meta.get("progress_pct")
        if not isinstance(progress, (int, float)) or not 0 <= progress <= 100:
            errors.append("project_meta progress_pct must be between 0 and 100")

    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate QueryStrategist project state")
    parser.add_argument("--project", required=True, help="project directory under projects/")
    args = parser.parse_args(argv)
    errors = validate_project(args.project)
    print(f"project: {Path(args.project).resolve()}")
    print(f"errors: {len(errors)}")
    for error in errors:
        print(f"  [ERROR] {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
