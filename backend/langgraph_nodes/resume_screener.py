import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Try to parse JSON safely."""
    try:
        # Clean markdown code blocks if present
        cleaned = re.sub(r'```json\s*|\s*```', '', text.strip())
        return json.loads(cleaned)
    except Exception as e:
        logger.debug("Direct JSON parse failed: %s", e)

    # Attempt to find JSON object using regex
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        candidate = match.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return {}


async def resume_screener(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare a candidate's resume against JD analysis and return skill match info.
    """
    logger.info("🔍 Resume Screener agent starting...")

    jd_analysis = state.get("jd_analysis", {})
    resume_text = state.get("resume_text", "")

    # Fallback default
    default_response = {
        "resume_eval": {
            "skill_match": 0,
            "matched_skills": [],
            "missing_skills": [],
            "comment": "Unable to evaluate resume."
        }
    }

    if not resume_text.strip():
        logger.warning("⚠️ Resume Screener: No resume text provided.")
        return default_response

    if not jd_analysis:
        logger.warning("⚠️ Resume Screener: No JD analysis provided.")
        return default_response

    # Try to use Gemini
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        import os

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable not set")

        model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=api_key
        )

        jd_json_str = json.dumps(jd_analysis, indent=2)

        prompt = f"""
You are an expert HR analyst. Compare the candidate's resume against the job description.

**Job Description Analysis:**
{jd_json_str}

**Candidate Resume:**
{resume_text}

Your Task:
1. List which required skills from the JD are present in the resume (matched_skills).
2. List which required skills are missing (missing_skills).
3. Compute a Skill Match percentage (0–100) = (#matched / #required) × 100.
4. Write a 1–2 sentence summary.

Return ONLY valid JSON:
{{
  "skill_match": <integer>,
  "matched_skills": ["skill1", "skill2", ...],
  "missing_skills": ["skill3", "skill4", ...],
  "comment": "Brief summary here."
}}
"""

        messages = [HumanMessage(content=prompt)]
        response = model.invoke(messages)

        raw_out = response.content if hasattr(response, "content") else str(response)
        parsed = _safe_parse_json(raw_out)

        # Extract safely
        skill_match = parsed.get("skill_match", 0)
        matched_skills = parsed.get("matched_skills", [])
        missing_skills = parsed.get("missing_skills", [])
        comment = parsed.get("comment", "Evaluation completed.")

        # Ensure proper types and normalization
        matched_skills = [s.strip().lower() for s in matched_skills]
        missing_skills = [s.strip().lower() for s in missing_skills]
        try:
            skill_match = int(skill_match)
            skill_match = max(0, min(100, skill_match))
        except:
            skill_match = 0

        return {
            "resume_eval": {
                "skill_match": skill_match,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "comment": comment
            }
        }

    except Exception as e:
        logger.exception("Resume Screener failed with Gemini, using fallback: %s", e)

        # --- Fallback manual skill match calculation ---
        required_skills = jd_analysis.get("required_skills", []) or jd_analysis.get("skills", [])
        required_skills = [s.strip().lower() for s in required_skills if s.strip()]

        resume_lower = resume_text.lower()

        matched = [s for s in required_skills if s in resume_lower]
        missing = [s for s in required_skills if s not in resume_lower]

        total = len(required_skills)
        skill_match = int((len(matched) / total) * 100) if total > 0 else 0

        logger.info(f"✅ Resume screening complete: {skill_match}% match ({len(matched)}/{total})")

        return {
            "resume_eval": {
                "skill_match": skill_match,
                "matched_skills": matched,
                "missing_skills": missing,
                "comment": f"Skill match: {len(matched)}/{total} required skills found ({skill_match}%)."
            }
        }
