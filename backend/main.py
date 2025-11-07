from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import re
import os

try:
    from . import gemini_client
except ImportError:
    import gemini_client

app = FastAPI(title="Talent Navigator Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok"}


class JDRequest(BaseModel):
    job_title: Optional[str] = None
    description: str


class JDAnalysis(BaseModel):
    word_count: int
    top_skills: List[str]
    notes: Optional[str] = None


class GenerateInterviewRequest(BaseModel):
    job_title: Optional[str] = None
    description: Optional[str] = None
    num_questions: int = 5


class InterviewQuestions(BaseModel):
    questions: List[str]


class ScoreRequest(BaseModel):
    question_id: Optional[str] = None
    answer_text: str
    rubrics: Optional[List[str]] = None


class ScoreResponse(BaseModel):
    score: float
    feedback: str


class ScreenResumeRequest(BaseModel):
    resume_text: str
    job_description: Optional[str] = None


class ScreenResult(BaseModel):
    pass_rate: float
    highlights: List[str]


@app.post("/analyze-jd", response_model=JDAnalysis)
async def analyze_jd(payload: JDRequest):
    """Simple placeholder JD analysis.

    This currently performs a deterministic, local analysis (word counts and naive skill extraction).
    Replace with AI or external service integration as needed.
    """
    text = (payload.description or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="description is required")

    # If gemini is configured, delegate to it; otherwise use local placeholder logic
    if gemini_client.available():
        result = await gemini_client.analyze_jd(text, payload.job_title)
        return JDAnalysis(word_count=result.get("word_count", 0), top_skills=result.get("top_skills", []), notes=result.get("notes"))

    words = re.findall(r"\w+", text)
    word_count = len(words)

    # naive: extract capitalized tokens or common skill keywords
    candidates = re.findall(r"\b([A-Z][A-Za-z+#\.]{1,30})\b", payload.description)
    skill_keywords = [k for k in ["Python", "TypeScript", "React", "SQL", "Docker", "AWS", "GCP", "FastAPI"] if k.lower() in payload.description.lower()]
    top_skills = []
    # prefer explicit keywords first
    for k in skill_keywords:
        if k not in top_skills:
            top_skills.append(k)
    # then add some capitalized candidates
    for c in candidates:
        if len(top_skills) >= 8:
            break
        if c not in top_skills:
            top_skills.append(c)

    return JDAnalysis(word_count=word_count, top_skills=top_skills[:8], notes="placeholder analysis — replace with AI integration")


@app.post("/generate-interview", response_model=InterviewQuestions)
async def generate_interview(payload: GenerateInterviewRequest):
    """Generate a set of interview questions (placeholder).

    This function returns deterministic, generic questions based on the job title.
    Replace with more advanced generation logic later.
    """
    # If gemini available, delegate
    if gemini_client.available():
        questions = await gemini_client.generate_interview(payload.description, payload.job_title, payload.num_questions)
        return InterviewQuestions(questions=questions)

    title = payload.job_title or payload.description or "Candidate"
    base_questions = [
        f"Tell me about your experience related to {title}.",
        "Describe a challenging problem you solved recently.",
        "How do you prioritize tasks when working under pressure?",
        "Explain a project where you worked with a team — what was your role?",
        "How do you approach debugging and root-cause analysis?",
    ]
    # return requested number
    n = max(1, min(20, payload.num_questions))
    questions = (base_questions * ((n // len(base_questions)) + 1))[:n]
    return InterviewQuestions(questions=questions)


@app.post("/score-answer", response_model=ScoreResponse)
async def score_answer(payload: ScoreRequest):
    """Placeholder scoring: returns a score based on answer length.

    Replace with rubric/AI scoring as needed.
    """
    # If gemini available, delegate
    if gemini_client.available():
        res = await gemini_client.score_answer(payload.answer_text, payload.rubrics)
        return ScoreResponse(score=res.get("score", 0.0), feedback=res.get("feedback", ""))

    text = payload.answer_text or ""
    length = len(text.strip())
    # naive scoring: normalize length to 0-1 and scale to 0-100
    score = min(100.0, (length / 500.0) * 100.0)
    feedback = "Answer is short." if length < 100 else "Answer length is reasonable. Consider adding more concrete examples."
    return ScoreResponse(score=round(score, 1), feedback=feedback)


@app.post("/screen-resume", response_model=ScreenResult)
async def screen_resume(payload: ScreenResumeRequest):
    """Simple resume screening: looks for occurrences of job keywords and returns a pass rate.

    This is a placeholder that should be replaced by a proper screening model.
    """
    resume = payload.resume_text or ""
    jd = payload.job_description or ""
    if not resume:
        raise HTTPException(status_code=400, detail="resume_text is required")

    # If gemini available, delegate
    if gemini_client.available():
        res = await gemini_client.screen_resume(resume, jd)
        return ScreenResult(pass_rate=res.get("pass_rate", 0.0), highlights=res.get("highlights", []))

    # naive matching: count keyword overlaps
    jd_words = set(w.lower() for w in re.findall(r"\w+", jd))
    resume_words = set(w.lower() for w in re.findall(r"\w+", resume))
    if jd_words:
        matches = len(jd_words & resume_words)
        pass_rate = matches / len(jd_words)
    else:
        pass_rate = 0.0

    # highlights: show a few matched tokens
    highlights = list((jd_words & resume_words))[:10]
    return ScreenResult(pass_rate=round(pass_rate, 3), highlights=highlights)
