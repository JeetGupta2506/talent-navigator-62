import logging
import os
import json
import re
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


async def score_aggregator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates all evaluation scores and provides a final hiring recommendation.
    Uses LLM to generate an HR-style summary with structured output.
    
    Input state structure:
        {
          "jd_analysis": {...},
          "resume_eval": {
              "skill_match": int,
              "matched_skills": List[str],
              "missing_skills": List[str],
              "comment": str
          },
          "interview_eval": {
              "overall_score": int,
              "question_scores": [...],
              "strengths": List[str],
              "concerns": List[str]
          }
        }
    
    Output structure:
        {
          "final_evaluation": {
              "overall_score": int (0-100),
              "resume_score": int,
              "interview_score": int,
              "recommendation": str ("Strong Hire" | "Hire" | "Maybe" | "No Hire"),
              "summary": str (HR-style executive summary),
              "key_strengths": List[str],
              "key_concerns": List[str]
          }
        }
    """
    logger.info("📊 Score Aggregator agent starting...")
    
    # Get API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY environment variable not set")
        raise RuntimeError("GOOGLE_API_KEY environment variable not set. Please set it in your .env file.")
    
    resume_eval = state.get("resume_eval", {})
    interview_eval = state.get("interview_eval", {})
    jd_analysis = state.get("jd_analysis", {})
    
    # Extract scores
    resume_score = resume_eval.get("skill_match", 0)
    interview_score = interview_eval.get("overall_score", 0)
    
    # Calculate weighted overall score
    # Resume: 50%, Interview: 50%
    overall_score = int(round((resume_score * 0.5) + (interview_score * 0.5)))
    
    # Determine recommendation based on 4-tier system
    if overall_score >= 80:
        initial_recommendation = "Strong Hire"
    elif overall_score >= 65:
        initial_recommendation = "Hire"
    elif overall_score >= 50:
        initial_recommendation = "Maybe"
    else:
        initial_recommendation = "No Hire"
    
    # Prepare data for LLM
    role = jd_analysis.get("role", "the position")
    matched_skills = resume_eval.get("matched_skills", [])
    missing_skills = resume_eval.get("missing_skills", [])
    interview_strengths = interview_eval.get("strengths", [])
    interview_concerns = interview_eval.get("concerns", [])
    
    # Aggregate key strengths and concerns
    key_strengths = []
    key_concerns = []
    
    # From resume
    if matched_skills:
        key_strengths.append(f"Strong skill match: {', '.join(matched_skills[:3])}")
    if missing_skills:
        key_concerns.append(f"Missing skills: {', '.join(missing_skills[:3])}")
    
    # From interview
    key_strengths.extend(interview_strengths[:2])
    key_concerns.extend(interview_concerns[:2])
    
    # Build prompt for LLM to generate executive summary
    prompt = f"""You are an HR manager writing a final candidate evaluation report.

**Job Role:** {role}

**Resume Evaluation (40% weight):**
- Skill Match Score: {resume_score}%
- Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}
- Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}

**Interview Evaluation (60% weight):**
- Interview Score: {interview_score}%
- Strengths: {', '.join(interview_strengths) if interview_strengths else 'None'}
- Concerns: {', '.join(interview_concerns) if interview_concerns else 'None'}

**Calculated Overall Score:** {overall_score}/100
**Recommendation:** {initial_recommendation}

Write a concise executive summary (2-4 sentences) that:
1. Summarizes the candidate's overall fit for the {role} position
2. Highlights their strongest qualities
3. Notes any areas of concern
4. Justifies the {initial_recommendation} recommendation

Return ONLY the summary text (no JSON, no formatting, just the paragraph).
"""
    
    try:
        # Initialize Gemini model
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3,
            google_api_key=api_key
        )
        
        # Call LLM
        logger.info("🤖 Calling LLM to generate executive summary...")
        response = model.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
        
        logger.info(f"📄 LLM generated summary")
        
        # Build final evaluation
        final_evaluation = {
            "overall_score": overall_score,
            "resume_score": resume_score,
            "interview_score": interview_score,
            "recommendation": initial_recommendation,
            "summary": summary,
            "key_strengths": key_strengths[:5],  # Top 5
            "key_concerns": key_concerns[:3]     # Top 3
        }
        
        logger.info(f"✅ Final evaluation complete: {overall_score}% - {initial_recommendation}")
        logger.info(f"   Resume: {resume_score}%, Interview: {interview_score}%")
        print(f"\n✅ SUCCESS: Final score {overall_score}% - Recommendation: {initial_recommendation}\n")
        
        return {"final_evaluation": final_evaluation}
    
    except Exception as e:
        logger.error(f"❌ Error in score aggregator: {str(e)}")
        print(f"\n❌ FAILURE: Score aggregator encountered an error: {str(e)}\n")
        
        # Return fallback response
        fallback_summary = f"Candidate evaluated for {role}. Resume shows {resume_score}% skill match with {len(matched_skills)} key skills. Interview performance scored {interview_score}%. Overall assessment: {overall_score}% - {initial_recommendation}."
        
        fallback_evaluation = {
            "overall_score": overall_score,
            "resume_score": resume_score,
            "interview_score": interview_score,
            "recommendation": initial_recommendation,
            "summary": fallback_summary,
            "key_strengths": key_strengths[:5],
            "key_concerns": key_concerns[:3]
        }
        return {"final_evaluation": fallback_evaluation}
