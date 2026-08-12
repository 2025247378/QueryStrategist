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
    def test_broad_query_uses_ieee_recall_baseline_without_exclusions(self):
        scope = aquaculture_scope()
        query = QUERY_GENERATOR.build_ieee(
            scope["keyword_tiers"], scope["explicit_exclusions"]
        )
        self.assertNotIn('"Abstract":', query)
        self.assertNotIn(" NOT ", query)
        for tier_terms in (
            scope["keyword_tiers"]["tier1_species_object"],
            scope["keyword_tiers"]["tier2_technology_method"],
        ):
            for term in tier_terms:
                expected = f'"{term}"' if " " in term else term
                self.assertIn(expected, query)
        self.assertNotIn('"quality assessment"', query)
        self.assertRegex(query, r"\b(fish)\b")

    def test_title_field_is_repeated_for_each_or_value(self):
        tiers = {
            "tier1_species_object": ["fish", "farmed fish"],
            "tier2_technology_method": ["hyperspectral imaging"],
            "tier3_application_task": ["freshness"],
        }
        query = QUERY_GENERATOR.build_ieee(tiers, [], broad=False)
        self.assertIn('"Document Title":fish', query)
        self.assertIn('"Document Title":"farmed fish"', query)
        self.assertNotRegex(query, r'"Document Title"\s*:\s*\(')
        self.assertNotIn('"Document Title":freshness', query)

    def test_all_variants_follow_syntax_and_clause_limit(self):
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

    def test_boolean_separated_terms_do_not_trigger_global_split(self):
        scope = aquaculture_scope()
        variants = QUERY_GENERATOR.generate_variants(scope, ["ieee"])["ieee"]
        broad = [row for row in variants if row["variant"] == "broad"]
        self.assertEqual(len(broad), 1)
        topical = [row for row in variants if row["variant"] == "topical"]
        self.assertEqual(len(topical), 1)
        self.assertGreater(topical[0]["query"].count(" OR "), 25)
        self.assertLessEqual(
            QUERY_GENERATOR._ieee_query_term_count(topical[0]["query"]),
            QUERY_GENERATOR.IEEE_MAX_SEARCH_TERMS,
        )

    def test_split_variants_preserve_all_application_terms(self):
        scope = aquaculture_scope()
        variants = QUERY_GENERATOR.generate_variants(scope, ["ieee"])["ieee"]
        topical_text = "\n".join(
            row["query"] for row in variants if row["variant"].startswith("topical")
        )
        for term in scope["keyword_tiers"]["tier3_application_task"]:
            expected = f'"{term}"' if " " in term else term
            self.assertIn(expected, topical_text)

    def test_compound_fish_scope_adds_generic_recall_anchors(self):
        scope = {
            "keyword_tiers": {
                "tier1_species_object": [
                    "aquaculture fish", "farmed fish", "cultured fish",
                    "fish fillet", "fish muscle", "aquatic products",
                ],
                "tier2_technology_method": [
                    "spectral imaging", "hyperspectral imaging", "multispectral imaging",
                ],
                "tier3_application_task": [
                    "quality assessment", "freshness detection", "weight estimation",
                ],
            },
            "explicit_exclusions": ["water quality monitoring"],
        }
        variants = QUERY_GENERATOR.generate_variants(scope, ["ieee"])["ieee"]
        baseline = next(row["query"] for row in variants if row["variant"] == "broad")
        topical = next(row["query"] for row in variants if row["variant"] == "topical")
        precise = next(row["query"] for row in variants if row["variant"] == "precise")
        self.assertRegex(baseline, r' OR fish\)')
        self.assertNotIn('"quality assessment"', baseline)
        self.assertIn('"quality assessment"', topical)
        self.assertIn(" OR quality OR freshness", topical)
        self.assertNotRegex(
            topical,
            r" OR (assessment|content|estimation|composition)(?: OR|\))",
        )
        self.assertIn('"Document Title":fish', precise)
        self.assertNotIn('"Document Title":"quality assessment"', precise)

    def test_ieee_specific_proximity_and_optional_conference_variants(self):
        scope = aquaculture_scope()
        scope["ieee_publication_titles"] = ["IEEE Access", "OCEANS"]
        variants = QUERY_GENERATOR.generate_variants(scope, ["ieee"])["ieee"]
        queries = "\n".join(row["query"] for row in variants)
        self.assertIn(" NEAR/10 ", queries)
        self.assertIn(" ONEAR/10 ", queries)
        self.assertIn('"Publication Title":"IEEE Access"', queries)
        self.assertIn('"Publication Title":OCEANS', queries)

    def test_proximity_connects_method_and_task_tiers(self):
        scope = aquaculture_scope()
        variants = QUERY_GENERATOR.generate_variants(scope, ["ieee"])["ieee"]
        proximity = "\n".join(
            row["query"] for row in variants
            if row["variant"].startswith("proximity")
        )
        self.assertIn('"hyperspectral imaging"', proximity)
        self.assertIn('"quality assessment"', proximity)
        self.assertIn(" NEAR/10 ", proximity)
        self.assertIn(" ONEAR/10 ", proximity)

    def test_simple_words_are_unquoted_but_phrases_are_quoted(self):
        query = QUERY_GENERATOR.build_ieee(
            {
                "tier1_species_object": ["fish", "farmed fish"],
                "tier2_technology_method": ["spectroscopy"],
                "tier3_application_task": ["freshness"],
            },
            [],
        )
        self.assertIn("(fish OR \"farmed fish\")", query)
        self.assertIn("(spectroscopy)", query)
        self.assertNotIn("(freshness)", query)

    def test_wildcard_constraints_are_validated(self):
        with self.assertRaisesRegex(ValueError, "three preceding"):
            QUERY_GENERATOR._ieee_validate_query("f* AND fish")
        with self.assertRaisesRegex(ValueError, "10-wildcard"):
            QUERY_GENERATOR._ieee_validate_query(
                " OR ".join(f"term{i}*" for i in range(11))
            )


if __name__ == "__main__":
    unittest.main()
