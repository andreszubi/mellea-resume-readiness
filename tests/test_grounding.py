"""Tests for the grounding checks. No model calls."""

from __future__ import annotations

import unittest

from analyzer.grounding import ground, is_grounded, ungrounded

RESUME = "Skills: Naïve Bayes, JavaScript, C++ and Node.js. Extreme Programming(XP). Database: MySQL"


class GroundingTests(unittest.TestCase):
    def test_case_spacing_and_punctuation_are_ignored(self) -> None:
        for skill in ("javascript", "Node JS", "Extreme Programming (XP)", "c++"):
            self.assertTrue(is_grounded(skill, RESUME), skill)

    def test_accents_are_ignored(self) -> None:
        self.assertTrue(is_grounded("naive bayes", RESUME))

    def test_only_whole_words_count(self) -> None:
        # "Java" must not pass because of "JavaScript", nor "C" because of "C++".
        self.assertFalse(is_grounded("Java", RESUME))
        self.assertFalse(is_grounded("C", RESUME))
        self.assertFalse(is_grounded("SQL", RESUME))

    def test_ungrounded_lists_what_is_missing_in_order(self) -> None:
        self.assertEqual(ungrounded(["MySQL", "Python", "C++", "Docker", ""], RESUME), ["Python", "Docker", ""])

    def test_ground_keeps_an_item_that_is_present(self) -> None:
        self.assertEqual(ground("Node.js", RESUME), "Node.js")

    def test_ground_strips_a_leading_category_label(self) -> None:
        self.assertEqual(ground("Version control MySQL", RESUME), "MySQL")

    def test_ground_returns_none_when_nothing_matches(self) -> None:
        self.assertIsNone(ground("Python", RESUME))
        self.assertIsNone(ground("", RESUME))


if __name__ == "__main__":
    unittest.main()
