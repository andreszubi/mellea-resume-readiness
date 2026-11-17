# mellea-resume-readiness

FIU Student Mellea Project: Resume Skills-Gap Analyzer

Compare a resume against a real job posting and see exactly which skills are missing — plus suggestions to close the gap. Built with Mellea so every "(missing) skill" is grounded in the actual postings, never made up.

## Setup
Requirements: Python 3.11+ (3.12 recommended) and a backend — [Ollama](https://ollama.com) running an IBM Granite model locally, or a hosted Granite endpoint.

1. Clone the repo and create a virtual environment:

   ```bash
   git clone https://github.com/<your-username>/mellea-resume-readiness.git
   cd mellea-resume-readiness
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```

2. Install the dependencies (Mellea is pinned in `requirements.txt`):

   ```bash
   pip install -r requirements.txt
   ```

3. Pull the Granite model Mellea uses by default (about 2.2 GB) and make sure Ollama is running:

   ```bash
   ollama pull granite4.2:3b
   ```

4. Check that everything works:

   ```bash
   python -c "import mellea; print(mellea.start_session().instruct('Reply with one word: ready').value)"
   ```

The virtual environment (`.venv/`) is not committed — each teammate creates their own with the steps above.


## How to contribute
Fork this repo, pick an open issue, and open a pull request. The interface (CLI, notebook, or web app) is your team's choice — the issues specify the outcome, not the implementation.
