from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from . import gemini_client
except ImportError:
    import gemini_client

try:
    from .recruitment_pipeline import build_pipeline, run_pipeline
except ImportError:
    from recruitment_pipeline import build_pipeline, run_pipeline

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
    gemini_status = "available" if gemini_client.available() else "not available"
    return {
        "status": "ok",
        "gemini": gemini_status,
        "api_key_set": bool(os.environ.get("GOOGLE_API_KEY"))
    }


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
    job_description: Optional[str] = None
    question_text: Optional[str] = None


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
    """Score answer based on job description relevance and quality.

    Uses Gemini to evaluate how well the answer demonstrates skills/experience
    relevant to the job description.
    """
    # If gemini available, delegate
    if gemini_client.available():
        res = await gemini_client.score_answer(
            payload.answer_text, 
            payload.rubrics,
            payload.job_description,
            payload.question_text
        )
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


@app.post("/evaluate-candidate-file", response_model=dict)
async def evaluate_candidate_file(file: UploadFile = File(...), job_description: Optional[str] = Form(None), interview_qa: Optional[str] = Form(None)):
    """Accept a resume file, extract text, and run the full LangGraph recruitment pipeline.

    `interview_qa` is an optional JSON string (array of {question,answer}) passed as a form field.
    """
    # Read file bytes
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {e}")

    # Try to extract text (PDF / plain text)
    resume_text = ""
    try:
        if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            try:
                import io
                from PyPDF2 import PdfReader

                reader = PdfReader(io.BytesIO(contents))
                pages = [p.extract_text() or "" for p in reader.pages]
                resume_text = "\n".join(pages)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")
        else:
            resume_text = contents.decode("utf-8", errors="ignore")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract resume text: {e}")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded resume contained no extractable text")

    # Parse interview_qa if provided (expect JSON string)
    parsed_interview = []
    if interview_qa:
        import json
        try:
            parsed_interview = json.loads(interview_qa)
        except Exception:
            # ignore parse errors and treat as empty
            parsed_interview = []

    try:
        pipeline = build_pipeline()
        result = await run_pipeline(pipeline, job_description or "", resume_text, parsed_interview)

        return {
            "jd_analysis": result.get("jd_analysis", {}),
            "resume_eval": result.get("resume_eval", {}),
            "interview_eval": result.get("interview_eval", {}),
            "final_evaluation": result.get("final_evaluation", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {e}")


@app.post("/screen-resume-file", response_model=ScreenResult)
async def screen_resume_file(file: UploadFile = File(...), job_description: Optional[str] = Form(None)):
    """Accept a resume file (PDF or plain text) and screen it against the job description.

    This endpoint extracts text from common formats (PDF, plain text) and delegates to the
    same screening logic used by `/screen-resume`.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Processing resume file: {file.filename}, content_type: {file.content_type}")
    
    # Read file bytes
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {e}")

    # Try to decode as text first
    resume_text = ""
    try:
        # If the file is a PDF, use PyPDF2 to extract text
        if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader

                reader = PdfReader(contents)
                pages = []
                for p in reader.pages:
                    text = p.extract_text() or ""
                    pages.append(text)
                resume_text = "\n".join(pages)
            except Exception:
                # PyPDF2 also accepts a file-like object; try that path
                try:
                    import io
                    from PyPDF2 import PdfReader

                    reader = PdfReader(io.BytesIO(contents))
                    pages = [p.extract_text() or "" for p in reader.pages]
                    resume_text = "\n".join(pages)
                except Exception as e:
                    # fallback to empty
                    raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")
        else:
            # attempt to decode as utf-8 text
            resume_text = contents.decode("utf-8", errors="ignore")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract resume text: {e}")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded resume contained no extractable text")

    logger.info(f"Extracted {len(resume_text)} chars from {file.filename}")
    
    # Delegate to existing screening implementation
    if gemini_client.available():
        logger.info(f"Using Gemini to screen {file.filename}")
        res = await gemini_client.screen_resume(resume_text, job_description or "")
        logger.info(f"Screening result for {file.filename}: {res.get('pass_rate', 0.0)} with {len(res.get('highlights', []))} highlights")
        return ScreenResult(pass_rate=res.get("pass_rate", 0.0), highlights=res.get("highlights", []))

    # fallback naive behavior (reuse code from screen_resume)
    jd = job_description or ""
    jd_words = set(w.lower() for w in re.findall(r"\w+", jd))
    resume_words = set(w.lower() for w in re.findall(r"\w+", resume_text))
    if jd_words:
        matches = len(jd_words & resume_words)
        pass_rate = matches / len(jd_words)
    else:
        pass_rate = 0.0

    highlights = list((jd_words & resume_words))[:10]
    return ScreenResult(pass_rate=round(pass_rate, 3), highlights=highlights)


# ============================================================================
# LangGraph Pipeline Endpoint
# ============================================================================

class PipelineRequest(BaseModel):
    job_description: str
    resume_text: str
    interview_qa: Optional[List[Dict[str, str]]] = None


class PipelineResponse(BaseModel):
    jd_analysis: Dict[str, Any]
    resume_eval: Dict[str, Any]
    interview_eval: Dict[str, Any]
    final_evaluation: Dict[str, Any]


@app.post("/evaluate-candidate", response_model=PipelineResponse)
async def evaluate_candidate(payload: PipelineRequest):
    """
    Run the complete LangGraph multi-agent recruitment pipeline.
    
    This endpoint:
    1. Analyzes the job description
    2. Screens the resume against requirements
    3. Evaluates interview responses (if provided)
    4. Aggregates scores and provides hiring recommendation
    
    Returns complete state with all intermediate and final evaluations.
    """
    try:
        # Build and run the pipeline
        pipeline = build_pipeline()
        result = await run_pipeline(
            pipeline,
            job_description=payload.job_description,
            resume_text=payload.resume_text,
            interview_qa=payload.interview_qa or []
        )
        
        return PipelineResponse(
            jd_analysis=result.get("jd_analysis", {}),
            resume_eval=result.get("resume_eval", {}),
            interview_eval=result.get("interview_eval", {}),
            final_evaluation=result.get("final_evaluation", {})
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

