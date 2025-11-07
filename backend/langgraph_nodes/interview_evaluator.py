import json
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _safe_parse_json(text: str) -> Dict[str, Any]:
    """Try to parse JSON safely."""
    try:
        cleaned = re.sub(r'```json\s*|\s*```', '', text.strip())
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return {}


async def interview_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates interview questions and answers based on JD requirements.
    
    Input state structure:
        {
          "jd_analysis": {...},
          "resume_eval": {...},
          "interview_qa": [
              {"question": str, "answer": str},
              ...
          ]
        }
    
    Output structure:
        {
          "interview_eval": {
              "overall_score": int (0-100),
              "question_scores": [
                  {"question": str, "score": int, "feedback": str},
                  ...
              ],
              "strengths": List[str],
              "concerns": List[str]
          }
        }
    """
    logger.info("💬 Interview Evaluator agent starting...")
    
    jd_analysis = state.get("jd_analysis", {})
    interview_qa = state.get("interview_qa", [])
    
    default_response = {
        "interview_eval": {
            "overall_score": 0,
            "question_scores": [],
            "strengths": [],
            "concerns": ["No interview data provided"]
        }
    }
    
    if not interview_qa:
        logger.warning("⚠️ Interview Evaluator: No interview Q&A provided.")
        return default_response
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        
        model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
        
        # Build Q&A text
        qa_text = "\n\n".join([
            f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}"
            for i, qa in enumerate(interview_qa)
        ])
        
        jd_json_str = json.dumps(jd_analysis, indent=2)
        
        prompt = f"""You are an experienced technical interviewer. Evaluate the candidate's interview responses based on the job requirements.

**Job Requirements:**
{jd_json_str}

**Interview Q&A:**
{qa_text}

**Evaluation Criteria:**
- Relevance to job requirements (40%)
- Technical depth and accuracy (30%)
- Communication clarity (15%)
- Examples and specificity (15%)

**Your Task:**
1. Score each answer (0-100)
2. Calculate an overall interview score (0-100)
3. Identify 2-3 strengths demonstrated
4. Identify 1-2 concerns or gaps

Return ONLY valid JSON with this structure:
{{
  "overall_score": <integer 0-100>,
  "question_scores": [
    {{"question": "Q1 text", "score": <0-100>, "feedback": "brief feedback"}},
    ...
  ],
  "strengths": ["strength1", "strength2", ...],
  "concerns": ["concern1", "concern2", ...]
}}"""

        messages = [HumanMessage(content=prompt)]
        response = model.invoke(messages)
        
        raw_out = response.content if hasattr(response, "content") else str(response)
        parsed = _safe_parse_json(raw_out)
        
        overall_score = parsed.get("overall_score", 0)
        question_scores = parsed.get("question_scores", [])
        strengths = parsed.get("strengths", [])
        concerns = parsed.get("concerns", [])
        
        # Validate and normalize
        try:
            overall_score = max(0, min(100, int(overall_score)))
        except:
            overall_score = 0
        
        result = {
            "interview_eval": {
                "overall_score": overall_score,
                "question_scores": question_scores,
                "strengths": strengths,
                "concerns": concerns
            }
        }
        
        logger.info(f"✅ Interview evaluation complete: {overall_score}% overall score")
        return result
        
    except Exception as e:
        logger.exception("Interview Evaluator failed: %s", e)
        
        # Simple fallback - basic length-based scoring
        total_score = 0
        question_scores = []
        
        for qa in interview_qa:
            answer_len = len(qa.get("answer", "").strip())
            score = min(100, int((answer_len / 300) * 100))
            total_score += score
            question_scores.append({
                "question": qa.get("question", ""),
                "score": score,
                "feedback": "Basic evaluation based on answer length."
            })
        
        overall = total_score // len(interview_qa) if interview_qa else 0
        
        return {
            "interview_eval": {
                "overall_score": overall,
                "question_scores": question_scores,
                "strengths": ["Provided answers to questions"],
                "concerns": ["Unable to perform detailed AI evaluation"]
            }
        }
