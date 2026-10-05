import importlib.util
from pathlib import Path


def _load_module(relative_path, name):
    path = Path(__file__).parents[1] / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


query_generator = _load_module(
    "query_crafter/scripts/query_generator.py", "query_generator_test_target"
)


def test_all_platform_variants_have_expected_shape_and_qa():
    scope = query_generator._demo_scope()
    variants = query_generator.generate_variants(scope)
    assert set(variants) == {
        "wos", "scopus", "ieee", "google_scholar", "cnki", "wanfang"
    }
    for platform, rows in variants.items():
        assert rows
        assert all(row["query"].strip() for row in rows)
        if platform == "google_scholar":
            assert all(len(row["query"]) <= 256 for row in rows)
        if platform == "ieee":
            for row in rows:
                query_generator._ieee_validate_query(row["query"])
    qa = query_generator.run_query_qa(variants, scope)
    assert qa["status"] != "FAIL"


def test_ieee_clause_counter_respects_boolean_boundaries_and_phrases():
    assert query_generator._ieee_clause_term_counts(
        '"Document Title":fish AND "Abstract":("hyperspectral imaging" OR multispectral)'
    ) == [1, 2, 1]
    assert query_generator._ieee_clause_term_counts(
        'fish ONEAR/3 feeding AND sensor NOT disease'
    ) == [1, 1, 1, 1]


def test_google_scholar_groups_never_break_length_or_quotes():
    tiers = {
        "tier1_species_object": ["aquaculture fish", "cultured fish", "farmed fish"],
        "tier2_technology_method": ["hyperspectral imaging", "multispectral imaging"],
        "tier3_application_task": ["quality grading", "freshness assessment"],
    }
    queries = query_generator._gs_layered_queries(tiers, include_task=True)
    assert queries
    for query in queries:
        assert len(query) <= 256
        assert query.count('"') % 2 == 0
        assert query.count("(") == query.count(")")


def test_broad_exclusions_are_not_added_to_query():
    scope = {
        "keyword_tiers": {
            "tier1_species_object": ["fish"],
            "tier2_technology_method": ["hyperspectral imaging"],
            "tier3_application_task": ["quality grading"],
        },
        "explicit_exclusions": ["fish", "water quality monitoring"],
    }
    policy = query_generator.classify_exclusions(scope)
    assert "fish" in policy["risky"]
    assert "fish" not in policy["query"]
    assert "water quality monitoring" in policy["query"]
