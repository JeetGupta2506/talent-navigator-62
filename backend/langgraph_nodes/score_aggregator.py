import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def score_aggregator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates all evaluation scores and provides a final hiring recommendation.
    
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
              "summary": str,
              "key_strengths": List[str],
              "key_concerns": List[str]
          }
        }
    """
    logger.info("📊 Score Aggregator agent starting...")
    
    resume_eval = state.get("resume_eval", {})
    interview_eval = state.get("interview_eval", {})
    jd_analysis = state.get("jd_analysis", {})
    
    # Extract scores
    resume_score = resume_eval.get("skill_match", 0)
    interview_score = interview_eval.get("overall_score", 0)
    
    # Calculate weighted overall score
    # Resume: 40%, Interview: 60%
    overall_score = int((resume_score * 0.4) + (interview_score * 0.6))
    
    # Determine recommendation
    if overall_score >= 80:
        recommendation = "Strong Hire"
    elif overall_score >= 65:
        recommendation = "Hire"
    elif overall_score >= 50:
        recommendation = "Maybe"
    else:
        recommendation = "No Hire"
    
    # Aggregate strengths and concerns
    key_strengths = []
    key_concerns = []
    
    # From resume
    matched_skills = resume_eval.get("matched_skills", [])
    if matched_skills:
        key_strengths.append(f"Strong skill match: {', '.join(matched_skills[:3])}")
    
    missing_skills = resume_eval.get("missing_skills", [])
    if missing_skills:
        key_concerns.append(f"Missing skills: {', '.join(missing_skills[:3])}")
    
    # From interview
    interview_strengths = interview_eval.get("strengths", [])
    key_strengths.extend(interview_strengths[:2])
    
    interview_concerns = interview_eval.get("concerns", [])
    key_concerns.extend(interview_concerns[:2])
    
    # Generate summary
    role = jd_analysis.get("role", "the position")
    summary = f"""
Candidate evaluated for {role}.
Resume shows {resume_score}% skill match with {len(matched_skills)} key skills.
Interview performance scored {interview_score}%.
Overall assessment: {overall_score}% - {recommendation}.
""".strip()
    
    result = {
        "final_evaluation": {
            "overall_score": overall_score,
            "resume_score": resume_score,
            "interview_score": interview_score,
            "recommendation": recommendation,
            "summary": summary,
            "key_strengths": key_strengths[:5],  # Top 5
            "key_concerns": key_concerns[:3]     # Top 3
        }
    }
    
    logger.info(f"✅ Final evaluation complete: {overall_score}% - {recommendation}")
    logger.info(f"   Resume: {resume_score}%, Interview: {interview_score}%")
    
    return result
