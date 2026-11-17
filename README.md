# mellea-resume-readiness

FIU Student Mellea Project: Resume Skills-Gap Analyzer

Compare a resume against a real job posting and see exactly which skills are missing — plus suggestions to close the gap. Built with Mellea so every "(missing) skill" is grounded in the actual postings, never made up.

## Setup

### Prerequisites
- **Python 3.11+**. uv can install it for you if you don't have it.
- **[uv](https://docs.astral.sh/uv/)**, the Python package and environment manager:
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **An LLM backend**: [Ollama](https://ollama.com) running an IBM Granite model locally, or a hosted Granite endpoint.

### Install
```bash
git clone https://github.com/swith004/mellea-resume-readiness.git   # or your fork
cd mellea-resume-readiness
uv sync          # creates .venv with Python 3.11 and installs Mellea from uv.lock
```

### Verify
```bash
uv run main.py
# -> mellea-resume-readiness is set up. Mellea version: 0.8.0
```

### Backend (Ollama + Granite)
```bash
ollama pull granite4.2:3b     # default model used by mellea.start_session()
ollama serve                  # if Ollama isn't already running
```

### Day-to-day
- Run anything inside the environment with `uv run <command>`, or activate it with `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).
- Add a dependency with `uv add <package>`. This updates `pyproject.toml` and `uv.lock`, so commit both.
- No uv? Plain pip works too: `python3.11 -m venv .venv && source .venv/bin/activate && pip install mellea`.


## Test data: real job postings

`data/` holds real postings pulled from the [USAJOBS Search API](https://developer.usajobs.gov/), saved as JSON. The included file, `data/postings_information-technology_miami-fl.json`, has 20 postings for the keyword "information technology" in Miami, FL. Each file records the query, when it was fetched, and a list of postings with `title`, `organization`, `locations`, `salary`, `summary`, `duties`, `qualifications`, `url`, and so on.

### Re-running the fetch
1. Request a free API key at <https://developer.usajobs.gov/apirequest/>.
2. Add the key and the email you registered with to `.env` (this file is gitignored):
   ```
   USAJOBS_API_KEY=your-key
   USAJOBS_EMAIL=you@example.com
   ```
3. Run the fetch. It asks for a keyword and a location:
   ```
   $ uv run scripts/fetch_postings.py
   Keyword: cybersecurity
   Location: Miami, FL
   Saved 20 postings (20 available) to data/postings_cybersecurity_miami-fl.json
   ```
   You can also pass them as options to skip the prompts. Both options are required when the script isn't run from a terminal (for example, from another script):
   ```bash
   uv run scripts/fetch_postings.py --keyword "cybersecurity" --location "Orlando, FL"
   ```
   The output goes to `data/postings_<keyword>_<location>.json`, overwriting any earlier fetch of the same query. Run `--help` to see all options.

> **Tip:** USAJOBS only lists federal jobs, and federal job titles rarely say "software developer". That keyword returned just 1 posting in Miami, while "information technology" returned 188, and the top 20 are almost all tech roles. That's the search used for the included file.

## Test data: sample resumes

`scripts/fetch_resumes.py` downloads the [Resume Dataset](https://huggingface.co/datasets/Sachinkelenjaguri/Resume_dataset) from Hugging Face and saves it as JSON. The included file, `data/resumes.json`, has 962 resumes across 25 job categories (only 166 are unique, the source repeats the rest). It records the source, when it was fetched, and a list of resumes with `category` and `resume` (the full text).

### Re-running the fetch
No API key is needed:
```bash
uv run scripts/fetch_resumes.py
```
The output goes to `data/resumes.json`, overwriting any earlier fetch.

### Browsing and loading the resumes
`scripts/load_resumes.py` reads `data/resumes.json` and prints the resumes. With no arguments it lists all 962 resumes, duplicates included, one line each: `#<index>  [<category>]  <char count>  <first 60 chars>...`, then a summary line.
```bash
uv run scripts/load_resumes.py # lists every resume
uv run scripts/load_resumes.py --category "Data Science" --unique --limit 5
uv run scripts/load_resumes.py --search "tensorflow" --full --limit 1
uv run scripts/load_resumes.py --index 12 --full
```

The flags are optional and can be combined. A resume must match all of them to be shown.

| Flag | What it does |
| --- | --- |
| `--category NAME` | Only resumes in this category (case-insensitive). An unknown name prints the valid categories with counts and exits with status 2. |
| `--search TEXT` | Only resumes whose text contains `TEXT` (case-insensitive). |
| `--unique` | Drop duplicate resume texts, keeping the first. |
| `--limit N` | Show at most `N` resumes. |
| `--index I` | Show only resume `#I`. Indexes start at 0 and always refer to the position in the file, whatever other filters are used. |
| `--full` | Print the complete resume text (with a header line) instead of the one-line summary. |
| `--max-chars N` | With `--full`, cut each resume off after `N` characters and note how many were left out. Default `0` means no limit. |
| `--list-categories` | Print each category and its resume count, then exit. |


## Resume extraction: `ResumeProfile`

`analyzer/` turns raw resume text into typed data.

- `analyzer/schemas.py` holds the data classes and nothing else, so any group can import them and build test objects by hand:
  ```python
  from analyzer import Education, Experience, ResumeProfile

  profile = ResumeProfile(
      skills=["Python", "SQL"],
      experience=[Experience(title="Intern", organization="Acme")],
      education=[Education(degree="B.S.", field_of_study="Computer Science")],
  )
  ```
  | Class | Fields |
  | --- | --- |
  | `ResumeProfile` | `skills: list[str]`, `experience: list[Experience]`, `education: list[Education]` |
  | `Experience` | `title: str`, then optional `organization`, `start`, `end`, `description` |
  | `Education` | `degree: str`, then optional `field_of_study`, `institution`, `year` |

  Optional fields are `None` when the resume does not state them. Dates are kept as written (`"May 2021"`, `"Present"`). Skills are trimmed and de-duplicated ignoring case. `profile.missing_sections()` lists the sections that came back empty.

- `analyzer/extract_resume.py` holds the Mellea `@generative` function and the `extract_resume(text) -> ResumeProfile` wrapper around it:
  ```python
  from analyzer.extract_resume import extract_resume

  profile = extract_resume(resume_text)
  ```
  Every skill it returns appears in the resume text. The check is plain Python in `analyzer/grounding.py` (whole words, ignoring case, spacing, punctuation, and accents), so it does not rely on the model. A skill the resume never mentions is dropped and logged.

### Running it
Run from the project root. It prints the profile as JSON and exits with status 1 if any section is empty:
```bash
uv run python -m analyzer.extract_resume --index 1                       # resume #1 in data/resumes.json
uv run python -m analyzer.extract_resume --file tests/fixtures/sample_resume.txt
```

### Tests
```bash
uv run python -m unittest discover -s tests -t .                         # no model calls
RUN_LLM_TESTS=1 uv run python -m unittest tests.test_extract_resume      # calls the model
```
