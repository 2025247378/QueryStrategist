import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "query_generator.py"
SPEC = importlib.util.spec_from_file_location("query_generator_search_a", MODULE_PATH)
QUERY_GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUERY_GENERATOR)


def bilingual_scope():
    return {
        "keyword_tiers": {
            "tier1_species_object": ["fish", "farmed fish", "cultured fish"],
            "tier2_technology_method": [
                "hyperspectral imaging", "multispectral imaging",
                "machine learning", "deep learning",
            ],
            "tier2_required_anchor": [
                "hyperspectral imaging", "multispectral imaging", "spectral imaging",
            ],
            "tier2_supporting_method": ["machine learning", "deep learning"],
            "tier3_application_task": [
                "quality assessment", "freshness", "fat content", "size grading",
                "weight estimation", "defect detection", "automatic sorting",
            ],
        },
        "explicit_exclusions": ["shrimp", "crab", "shellfish"],
        "keyword_tiers_zh": {
            "tier1_species_object": ["养殖鱼类", "鱼肉", "鱼片"],
            "tier2_technology_method": ["高光谱成像", "多光谱成像", "机器学习"],
            "tier2_required_anchor": ["高光谱成像", "多光谱成像", "光谱成像"],
            "tier2_supporting_method": ["机器学习"],
            "tier3_application_task": [
                "品质鉴定", "新鲜度", "脂肪含量", "规格分级", "缺陷检测", "自动分选",
            ],
        },
        "explicit_exclusions_zh": ["虾", "蟹", "贝类", "水质监测"],
    }


