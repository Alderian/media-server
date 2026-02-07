"""
Unit tests for the scoring module.

Tests the confidence scoring system that evaluates how well
metadata from APIs matches the original filename.
"""

import unittest
from scoring import ConfidenceScorer
from models import ScoreBreakdown, MetadataCandidate


class TestConfidenceScorer(unittest.TestCase):
    """
    Tests for the ConfidenceScorer class.

    Verifies that the scoring algorithm correctly evaluates
    metadata matches using fuzzy string matching.
    """

    def setUp(self):
        """Set up scorer with default settings."""
        self.scorer = ConfidenceScorer(
            min_confidence=0.7,
            auto_accept_threshold=0.85,
            fuzzy_threshold=0.8,
            year_tolerance=1,
        )

    def test_exact_match(self):
        """Test scoring of an exact title and year match."""
        score = self.scorer.score_match(
            query_title="The Matrix",
            query_year="1999",
            result_title="The Matrix",
            result_year="1999",
        )
        self.assertGreaterEqual(score.overall, 0.9)
        self.assertEqual(score.title_similarity, 1.0)
        self.assertEqual(score.year_match, 1.0)

    def test_close_title_match(self):
        """Test scoring of a close but not exact title match."""
        score = self.scorer.score_match(
            query_title="The Matrix",
            query_year="1999",
            result_title="Matrix, The",
            result_year="1999",
        )
        self.assertGreater(score.title_similarity, 0.7)
        self.assertGreater(score.overall, 0.7)

    def test_year_tolerance(self):
        """Test that year tolerance allows slight differences."""
        score = self.scorer.score_match(
            query_title="Movie",
            query_year="2000",
            result_title="Movie",
            result_year="2001",
        )
        self.assertEqual(score.year_match, 0.8)  # Within tolerance

        score2 = self.scorer.score_match(
            query_title="Movie",
            query_year="2000",
            result_title="Movie",
            result_year="2005",
        )
        self.assertLess(score2.year_match, 0.8)  # Outside tolerance

    def test_no_year_in_query(self):
        """Test scoring when query has no year."""
        score = self.scorer.score_match(
            query_title="Movie",
            query_year=None,
            result_title="Movie",
            result_year="2020",
        )
        self.assertEqual(score.year_match, 0.5)  # Neutral

    def test_no_year_in_result(self):
        """Test scoring when result has no year."""
        score = self.scorer.score_match(
            query_title="Movie",
            query_year="2020",
            result_title="Movie",
            result_year=None,
        )
        self.assertEqual(score.year_match, 0.3)  # Slight penalty

    def test_poor_match(self):
        """Test scoring of a poor title match."""
        score = self.scorer.score_match(
            query_title="The Matrix",
            query_year="1999",
            result_title="Speed",
            result_year="1994",
        )
        self.assertLess(score.overall, 0.5)

    def test_is_confident(self):
        """Test confidence threshold checking."""
        high_score = ScoreBreakdown(
            title_similarity=0.95,
            year_match=1.0,
            keyword_overlap=0.5,
            overall=0.85,
        )
        low_score = ScoreBreakdown(
            title_similarity=0.5,
            year_match=0.5,
            keyword_overlap=0.5,
            overall=0.5,
        )

        self.assertTrue(high_score.overall >= self.scorer.min_confidence)
        self.assertFalse(low_score.overall >= self.scorer.min_confidence)

    def test_select_best_match(self):
        """Test selection of best match from candidates."""
        results = [
            MetadataCandidate(
                source="tmdb", id="1", title="Wrong Movie",
                score=ScoreBreakdown(0.5, 0.5, 0.5, 0.5)
            ),
            MetadataCandidate(
                source="tmdb", id="2", title="The Matrix",
                score=ScoreBreakdown(0.95, 1.0, 0.5, 0.85)
            ),
            MetadataCandidate(
                source="tmdb", id="3", title="Matrix Reloaded",
                score=ScoreBreakdown(0.7, 0.5, 0.5, 0.6)
            ),
        ]

        best = self.scorer.select_best_match(results)
        self.assertIsNotNone(best)
        self.assertEqual(best.title, "The Matrix")

    def test_no_confident_match(self):
        """Test that None is returned when no results provided."""
        results = []
        best = self.scorer.select_best_match(results)
        self.assertIsNone(best)

    def test_metadata_hints_modern_codec(self):
        """
        Test that modern codecs boost year scores for recent content.

        When query has no year and file uses h265, matches with years 2015+
        should receive a boost to the year score.
        """
        # Without metadata, score is neutral
        score_no_meta = self.scorer.score_match(
            query_title="Movie",
            query_year=None,
            result_title="Movie",
            result_year="2020",
        )

        # With modern codec, should boost
        score_with_meta = self.scorer.score_match(
            query_title="Movie",
            query_year=None,
            result_title="Movie",
            result_year="2020",
            file_metadata={"video_codec": "h265"},
        )

        self.assertGreater(score_with_meta.overall, score_no_meta.overall)

    def test_metadata_hints_legacy_codec(self):
        """
        Test that legacy codecs boost year scores for older content.

        When query has no year and file uses xvid, matches with years <=2010
        should receive a boost to the year score.
        """
        score_no_meta = self.scorer.score_match(
            query_title="OldMovie",
            query_year=None,
            result_title="OldMovie",
            result_year="2005",
        )

        # Legacy codec with older content
        score_with_meta = self.scorer.score_match(
            query_title="OldMovie",
            query_year=None,
            result_title="OldMovie",
            result_year="2005",
            file_metadata={"video_codec": "xvid"},
        )

        self.assertGreater(score_with_meta.overall, score_no_meta.overall)

    def test_metadata_hints_hdr(self):
        """
        Test that HDR content boosts scores for 2016+ releases.

        HDR is only practical for content from 2016 onwards, so this
        provides a small confidence boost for matching newer content.
        """
        score_no_meta = self.scorer.score_match(
            query_title="HDRMovie",
            query_year=None,
            result_title="HDRMovie",
            result_year="2020",
        )

        # HDR with modern 2020 content
        score_with_hdr = self.scorer.score_match(
            query_title="HDRMovie",
            query_year=None,
            result_title="HDRMovie",
            result_year="2020",
            file_metadata={"hdr": True},
        )

        self.assertGreater(score_with_hdr.overall, score_no_meta.overall)

    def test_metadata_hints_no_effect_with_year(self):
        """
        Test that metadata hints don't affect scores when query has a year.

        When the filename already contains a year, the metadata hints
        should not alter the scoring since we have direct year data.
        """
        score_no_meta = self.scorer.score_match(
            query_title="Movie",
            query_year="2020",
            result_title="Movie",
            result_year="2020",
        )

        score_with_meta = self.scorer.score_match(
            query_title="Movie",
            query_year="2020",
            result_title="Movie",
            result_year="2020",
            file_metadata={"video_codec": "h265", "hdr": True},
        )

        # Should be the same since query_year is present
        self.assertEqual(score_no_meta.overall, score_with_meta.overall)


class TestScoreBreakdown(unittest.TestCase):
    """Tests for ScoreBreakdown serialization."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        score = ScoreBreakdown(
            title_similarity=0.9567,
            year_match=1.0,
            keyword_overlap=0.5,
            overall=0.8234,
        )
        d = score.to_dict()

        self.assertEqual(d["title_similarity"], 0.957)  # Rounded
        self.assertEqual(d["year_match"], 1.0)
        self.assertEqual(d["keyword_overlap"], 0.5)
        self.assertEqual(d["overall"], 0.823)


if __name__ == "__main__":
    unittest.main()
