import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

API_KEY = os.environ.get("GOOGLE_API_KEY")
MODEL = os.environ.get("GEMINI_MODEL", "text-bison-001")

_genai = None
_available = False

if API_KEY:
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=API_KEY)
        _genai = genai
        _available = True
    except Exception as e:
        logger.warning("Failed to import/configure google.generativeai: %s", e)
        _available = False
else:
    logger.info("GOOGLE_API_KEY not set — Gemini client unavailable")


def available() -> bool:
    return _available and _genai is not None


async def analyze_jd(description: str, job_title: Optional[str] = None) -> dict:
    """Ask Gemini to extract top skills; compute word_count locally."""
    from re import findall

    word_count = len(findall(r"\w+", description or ""))
    top_skills: List[str] = []
    notes = ""

    if not available():
        return {"word_count": word_count, "top_skills": top_skills, "notes": "gemini not configured"}

    prompt = f"Extract the top 8 technical skills (comma separated) mentioned in this job description. If none, return an empty line. Job description:\n{description}\n\nRespond only with a comma-separated list of skills."
    try:
        resp = _genai.generate_text(model=MODEL, prompt=prompt, max_output_tokens=256)
        raw = getattr(resp, "text", None) or str(resp)
        # parse comma-separated tokens
        skills = [s.strip() for s in raw.split(",") if s.strip()]
        top_skills = skills[:8]
        notes = "extracted by gemini"
    except Exception as e:
        logger.exception("Gemini analyze_jd failed: %s", e)
        notes = f"gemini error: {e}"

    return {"word_count": word_count, "top_skills": top_skills, "notes": notes}


async def generate_interview(description: Optional[str], job_title: Optional[str], num_questions: int = 5) -> List[str]:
    if not available():
        # fallback simple deterministic questions
        title = job_title or description or "Candidate"
        base_questions = [
            f"Tell me about your experience related to {title}.",
            "Describe a challenging problem you solved recently.",
            "How do you prioritize tasks when working under pressure?",
            "Explain a project where you worked with a team — what was your role?",
            "How do you approach debugging and root-cause analysis?",
        ]
        n = max(1, min(20, num_questions))
        return (base_questions * ((n // len(base_questions)) + 1))[:n]

    prompt = (
        f"You are an expert interviewer. Given the job title: {job_title or 'N/A'} and job description:\n{description or 'N/A'}\n\n"
        f"Generate {num_questions} clear, focused interview questions that assess both technical skills and problem-solving ability. Return each question on its own line."
    )
    try:
        resp = _genai.generate_text(model=MODEL, prompt=prompt, max_output_tokens=512)
        raw = getattr(resp, "text", None) or str(resp)
        # split by lines and filter
        questions = [q.strip("- \n\t") for q in raw.splitlines() if q.strip()]
        if not questions:
            # fallback to simple
            return await generate_interview(description, job_title, num_questions)
        return questions[:num_questions]
    except Exception as e:
        logger.exception("Gemini generate_interview failed: %s", e)
        return await generate_interview(description, job_title, num_questions)


async def score_answer(answer_text: str, rubrics: Optional[List[str]] = None) -> dict:
    # Fallback: simple length-based score if gemini unavailable
    if not available():
        length = len((answer_text or "").strip())
        score = min(100.0, (length / 500.0) * 100.0)
        feedback = "Answer is short." if length < 100 else "Answer length is reasonable."
        return {"score": round(score, 1), "feedback": feedback}

    rubric_text = "\n".join(rubrics or [])
    prompt = (
        f"You are an experienced interviewer. Given the following rubrics:\n{rubric_text or 'N/A'}\n\n"
        f"Score the following candidate answer on a scale from 0 to 100 and provide a short feedback sentence."
        f"\nAnswer:\n{answer_text}\n\nRespond in exactly this format:\nSCORE:<number>\nFEEDBACK:<one sentence>"
    )
    try:
        resp = _genai.generate_text(model=MODEL, prompt=prompt, max_output_tokens=256)
        raw = getattr(resp, "text", None) or str(resp)
        # parse
        score = 0.0
        feedback = ""
        for line in raw.splitlines():
            if line.upper().startswith("SCORE:"):
                try:
                    score = float(line.split(":", 1)[1].strip())
                except Exception:
                    pass
            if line.upper().startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
        if feedback == "":
            feedback = raw.strip()
        return {"score": round(score, 1), "feedback": feedback}
    except Exception as e:
        logger.exception("Gemini score_answer failed: %s", e)
        return {"score": 0.0, "feedback": f"gemini error: {e}"}


async def screen_resume(resume_text: str, job_description: Optional[str] = None) -> dict:
    # fallback simple screening
    if not available():
        from re import findall

        jd_words = set(w.lower() for w in findall(r"\w+", job_description or ""))
        resume_words = set(w.lower() for w in findall(r"\w+", resume_text or ""))
        if jd_words:
            matches = len(jd_words & resume_words)
            pass_rate = matches / len(jd_words)
        else:
            pass_rate = 0.0
        highlights = list((jd_words & resume_words))[:10]
        return {"pass_rate": round(pass_rate, 3), "highlights": highlights}

    prompt = (
        f"Given the job description:\n{job_description or 'N/A'}\n\nAnd the candidate resume:\n{resume_text}\n\n"
        "Provide a JSON object with keys: pass_rate (0-1 number), highlights (an array of up to 10 keywords or short phrases found in the resume that match the JD). Respond with only valid JSON."
    )
    try:
        resp = _genai.generate_text(model=MODEL, prompt=prompt, max_output_tokens=512)
        raw = getattr(resp, "text", None) or str(resp)
        # try to parse JSON safely
        import json

        parsed = json.loads(raw)
        # ensure types
        pass_rate = float(parsed.get("pass_rate", 0.0))
        highlights = parsed.get("highlights", []) or []
        return {"pass_rate": round(pass_rate, 3), "highlights": highlights[:10]}
    except Exception as e:
        logger.exception("Gemini screen_resume failed or returned non-JSON: %s", e)
        # fallback to simple extraction
        return await screen_resume(resume_text, job_description)
