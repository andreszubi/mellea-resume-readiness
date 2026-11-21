from __future__ import annotations
from email.charset import ALIASES
from pydantic import BaseModel, Field

class Match(BaseModel):
    score: float
    missing: list[str]

ALIASES = {
    "js": "javascript",
    "py": "python",
    "k8s": "kubernetes",
}

def normalize(skill:str) -> str:
    s = " ".join(skill.lower().split())
    return ALIASES.get(s, s)

def match(resume: ResumeProfile, job: JobRequirements) -> Match:
    have = {normalize(s) for s in resume.skills}
    required = job.requires_skills
    missing = [s for s in required if normalize(s) not in have]
    score = 100 * (len(required) - len(missing)) / len(required) if required else 100
    return Match(score=round(score, 1), missing=missing)

if __name__ == "main":
    result = match(resume,job)
    print(f"Match score: {result.score}%")
    for item in result.missing:
        print(f"Missing: {item}")

    