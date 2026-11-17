"""Check that extracted items really appear in the source text.

A small model sometimes returns a skill the resume never mentions (in testing it
copied the example skills out of its own instructions). These checks are plain
Python, so the result does not depend on the model being honest.
"""

from __future__ import annotations

import re
import unicodedata

# A word is a run of letters and digits, plus "+" and "#" so that "C++" and "C#"
# stay distinct from "C".
_WORD = re.compile(r"[a-z0-9+#]+")


def normalize(text: str) -> str:
    """Lowercase and reduce to words separated by single spaces, with a space at each end.

    Punctuation and spacing differences disappear ("Node.js" and "node js" compare
    equal), accents are removed ("Naïve" matches "Naive"), and the padding lets a
    whole-word search be a plain substring test.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " " + " ".join(_WORD.findall(plain.casefold())) + " "


def is_grounded(item: str, source: str) -> bool:
    """True if `item` appears in `source` as whole words, ignoring case, spacing, and punctuation.

    Whole words matter: "Java" is not grounded by a resume that only says "JavaScript".
    """
    return not ungrounded([item], source)


def ungrounded(items: list[str], source: str) -> list[str]:
    """The items that do not appear in `source`. An empty list means everything is grounded."""
    haystack = normalize(source)
    return [item for item in items if not normalize(item).strip() or normalize(item) not in haystack]


def ground(item: str, source: str) -> str | None:
    """Return `item` if it appears in `source`, else its longest ending that does, else None.

    The model sometimes puts a category label in front of a real entry, turning the
    resume line "Database: MySQL" into the skill "Database MySQL". Dropping leading
    words recovers "MySQL" instead of losing the skill.
    """
    words = item.split()
    for start in range(len(words)):
        candidate = " ".join(words[start:])
        if is_grounded(candidate, source):
            return candidate
    return None
