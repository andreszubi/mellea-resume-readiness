"""End-to-end test for the resume extractor. It calls the model, so it is opt-in:

    RUN_LLM_TESTS=1 uv run python -m unittest tests.test_extract_resume -v

Needs Ollama running with granite4.2:3b pulled.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from analyzer.extract_resume import extract_resume
from analyzer.grounding import ungrounded

SAMPLE = Path(__file__).parent / "fixtures" / "sample_resume.txt"


@unittest.skipUnless(os.environ.get("RUN_LLM_TESTS") == "1", "set RUN_LLM_TESTS=1 to call the model")
class ExtractResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SAMPLE.read_text(encoding="utf-8")
        cls.profile = extract_resume(cls.text)

    def test_sample_resume_is_fully_populated(self) -> None:
        self.assertEqual(self.profile.missing_sections(), [])

    def test_finds_the_listed_skills(self) -> None:
        found = {skill.casefold() for skill in self.profile.skills}
        for skill in ("python", "sql", "react", "docker"):
            self.assertIn(skill, found)

    def test_every_skill_appears_in_the_resume(self) -> None:
        self.assertEqual(ungrounded(self.profile.skills, self.text), [])

    def test_finds_both_jobs_and_both_degrees(self) -> None:
        self.assertEqual(len(self.profile.experience), 2)
        self.assertEqual(len(self.profile.education), 2)
        self.assertEqual(self.profile.experience[0].organization, "Sunshine Health Systems")


class ExtractResumeInputTests(unittest.TestCase):
    def test_empty_text_is_rejected_before_calling_the_model(self) -> None:
        with self.assertRaises(ValueError):
            extract_resume("   \n ")


if __name__ == "__main__":
    unittest.main()
