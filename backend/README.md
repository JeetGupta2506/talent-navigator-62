Talent Navigator - FastAPI backend

This folder contains a minimal FastAPI backend scaffold for local development.

Quick start (Windows PowerShell):

1. Create and activate a virtual environment:

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install dependencies:

   pip install -r requirements.txt

3. Run development server:

   uvicorn main:app --reload --host 0.0.0.0 --port 8000

Endpoints available:

- GET /health — health check
- POST /analyze-jd — analyze a job description (placeholder)
- POST /generate-interview — generate interview questions (placeholder)
- POST /score-answer — score candidate answers (placeholder)
- POST /screen-resume — screen a resume (placeholder)

Next steps:
- Wire these endpoints to your AI services or Supabase functions.
- Add authentication and logging.
- Add tests and CI config.

Gemini (Google) integration
---------------------------
This backend can call Google's Gemini (Generative AI) models when you provide a `GOOGLE_API_KEY`.

1. Create a file named `.env` in `backend/` or set the following environment variables in your shell:

   - `GOOGLE_API_KEY` — your Google Generative API key
   - `GEMINI_MODEL` — (optional) model id to use, defaults to `text-bison-001`

2. Install dependencies (includes `google-generativeai`):

   pip install -r requirements.txt

3. Start the server (PowerShell example):

   # from repository root
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

When `GOOGLE_API_KEY` is present, the `/analyze-jd`, `/generate-interview`, `/score-answer`, and `/screen-resume` endpoints will delegate to Gemini. If not present, the endpoints keep the local placeholder behavior.
