import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "harvest.py"
SPEC = importlib.util.spec_from_file_location("harvest", MODULE_PATH)
HARVEST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARVEST)


class HarvestTests(unittest.TestCase):
    def test_abstract_inverted_index_is_reconstructed(self):
        work = {"abstract_inverted_index": {
            "water": [0], "quality": [1], "monitoring": [2],
        }}
        self.assertEqual(HARVEST._abstract_text(work), "water quality monitoring")

    def test_filtered_openalex_excludes_title_and_abstract(self):
        payload = {"results": [
            {
                "title": "Spectral grading of farmed fish",
                "authorships": [], "publication_year": 2024,
                "doi": None, "cited_by_count": 0, "id": "W1",
                "primary_location": {}, "open_access": {"is_oa": True},
                "abstract_inverted_index": {"water": [0], "quality": [1], "monitoring": [2]},
            },
            {
                "title": "Spectral grading of farmed fish",
                "authorships": [], "publication_year": 2024,
                "doi": None, "cited_by_count": 0, "id": "W2",
                "primary_location": {}, "open_access": {"is_oa": True},
                "abstract_inverted_index": {"freshness": [0], "grading": [1]},
            },
        ]}
        with patch.object(HARVEST, "_get", return_value=payload) as get:
            rows = HARVEST.harvest_openalex_filtered(
                ["fish"], ["spectral imaging"], ["freshness"],
                min_year=2020, exclude_terms=["water quality"],
            )
        self.assertEqual([row["title"] for row in rows], ["Spectral grading of farmed fish"])
        params = get.call_args.args[1]
        self.assertIn("abstract_inverted_index", params["select"])

    def test_three_tier_filter_is_reachable_from_harvest(self):
        with patch.object(HARVEST, "harvest_openalex_filtered", return_value=[]) as filtered:
            result = HARVEST.harvest(
                "fish spectral freshness", verify=False,
                species_terms=["fish"], tech_terms=["spectral imaging"],
                task_terms=["freshness"],
            )
        filtered.assert_called_once()
        self.assertEqual(result["statistics"]["harvested"], 0)

    def test_three_tier_filter_rejects_partial_input(self):
        with self.assertRaisesRegex(ValueError, "三层过滤"):
            HARVEST.harvest(
                "fish", verify=False,
                species_terms=["fish"], tech_terms=["spectral imaging"],
            )


if __name__ == "__main__":
    unittest.main()
