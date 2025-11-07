"""
LangGraph Recruitment Pipeline

This module builds a multi-agent workflow that processes candidates through:
1. Job Description Analysis
2. Resume Screening
3. Interview Evaluation
4. Score Aggregation and Recommendation

Usage:
    from backend.recruitment_pipeline import build_pipeline, run_pipeline
    
    pipeline = build_pipeline()
    
    result = await run_pipeline(
        pipeline,
        job_description="...",
        resume_text="...",
        interview_qa=[
            {"question": "...", "answer": "..."},
            ...
        ]
    )
"""

import logging
from typing import Any, Dict, List, Optional
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from langgraph_nodes.jd_analyzer import jd_analyzer
from langgraph_nodes.resume_screener import resume_screener
from langgraph_nodes.interview_evaluator import interview_evaluator
from langgraph_nodes.score_aggregator import score_aggregator

logger = logging.getLogger(__name__)


class RecruitmentState(TypedDict, total=False):
    """State schema for the recruitment pipeline."""
    # Input
    job_description: str
    resume_text: str
    interview_qa: List[Dict[str, str]]
    
    # Intermediate results
    jd_analysis: Dict[str, Any]
    resume_eval: Dict[str, Any]
    interview_eval: Dict[str, Any]
    
    # Final output
    final_evaluation: Dict[str, Any]


def build_pipeline():
    """
    Build and compile the LangGraph recruitment pipeline.
    
    Returns:
        Compiled StateGraph that can be invoked with initial state.
    """
    logger.info("🔨 Building recruitment pipeline...")
    
    # Create the state graph
    workflow = StateGraph(RecruitmentState)
    
    # Add nodes
    workflow.add_node("jd_analyzer", jd_analyzer)
    workflow.add_node("resume_screener", resume_screener)
    workflow.add_node("interview_evaluator", interview_evaluator)
    workflow.add_node("score_aggregator", score_aggregator)
    
    # Define the flow
    workflow.set_entry_point("jd_analyzer")
    workflow.add_edge("jd_analyzer", "resume_screener")
    workflow.add_edge("resume_screener", "interview_evaluator")
    workflow.add_edge("interview_evaluator", "score_aggregator")
    workflow.add_edge("score_aggregator", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("✅ Pipeline built successfully")
    return app


async def run_pipeline(
    pipeline,
    job_description: str,
    resume_text: str,
    interview_qa: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Run the complete recruitment pipeline.
    
    Args:
        pipeline: Compiled LangGraph pipeline from build_pipeline()
        job_description: The job description text
        resume_text: The candidate's resume text
        interview_qa: List of interview questions and answers (optional)
                     Format: [{"question": "...", "answer": "..."}, ...]
    
    Returns:
        Complete state including final_evaluation
    """
    logger.info("🚀 Starting recruitment pipeline execution...")
    
    # Prepare initial state
    initial_state: RecruitmentState = {
        "job_description": job_description,
        "resume_text": resume_text,
        "interview_qa": interview_qa or []
    }
    
    # Run the pipeline
    try:
        result = await pipeline.ainvoke(initial_state)
        logger.info("✅ Pipeline execution complete")
        return result
    except Exception as e:
        logger.exception(f"❌ Pipeline execution failed: {e}")
        raise


# Convenience function for quick testing
async def quick_evaluate(
    job_description: str,
    resume_text: str,
    interview_qa: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Quick evaluation - builds pipeline and runs it in one call.
    
    Returns:
        The final_evaluation dict from the pipeline result
    """
    pipeline = build_pipeline()
    result = await run_pipeline(pipeline, job_description, resume_text, interview_qa)
    return result.get("final_evaluation", {})


if __name__ == "__main__":
    # Example usage for testing
    import asyncio
    
    async def test_pipeline():
        sample_jd = """
        Senior Python Developer
        Required Skills: Python, Django, PostgreSQL, AWS, Docker
        5+ years experience required
        """
        
        sample_resume = """
        John Doe
        Senior Software Engineer
        8 years of experience with Python, Django, Flask
        Worked with PostgreSQL, MySQL, MongoDB
        Deployed applications on AWS and GCP
        Expert in Docker and Kubernetes
        """
        
        sample_interview = [
            {
                "question": "Describe your experience with Django",
                "answer": "I have 6 years of Django experience, built multiple production APIs"
            },
            {
                "question": "How do you handle database optimization?",
                "answer": "I use indexing, query optimization, and caching strategies"
            }
        ]
        
        result = await quick_evaluate(sample_jd, sample_resume, sample_interview)
        
        print("\n" + "="*60)
        print("FINAL EVALUATION")
        print("="*60)
        print(f"Overall Score: {result.get('overall_score')}%")
        print(f"Recommendation: {result.get('recommendation')}")
        print(f"\nSummary:\n{result.get('summary')}")
        print(f"\nStrengths: {result.get('key_strengths')}")
        print(f"\nConcerns: {result.get('key_concerns')}")
        print("="*60)
    
    asyncio.run(test_pipeline())
