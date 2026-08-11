import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "query_generator.py"
SPEC = importlib.util.spec_from_file_location("query_generator", MODULE_PATH)
QUERY_GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUERY_GENERATOR)


def aquaculture_scope():
    return {
        "keyword_tiers": {
            "tier1_species_object": [
                "aquaculture fish", "farmed fish", "cultured fish",
                "fish products", "fish fillet", "whole fish",
            ],
            "tier2_technology_method": [
                "hyperspectral imaging", "multispectral imaging", "spectral imaging",
                "spectral feature extraction", "wavelength selection", "chemometrics",
                "machine learning", "deep learning", "non-destructive detection",
            ],
            "tier3_application_task": [
                "quality assessment", "freshness evaluation", "fat content",
                "moisture content", "protein content", "texture", "flavor",
                "size grading", "weight estimation", "length estimation",
                "grade classification", "defect detection", "damage detection",
                "species identification", "origin traceability", "online detection",
                "automatic sorting", "intelligent grading equipment",
            ],
        },
        "explicit_exclusions": [
            "shrimp", "crab", "shellfish", "water quality monitoring",
            "pathogen detection", "disease diagnosis", "sensory evaluation",
        ],
    }


class IEEEQueryTests(unittest.TestCase):
    def test_broad_query_uses_all_metadata_and_canonical_not(self):
        scope = aquaculture_scope()
        query = QUERY_GENERATOR.build_ieee(
            scope["keyword_tiers"], scope["explicit_exclusions"]
        )
        self.assertNotIn('"Abstract":', query)
        self.assertNotIn(" AND NOT ", query)
        self.assertIn(" NOT (", query)

    def test_title_field_is_repeated_for_each_or_value(self):
        tiers = {
            "tier1_species_object": ["fish", "farmed fish"],
            "tier2_technology_method": ["hyperspectral imaging"],
            "tier3_application_task": ["freshness"],
        }
        query = QUERY_GENERATOR.build_ieee(tiers, [], broad=False)
        self.assertIn('"Document Title":"fish"', query)
        self.assertIn('"Document Title":"farmed fish"', query)
        self.assertNotRegex(query, r'"Document Title"\s*:\s*\(')

    def test_all_variants_follow_syntax_and_term_limit(self):
        variants = QUERY_GENERATOR.generate_variants(
            aquaculture_scope(), ["ieee"]
        )["ieee"]
        self.assertGreater(len(variants), 4)
        for variant in variants:
            query = variant["query"]
            self.assertNotRegex(query, r'"[^"\r\n]+"\s*:\s*\(')
            self.assertLessEqual(
                QUERY_GENERATOR._ieee_query_term_count(query),
                QUERY_GENERATOR.IEEE_MAX_SEARCH_TERMS,
                variant["variant"],
            )

    def test_split_variants_preserve_all_application_terms(self):
        scope = aquaculture_scope()
        variants = QUERY_GENERATOR.generate_variants(scope, ["ieee"])["ieee"]
        broad_text = "\n".join(
            row["query"] for row in variants if row["variant"].startswith("broad")
        )
        for term in scope["keyword_tiers"]["tier3_application_task"]:
            self.assertIn(f'"{term}"', broad_text)

    def test_ieee_specific_proximity_and_optional_conference_variants(self):
        scope = aquaculture_scope()
        scope["ieee_publication_titles"] = ["IEEE Access", "OCEANS"]
        variants = QUERY_GENERATOR.generate_variants(scope, ["ieee"])["ieee"]
        queries = "\n".join(row["query"] for row in variants)
        self.assertIn(" NEAR/3 ", queries)
        self.assertIn(" ONEAR/3 ", queries)
        self.assertIn('"Publication Title":"IEEE Access"', queries)
        self.assertIn('"Publication Title":"OCEANS"', queries)


if __name__ == "__main__":
    unittest.main()
