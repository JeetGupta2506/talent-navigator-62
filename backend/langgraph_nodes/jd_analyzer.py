import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    if not text:
        return ""
    # remove excessive whitespace and normalize newlines
    cleaned = re.sub(r"\s+", " ", text.replace('\r', ' ').replace('\n', ' ')).strip()
    return cleaned


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Try to parse JSON safely. If direct json.loads fails, attempt to extract the first JSON object using regex."""
    try:
        return json.loads(text)
    except Exception as e:
        logger.debug("Direct JSON parse failed: %s", e)

    # attempt to find a JSON object in the text
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        candidate = match.group(1)
        try:
            return json.loads(candidate)
        except Exception as e:
            logger.debug("Regex-extracted JSON parse failed: %s", e)

    # final fallback: try to replace single quotes with double quotes (best-effort)
    try:
        alt = text.replace("'", '"')
        return json.loads(alt)
    except Exception as e:
        logger.debug("Fallback JSON parse failed: %s", e)

    # give up — return empty structure
    return {}


async def jd_analyzer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a job description string in `state['job_description']` and return a dictionary
    with key 'jd_analysis' whose value is a parsed JSON-like structure extracted by an LLM.

    The LLM is requested to return a JSON object ONLY (no extra text) with fields:
      - role
      - required_skills (list)
      - tools (list)
      - minimum_experience (string)
      - responsibilities (list)
      - education (string)
      - employment_type (string)

    This function will try to use langchain's Gemini chat model via HumanMessage if available,
    otherwise it will raise an informative error.
    """
    raw_jd = (state or {}).get("job_description") or ""
    jd = _clean_text(raw_jd)

    if not jd:
        logger.warning("No job description provided to jd_analyzer")
        return {"jd_analysis": {}}

    # build the instruction prompt
    prompt = (
        "You are a helpful assistant that extracts structured information from a job description.\n"
        "Given the following job description, produce a JSON object ONLY (no explanation or extra text) with the exact keys:\n"
        "role, required_skills, tools, minimum_experience, responsibilities, education, employment_type.\n"
        "- role: short string title\n"
        "- required_skills: array of short strings (technology or skill names)\n"
        "- tools: array of short strings (tools or technologies)\n"
        "- minimum_experience: short string like '2 years' or 'Not specified'\n"
        "- responsibilities: array of short bullet strings (2-8 items ideally)\n"
        "- education: short string if present otherwise empty string\n"
        "- employment_type: Full-time / Part-time / Internship / Contract / Not specified\n\n"
        "Return valid JSON only.\n\n"
        f"Job Description:\n{jd}\n"
    )

    # Try to import langchain's Gemini integration
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
    except Exception as e:
        logger.exception("Failed to import LangChain's Gemini integration: %s", e)
        raise RuntimeError("LangChain Google Gemini integration not available. Try: pip install langchain-google-genai")

    # instantiate model with Google's Gemini Pro
    try:
        model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    except Exception as e:
        logger.exception("Failed to instantiate Gemini model: %s", e)
        raise

    # call the model
    try:
        messages = [HumanMessage(content=prompt)]
        response = model.invoke(messages)

        # model may return an object or a list — get text content robustly
        raw_out = ""
        if hasattr(response, "content"):
            raw_out = getattr(response, "content")
        else:
            # str or other
            raw_out = str(response)

        parsed = _safe_parse_json(raw_out)

        # normalize keys to expected shape
        normalized = {
            "role": parsed.get("role") or parsed.get("position") or "",
            "required_skills": parsed.get("required_skills") or parsed.get("skills") or [],
            "tools": parsed.get("tools") or parsed.get("technologies") or [],
            "minimum_experience": parsed.get("minimum_experience") or parsed.get("experience") or "",
            "responsibilities": parsed.get("responsibilities") or parsed.get("responsibilities_list") or [],
            "education": parsed.get("education") or "",
            "employment_type": parsed.get("employment_type") or parsed.get("employment") or "",
        }

        logger.info(f"JD Analysis complete: {normalized.get('role', 'Unknown role')}")
        return {"jd_analysis": normalized}
    except Exception as e:
        logger.exception("jd_analyzer failed: %s", e)
        # return empty structure on failure (LangGraph can inspect logs)
        return {"jd_analysis": {}}
