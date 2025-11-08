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
    Uses only LangChain with Gemini - no fallback mechanism.
    """
    logger.info("🔍 Resume Screener agent starting...")

    jd_analysis = state.get("jd_analysis", {})
    resume_text = state.get("resume_text", "")

    if not resume_text.strip():
        logger.error("⚠️ Resume Screener: No resume text provided.")
        raise ValueError("Resume text is required for screening")

    if not jd_analysis:
        logger.error("⚠️ Resume Screener: No JD analysis provided.")
        raise ValueError("Job description analysis is required for screening")

    # Use LangChain with Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    import os

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY environment variable not set")
        raise RuntimeError("GOOGLE_API_KEY environment variable not set")

    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.2,  # Lower temperature for more consistent scoring
        google_api_key=api_key
    )

    jd_json_str = json.dumps(jd_analysis, indent=2)

    prompt = f"""
You are an expert HR analyst specializing in resume evaluation and candidate assessment. 
Your task is to perform a comprehensive skill match analysis between the candidate's resume and the job requirements.

**Job Description Analysis:**
{jd_json_str}

**Candidate Resume:**
{resume_text}

**Evaluation Guidelines:**

1. **Skill Matching Rules:**
   - Match skills semantically, not just by exact keyword (e.g., "React" matches "ReactJS", "React.js")
   - Consider skill variations and related technologies (e.g., "PostgreSQL" matches "Postgres", "ML" matches "Machine Learning")
   - Look for skills demonstrated through project descriptions, not just listed
   - Account for experience level and proficiency indicators

2. **Scoring Methodology:**
   - Base score: (# matched required skills / # total required skills) × 100
   - Bonus points (up to +15):
     * +5 if candidate exceeds minimum experience requirement
     * +5 if candidate has relevant certifications or advanced degrees
     * +5 if candidate demonstrates preferred/nice-to-have skills
   - Deductions (up to -10):
     * -5 if missing critical/must-have skills
     * -5 if experience level is below requirement
   - Final score should be capped between 0-100

3. **Matched Skills:** List all required skills found in the resume (include semantic matches)

4. **Missing Skills:** List only the required skills that are clearly absent

5. **Comment:** Provide a 2-3 sentence executive summary highlighting:
   - Overall fit strength
   - Key strengths
   - Critical gaps (if any)

Return ONLY valid JSON with this exact structure:
{{
  "skill_match": <integer between 0-100>,
  "matched_skills": ["skill1", "skill2", ...],
  "missing_skills": ["skill3", "skill4", ...],
  "comment": "Executive summary of candidate fit."
}}
"""

    messages = [HumanMessage(content=prompt)]
    response = model.invoke(messages)

    raw_out = response.content if hasattr(response, "content") else str(response)
    parsed = _safe_parse_json(raw_out)

    if not parsed:
        logger.error("Failed to parse JSON response from Gemini")
        raise ValueError("Failed to parse valid JSON response from Gemini")

    # Extract and validate
    skill_match = parsed.get("skill_match", 0)
    matched_skills = parsed.get("matched_skills", [])
    missing_skills = parsed.get("missing_skills", [])
    comment = parsed.get("comment", "Evaluation completed.")

    # Ensure proper types and normalization
    if not isinstance(matched_skills, list):
        matched_skills = []
    if not isinstance(missing_skills, list):
        missing_skills = []
    
    # Normalize skill names (preserve original casing for display, but deduplicate)
    matched_skills = list(dict.fromkeys([s.strip() for s in matched_skills if s.strip()]))
    missing_skills = list(dict.fromkeys([s.strip() for s in missing_skills if s.strip()]))
    
    # Validate and normalize score
    try:
        skill_match = int(skill_match)
        skill_match = max(0, min(100, skill_match))
    except:
        # If score is invalid, calculate from matched/total ratio
        total_skills = len(matched_skills) + len(missing_skills)
        if total_skills > 0:
            skill_match = int((len(matched_skills) / total_skills) * 100)
        else:
            skill_match = 0

    logger.info(f"✅ Resume screening complete: {skill_match}% match ({len(matched_skills)} matched, {len(missing_skills)} missing)")

    return {
        "resume_eval": {
            "skill_match": skill_match,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "comment": comment
        }
    }
