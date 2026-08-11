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

    def test_wos_requires_object_anchor_and_task(self):
        query = self.queries["wos"]
        self.assertEqual(query.count("TS=("), 4)  # three required tiers + exclusion
        self.assertIn('TS=(fish OR "farmed fish" OR "cultured fish")', query)
        self.assertIn('TS=("hyperspectral imaging"', query)
        self.assertIn('TS=("quality assessment"', query)
        self.assertNotIn('"machine learning"', query)

    def test_scopus_requires_object_anchor_and_task(self):
        query = self.queries["scopus"]
        self.assertGreaterEqual(query.count("TITLE-ABS-KEY("), 4)
        self.assertIn('TITLE-ABS-KEY(fish OR "farmed fish"', query)
        self.assertIn('TITLE-ABS-KEY("hyperspectral imaging"', query)
        self.assertIn('TITLE-ABS-KEY("quality assessment"', query)
        self.assertTrue(query.rfind("AND NOT") > query.rfind(" AND "))

    def test_ieee_is_complete_and_uses_all_metadata(self):
        query = self.queries["ieee"]
        self.assertNotIn('"Document Title":', query)
        self.assertIn("(fish OR \"farmed fish\" OR \"cultured fish\")", query)
        self.assertIn('"spectral imaging"', query)
        self.assertIn('"automatic sorting"', query)

    def test_google_scholar_returns_complete_complementary_queries(self):
        queries = self.queries["google_scholar"]
        self.assertIsInstance(queries, list)
        self.assertTrue(queries)
        self.assertTrue(all(len(query) <= 256 for query in queries))
        joined = "\n".join(queries)
        for term in self.scope["keyword_tiers"]["tier3_application_task"]:
            self.assertIn(QUERY_GENERATOR._gs_term(term), joined)
        for query in queries:
            self.assertIn('"hyperspectral imaging"', query)
            self.assertIn('"quality assessment"', joined)

    def test_cnki_uses_chinese_tiers_and_three_required_concepts(self):
        query = self.queries["cnki"]
        self.assertIn("SU='养殖鱼类'", query)
        self.assertIn("SU='高光谱成像'", query)
        self.assertIn("SU='品质鉴定'", query)
        self.assertNotIn("farmed fish", query)
        self.assertGreaterEqual(query.count(" AND "), 2)
        self.assertNotIn("AND NOT", query)
        self.assertIn(" NOT (SU='虾' OR SU='蟹'", query)

    def test_wanfang_matches_current_professional_search_box(self):
        query = self.queries["wanfang"]
        self.assertNotIn("主题:", query)
        self.assertIn("(养殖鱼类 OR 鱼肉 OR 鱼片)", query)
        self.assertIn("(高光谱成像 OR 多光谱成像 OR 光谱成像)", query)
        self.assertIn("(品质鉴定 OR 新鲜度", query)
        self.assertIn(" NOT (虾 OR 蟹 OR 贝类 OR 水质监测)", query)
        self.assertLessEqual(len(query), 800)

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

    def test_search_a_rejects_missing_required_tier(self):
        incomplete = bilingual_scope()
        incomplete["keyword_tiers"].pop("tier3_application_task")
        with self.assertRaisesRegex(ValueError, "tier3 task"):
            QUERY_GENERATOR.generate(incomplete)


if __name__ == "__main__":
    unittest.main()
