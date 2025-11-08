import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Try to parse JSON safely."""
    try:
        # Try to clean markdown code blocks
        cleaned = re.sub(r'```json\s*|\s*```', '', text.strip())
        return json.loads(cleaned)
    except Exception as e:
        logger.debug("Direct JSON parse failed: %s", e)

    # attempt to find a JSON object in the text
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
    LangGraph-based resume screener agent that compares resume against JD analysis.
    
    Input state structure:
        {
          "jd_analysis": {
              "role": str,
              "required_skills": List[str],
              ... (other JD fields)
          },
          "resume_text": str
        }
    
    Output structure:
        {
          "resume_eval": {
              "skill_match": int (0-100),
              "matched_skills": List[str],
              "missing_skills": List[str],
              "comment": str
          }
        }
    """
    logger.info("🔍 Resume Screener agent starting...")
    
    # Extract inputs from state
    jd_analysis = state.get("jd_analysis", {})
    resume_text = state.get("resume_text", "")
    
    # Prepare default/fallback response
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
        
        # Build the prompt
        jd_json_str = json.dumps(jd_analysis, indent=2)
        
        prompt = f"""You are an expert HR analyst. Compare the candidate's resume against the structured job description analysis below.

**Job Description Analysis:**
{jd_json_str}

**Candidate Resume:**
{resume_text}

**Your Task:**
1. Identify which required skills from the JD are present in the resume (matched_skills).
2. Identify which required skills are missing from the resume (missing_skills).
3. Calculate a Skill Match percentage (0-100) based on how many required skills are found.
4. Write a brief 1-2 sentence comment summarizing the candidate's fit.

**IMPORTANT:** Return your analysis in valid JSON format with this exact structure:
{{
  "skill_match": <integer 0-100>,
  "matched_skills": ["skill1", "skill2", ...],
  "missing_skills": ["skill3", "skill4", ...],
  "comment": "Brief summary here."
}}

Return ONLY the JSON object, no extra text."""

        messages = [HumanMessage(content=prompt)]
        response = model.invoke(messages)
        
        raw_out = response.content if hasattr(response, "content") else str(response)
        parsed = _safe_parse_json(raw_out)
        
        # Extract with fallbacks
        skill_match = parsed.get("skill_match", 0)
        matched_skills = parsed.get("matched_skills", [])
        missing_skills = parsed.get("missing_skills", [])
        comment = parsed.get("comment", "Evaluation completed.")
        
        # Ensure skill_match is an integer between 0-100
        try:
            skill_match = int(skill_match)
            skill_match = max(0, min(100, skill_match))
        except:
            skill_match = 0
        
        result = {
            "resume_eval": {
                "skill_match": skill_match,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "comment": comment
            }
        }
        
        logger.info(f"✅ Resume screening complete: {skill_match}% match with {len(matched_skills)} matched skills")
        return result
        
    except Exception as e:
        logger.exception("Resume Screener failed with Gemini, using fallback: %s", e)
        
        # Simple keyword matching fallback
        required_skills = jd_analysis.get("required_skills", [])
        if not required_skills:
            required_skills = jd_analysis.get("skills", [])
        
        resume_lower = resume_text.lower()
        matched = [skill for skill in required_skills if skill.lower() in resume_lower]
        missing = [skill for skill in required_skills if skill.lower() not in resume_lower]
        
        match_pct = int((len(matched) / len(required_skills)) * 100) if required_skills else 0
        
        return {
            "resume_eval": {
                "skill_match": match_pct,
                "matched_skills": matched,
                "missing_skills": missing,
                "comment": f"Basic keyword match: {len(matched)}/{len(required_skills)} skills found."
            }
        }
