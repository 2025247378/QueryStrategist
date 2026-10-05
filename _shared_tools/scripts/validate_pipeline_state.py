"""Validate a QueryStrategist project configuration and persisted pipeline state."""

import argparse
import json
import sys
from pathlib import Path


CONFIG_FIELDS = (
    "research_direction",
    "interaction_language",
    "target_language",
    "writing_type",
    "literature_time_span",
    "enabled_databases",
)
META_FIELDS = (
    "project_id",
    "research_direction",
    "pipeline_step",
    "progress_pct",
    "writing_type",
    "target_language",
)
PIPELINE_STATE_FIELDS = (
    "schema_version",
    "project_id",
    "current_step",
    "step_status",
    "updated_at",
)

SUPPORTED_DATABASES = {
    "Web of Science",
    "Scopus",
    "IEEE Xplore",
    "Google Scholar",
    "CNKI",
    "Wanfang",
}


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
    pipeline_state = _load(project_dir / "pipeline_state.json", errors) \
        if (project_dir / "pipeline_state.json").exists() else None

    if isinstance(pipeline_state, dict):
        for field in PIPELINE_STATE_FIELDS:
            if field not in pipeline_state:
                errors.append(f"pipeline_state missing field: {field}")
        if pipeline_state.get("schema_version") != 1:
            errors.append("pipeline_state schema_version must be 1")
        if not isinstance(pipeline_state.get("project_id"), str) or not pipeline_state.get("project_id").strip():
            errors.append("pipeline_state project_id must be a non-empty string")
        if not isinstance(pipeline_state.get("current_step"), str) or not pipeline_state.get("current_step").strip():
            errors.append("pipeline_state current_step must be a non-empty string")
        step_status = pipeline_state.get("step_status")
        if not isinstance(step_status, dict):
            errors.append("pipeline_state step_status must be an object")
        for ref_name in ("scope_card_ref", "query_pack_ref", "candidate_list_ref", "usage_guide_ref"):
            if ref_name in pipeline_state and pipeline_state[ref_name] is not None \
                    and not isinstance(pipeline_state[ref_name], str):
                errors.append(f"pipeline_state {ref_name} must be a string or null")
        for count_name in ("candidate_count", "verified_count"):
            if count_name in pipeline_state and (
                not isinstance(pipeline_state[count_name], int) or pipeline_state[count_name] < 0
            ):
                errors.append(f"pipeline_state {count_name} must be a non-negative integer")
        if "qa_status" in pipeline_state and pipeline_state["qa_status"] not in {"PASS", "WARNING", "FAIL", None}:
            errors.append("pipeline_state qa_status must be PASS, WARNING, FAIL, or null")

    if isinstance(config, dict):
        for field in CONFIG_FIELDS:
            if field not in config:
                errors.append(f"config missing field: {field}")
        direction = config.get("research_direction")
        if not isinstance(direction, str) or not direction.strip():
            errors.append("config research_direction must be a non-empty string")
        databases = config.get("enabled_databases")
        if not isinstance(databases, list) or not databases or not all(
            isinstance(value, str) and value.strip() for value in databases
        ):
            errors.append("config enabled_databases must be a non-empty string list")
        elif unknown := sorted(set(databases) - SUPPORTED_DATABASES):
            errors.append("config enabled_databases contains unsupported values: " + ", ".join(unknown))
        span = config.get("literature_time_span")
        if not isinstance(span, dict):
            errors.append("config literature_time_span must be an object")
        else:
            mode = span.get("mode", "fixed")
            start, end = span.get("start"), span.get("end")
            if mode == "fixed":
                if not isinstance(start, int) or not isinstance(end, int):
                    errors.append("fixed literature_time_span.start/end must be integers")
                elif start > end:
                    errors.append("config literature_time_span.start must be <= end")
            elif mode == "multi_window":
                presets = span.get("presets_years")
                if start is not None and not isinstance(start, int):
                    errors.append("multi_window literature_time_span.start must be null or an integer")
                if not isinstance(end, int):
                    errors.append("multi_window literature_time_span.end must be an integer")
                if not isinstance(presets, list) or not presets or not all(
                    isinstance(value, int) and value > 0 for value in presets
                ):
                    errors.append("multi_window literature_time_span.presets_years must contain positive integers")
            else:
                errors.append("config literature_time_span.mode must be fixed or multi_window")

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
