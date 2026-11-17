"""Turn raw resume text into a ResumeProfile with a Mellea @generative function.

Use it from code:

    from analyzer.extract_resume import extract_resume
    profile = extract_resume(resume_text)

Or from the command line, run from the project root:

    uv run python -m analyzer.extract_resume --index 0
    uv run python -m analyzer.extract_resume --file path/to/resume.txt
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from mellea import MelleaSession, generative, start_session
from mellea.backends import ModelOption
from pydantic import ValidationError

from analyzer.grounding import ground
from analyzer.schemas import ResumeProfile

logger = logging.getLogger(__name__)


class ExtractionError(RuntimeError):
    """The model's answer could not be read as a ResumeProfile."""

# Settings for every extraction call:
# - Temperature 0 keeps runs repeatable.
# - Thinking is off. Granite 4.2 thinks by default, and on real resumes it spent
#   tens of thousands of tokens reasoning without ever writing the answer.
# - The context window is raised because the longest sample resumes (about
#   14,000 characters) do not fit in Ollama's default.
# - The token cap stops a runaway generation instead of letting it run for minutes.
MODEL_OPTIONS = {
    ModelOption.TEMPERATURE: 0.0,
    ModelOption.THINKING: False,
    ModelOption.CONTEXT_WINDOW: 8192,
    ModelOption.MAX_NEW_TOKENS: 3000,
}


@generative
def extract_resume_profile(resume_text: str) -> ResumeProfile:
    """Extract a structured profile from the resume text.

    Use only information that is written in the resume. Never guess or add
    anything that is not there.

    - skills: every skill, tool, programming language, framework, and
      technology the resume names. One skill per item, a few words at most,
      spelled as in the resume. Split lists apart: the line
      "Tools: Alpha, Beta, Gamma" becomes "Alpha", "Beta", "Gamma". Never
      repeat a skill. Do not include category labels, sentences, job titles,
      or durations.
    - experience: every job, internship, or project, with its title,
      organization, start date, end date, and a one-sentence description.
    - education: every degree or certificate, with its field of study,
      institution, and year.

    When the resume does not state a value, use null. Use an empty list when
    the resume has no entries for a section.
    """


def extract_resume(text: str, m: MelleaSession | None = None) -> ResumeProfile:
    """Extract a ResumeProfile from resume text.

    Every skill in the result appears in `text`. A skill the model returns that
    the resume does not mention is trimmed to the part that is mentioned, or
    dropped (and logged as a warning) when no part is.

    Pass an existing session as `m` to reuse it across calls; otherwise a new
    default session (Ollama + Granite) is started.
    """
    if not text or not text.strip():
        raise ValueError("resume text is empty")
    session = m if m is not None else start_session()
    try:
        profile = extract_resume_profile(session, resume_text=text, model_options=MODEL_OPTIONS)
    except ValidationError as e:
        # Usually the answer was cut off at the token cap, leaving incomplete JSON.
        raise ExtractionError(f"model returned an unreadable profile: {e.errors()[0]['msg']}") from e

    grounded = [ground(skill, text) for skill in profile.skills]
    invented = [skill for skill, found in zip(profile.skills, grounded) if found is None]
    if invented:
        logger.warning("Dropped %d skill(s) not found in the resume: %s", len(invented), ", ".join(invented))
    # Rebuild through the schema so skills shortened to the same text are deduplicated.
    profile = profile.model_copy(update={"skills": [skill for skill in grounded if skill is not None]})
    profile = ResumeProfile.model_validate(profile.model_dump())
    return profile


def _read_resume(args: argparse.Namespace) -> str:
    if args.file is not None:
        return args.file.read_text(encoding="utf-8")
    # Group 9's loader; importable because this module is run from the project root.
    from scripts.load_resumes import load_resumes

    resumes = load_resumes()
    if args.index >= len(resumes):
        raise IndexError(f"--index {args.index} out of range (0-{len(resumes) - 1})")
    return resumes[args.index]["resume"]


def main(argv: list[str] | None = None) -> int:
    """Extract one resume and print it as JSON. Exit code 0 = fully populated, 1 = not."""
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    parser = argparse.ArgumentParser(description="Extract a ResumeProfile from one resume.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--index", type=int, default=0, metavar="I", help="resume #I in data/resumes.json (default 0)")
    source.add_argument("--file", type=Path, metavar="PATH", help="a text file holding one resume")
    args = parser.parse_args(argv)

    try:
        text = _read_resume(args)
    except (OSError, IndexError, ValueError) as e:
        print(e, file=sys.stderr)
        return 1

    try:
        profile = extract_resume(text)
    except ExtractionError as e:
        print(e, file=sys.stderr)
        return 1
    print(profile.model_dump_json(indent=2))

    missing = profile.missing_sections()
    if missing:
        print(f"Not fully populated; empty sections: {', '.join(missing)}", file=sys.stderr)
        return 1
    print(
        f"Fully populated: {len(profile.skills)} skills, "
        f"{len(profile.experience)} experience entries, {len(profile.education)} education entries",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
