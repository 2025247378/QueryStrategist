import importlib.util
import json
from pathlib import Path


def _load_module(relative_path, name):
    path = Path(__file__).parents[1] / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


harvest = _load_module(
    "literature_harvester/scripts/harvest.py", "harvest_test_target"
)


def test_extract_doi_and_deduplicate():
    assert harvest._extract_doi("https://doi.org/10.1000/ABC") == "10.1000/ABC"
    papers = [
        {"title": "Same title", "year": 2024, "doi": "10.1000/a"},
        {"title": "Same title", "year": 2024, "doi": "https://doi.org/10.1000/a"},
        {"title": "Same title", "year": 2024, "doi": None},
        {"title": "Same title", "year": 2024, "doi": None},
    ]
    assert len(harvest.deduplicate_papers(papers)) == 2


def test_crossref_match_quality_and_title_mismatch(monkeypatch):
    monkeypatch.setattr(
        harvest,
        "_get",
        lambda *args, **kwargs: {
            "message": {
                "title": ["Hyperspectral imaging for fish quality grading"],
                "issued": {"date-parts": [[2024]]},
            }
        },
    )
    ok, detail = harvest.verify_by_doi(
        "10.1000/test", "Hyperspectral imaging for fish quality grading", 2024
    )
    assert ok is True
    assert detail["match_quality"] == "high"
    assert detail["reason"] == "match"

    ok, detail = harvest.verify_by_doi("10.1000/test", "Unrelated title", 2024)
    assert ok is False
    assert detail["reason"] == "title_mismatch"
    assert detail["retryable"] is False


def test_verification_reasons_and_checkpoint_resume(monkeypatch, tmp_path):
    calls = []

    def fake_verify(doi, expected_title, expected_year, mailto=None):
        calls.append(doi)
        if doi.endswith("timeout"):
            raise TimeoutError("Crossref timeout")
        return True, {"reason": "match", "similarity": 0.95, "match_quality": "high"}

    monkeypatch.setattr(harvest, "verify_by_doi", fake_verify)
    papers = [
        {"title": "No DOI", "year": 2024, "doi": None},
        {"title": "Valid", "year": 2024, "doi": "10.1000/valid"},
        {"title": "Timeout", "year": 2024, "doi": "10.1000/timeout"},
    ]
    checkpoint = tmp_path / "harvest_checkpoint.json"
    kept, dropped = harvest.verify_openalex_results(
        papers, checkpoint_path=checkpoint, checkpoint_every=1
    )
    assert not dropped
    assert {item["verification_detail"]["reason"] for item in kept} == {
        "no_doi", "match", "api_timeout"
    }
    assert checkpoint.is_file()
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["completed_run"] is True
    first_call_count = len(calls)

    kept, dropped = harvest.verify_openalex_results(
        papers, checkpoint_path=checkpoint
    )
    assert len(calls) == first_call_count
    assert len(kept) == 3
    assert not dropped

    harvest.verify_openalex_results(
        papers, checkpoint_path=checkpoint, retry_unverified=True
    )
    assert len(calls) == first_call_count + 1