class SearchARulesTests(unittest.TestCase):
    def setUp(self):
        self.scope = bilingual_scope()
        self.queries = QUERY_GENERATOR.generate(self.scope)

    def test_wos_a0_requires_only_object_and_technology(self):
        query = self.queries["wos"]
        self.assertEqual(query.count("TS=("), 2)
        self.assertIn('TS=(fish OR "farmed fish" OR "cultured fish")', query)
        self.assertIn('TS=("hyperspectral imaging"', query)
        self.assertNotIn('"quality assessment"', query)
        self.assertNotIn(" NOT ", query)
        self.assertNotIn('"machine learning"', query)

    def test_scopus_a0_requires_only_object_and_technology(self):
        query = self.queries["scopus"]
        self.assertEqual(query.count("TITLE-ABS-KEY("), 2)
        self.assertIn('TITLE-ABS-KEY(fish OR "farmed fish"', query)
        self.assertIn('TITLE-ABS-KEY("hyperspectral imaging"', query)
        self.assertNotIn('"quality assessment"', query)
        self.assertNotIn("AND NOT", query)

    def test_ieee_uses_method_recall_baseline_and_all_metadata(self):
        query = self.queries["ieee"]
        self.assertNotIn('"Document Title":', query)
        self.assertIn("(fish OR \"farmed fish\" OR \"cultured fish\")", query)
        self.assertIn('"spectral imaging"', query)
        self.assertNotIn('"automatic sorting"', query)
        self.assertNotIn("shrimp", query)

    def test_google_scholar_a0_is_short_two_layer_query_set(self):
        queries = self.queries["google_scholar"]
        self.assertIsInstance(queries, list)
        self.assertTrue(queries)
        self.assertLessEqual(len(queries), 6)
        self.assertTrue(all(len(query) <= 256 for query in queries))
        joined = "\n".join(queries)
        for term in self.scope["keyword_tiers"]["tier3_application_task"]:
            self.assertNotIn(QUERY_GENERATOR._gs_term(term), joined)
        for query in queries:
            self.assertIn('"hyperspectral imaging"', query)
            self.assertIn("fish", query)

    def test_cnki_a0_uses_chinese_object_and_technology_only(self):
        query = self.queries["cnki"]
        self.assertIn("SU='养殖鱼类'", query)
        self.assertIn("SU='高光谱成像'", query)
        self.assertNotIn("SU='品质鉴定'", query)
        self.assertNotIn("farmed fish", query)
        self.assertEqual(query.count(" AND "), 1)
        self.assertNotIn(" NOT ", query)

    def test_wanfang_matches_current_professional_search_box(self):
        query = self.queries["wanfang"]
        self.assertNotIn("主题:", query)
        self.assertIn("(养殖鱼类 OR 鱼肉 OR 鱼片)", query)
        self.assertIn("(高光谱成像 OR 多光谱成像 OR 光谱成像)", query)
        self.assertNotIn("品质鉴定", query)
        self.assertNotIn(" NOT ", query)
        self.assertLessEqual(len(query), 800)

    def test_a1_restores_task_layer_and_exclusions(self):
        variants = QUERY_GENERATOR.generate_variants(self.scope)
        expected = {
            "wos": ('"quality assessment"', " NOT "),
            "scopus": ('"quality assessment"', " AND NOT "),
            "cnki": ("SU='品质鉴定'", " NOT "),
            "wanfang": ("品质鉴定", " NOT "),
        }
        for platform, (task, exclusion_op) in expected.items():
            topical = next(row["query"] for row in variants[platform]
                           if row["variant"] == "topical")
            self.assertIn(task, topical, platform)
            self.assertIn(exclusion_op, topical, platform)

        scholar = variants["google_scholar"]
        a0 = [row for row in scholar if row["variant"].startswith("broad")]
        a1 = [row for row in scholar if row["variant"].startswith("topical")]
        self.assertLessEqual(len(a0), 6)
        self.assertLessEqual(len(a1), 6)
        self.assertTrue(any('"quality assessment"' in row["query"] for row in a1))
        self.assertTrue(all('"quality assessment"' not in row["query"] for row in a0))
        self.assertTrue(all("-shrimp" in row["query"] for row in a1))

    def test_review_variants_keep_exclusions_at_the_end(self):
        variants = QUERY_GENERATOR.generate_variants(self.scope)
        for platform in ("wos", "scopus", "cnki", "wanfang"):
            review = next(
                row["query"] for row in variants[platform]
                if row["variant"] == "review"
            )
            self.assertLess(review.find("review") if "review" in review else review.find("综述"),
                            review.rfind(" NOT ") if " NOT " in review else review.rfind(" AND NOT "))
        scopus_review = next(
            row["query"] for row in variants["scopus"]
            if row["variant"] == "review"
        )
        self.assertGreater(scopus_review.rfind(" AND NOT "), scopus_review.rfind("review"))

    def test_precise_variants_are_materially_narrower(self):
        variants = QUERY_GENERATOR.generate_variants(self.scope)
        for platform in ("wos", "scopus", "cnki", "wanfang"):
            broad = next(row["query"] for row in variants[platform]
                         if row["variant"] == "broad")
            precise = next(row["query"] for row in variants[platform]
                           if row["variant"] == "precise")
            self.assertNotEqual(broad, precise, platform)
        self.assertIn("TI=", next(row["query"] for row in variants["wos"]
                                  if row["variant"] == "precise"))
        self.assertIn(" W/5 ", next(row["query"] for row in variants["scopus"]
                                    if row["variant"] == "precise"))
        self.assertIn("TI=", next(row["query"] for row in variants["cnki"]
                                  if row["variant"] == "precise"))

    def test_a0_allows_missing_task_but_variants_require_it(self):
        incomplete = bilingual_scope()
        incomplete["keyword_tiers"].pop("tier3_application_task")
        incomplete["keyword_tiers_zh"].pop("tier3_application_task")
        generated = QUERY_GENERATOR.generate(incomplete)
        self.assertIn("wos", generated)
        with self.assertRaisesRegex(ValueError, "tier3 task"):
            QUERY_GENERATOR.generate_variants(incomplete)


if __name__ == "__main__":
    unittest.main()
