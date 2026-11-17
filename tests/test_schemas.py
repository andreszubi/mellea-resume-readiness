"""Tests for the data classes. No model calls, so they run in well under a second.

    uv run python -m unittest discover -s tests -t . -v
"""

from __future__ import annotations

import unittest

from analyzer.schemas import Education, Experience, ResumeProfile


class ResumeProfileTests(unittest.TestCase):
    def test_hand_built_profile_only_needs_the_fields_you_care_about(self) -> None:
        profile = ResumeProfile(
            skills=["Python"],
            experience=[Experience(title="Intern")],
            education=[Education(degree="B.S.")],
        )
        self.assertIsNone(profile.experience[0].organization)
        self.assertIsNone(profile.education[0].institution)
        self.assertTrue(profile.is_fully_populated)

    def test_empty_profile_reports_every_section_missing(self) -> None:
        profile = ResumeProfile()
        self.assertEqual(profile.missing_sections(), ["skills", "experience", "education"])
        self.assertFalse(profile.is_fully_populated)

    def test_missing_sections_names_only_the_empty_ones(self) -> None:
        profile = ResumeProfile(skills=["SQL"], education=[Education(degree="B.A.")])
        self.assertEqual(profile.missing_sections(), ["experience"])

    def test_skills_are_trimmed_and_deduplicated_ignoring_case(self) -> None:
        profile = ResumeProfile(skills=["  Python ", "python", "SQL", "", "   ", "Machine   Learning", "SQL"])
        self.assertEqual(profile.skills, ["Python", "SQL", "Machine Learning"])

    def test_entries_without_a_title_or_degree_are_dropped(self) -> None:
        profile = ResumeProfile(
            experience=[Experience(title="  "), Experience(title="Analyst")],
            education=[Education(degree=""), Education(degree="M.S.")],
        )
        self.assertEqual([e.title for e in profile.experience], ["Analyst"])
        self.assertEqual([e.degree for e in profile.education], ["M.S."])

    def test_blank_optional_fields_become_none(self) -> None:
        job = Experience(title="Analyst", organization="  ", start="", description=" Did \n things ")
        self.assertIsNone(job.organization)
        self.assertIsNone(job.start)
        self.assertEqual(job.description, "Did things")

    def test_round_trips_through_json(self) -> None:
        profile = ResumeProfile(
            skills=["Python", "Flask"],
            experience=[Experience(title="Intern", organization="Acme", start="May 2025", end="Present")],
            education=[Education(degree="B.S.", field_of_study="Computer Science", year="2026")],
        )
        self.assertEqual(ResumeProfile.model_validate_json(profile.model_dump_json()), profile)

    def test_model_sees_every_field_as_required(self) -> None:
        # The model skips fields it is told are optional, which left whole sections empty.
        schema = ResumeProfile.model_json_schema()
        self.assertEqual(schema["required"], ["skills", "experience", "education"])
        self.assertEqual(
            schema["$defs"]["Experience"]["required"],
            ["title", "organization", "start", "end", "description"],
        )
        self.assertEqual(
            schema["$defs"]["Education"]["required"],
            ["degree", "field_of_study", "institution", "year"],
        )


if __name__ == "__main__":
    unittest.main()
