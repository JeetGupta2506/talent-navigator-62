"""
Test script for the LangGraph recruitment pipeline.

Run this to see the complete workflow in action:
    python test_pipeline.py
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from recruitment_pipeline import build_pipeline, run_pipeline


async def test_pipeline():
    print("\n" + "="*80)
    print("🚀 TESTING LANGGRAPH RECRUITMENT PIPELINE")
    print("="*80 + "\n")
    
    # Sample data
    job_description = """
    Machine Learning Engineer - Senior Level
    
    We're looking for an experienced ML Engineer to join our AI team.
    
    Required Skills:
    - Python, TensorFlow, PyTorch
    - Machine Learning, Deep Learning
    - NLP, Computer Vision
    - AWS or GCP
    - Docker, Kubernetes
    
    Minimum 5 years of ML experience required.
    Master's degree in Computer Science or related field preferred.
    """
    
    resume_text = """
    JOHN DOE
    Senior Machine Learning Engineer
    
    Experience:
    - 7 years of ML/AI development
    - Expert in Python, TensorFlow, and PyTorch
    - Built production NLP systems processing 1M+ documents
    - Deployed models on AWS using Docker and Kubernetes
    - Led team of 5 ML engineers
    
    Education:
    - M.S. Computer Science, Stanford University
    - B.S. Computer Engineering, MIT
    
    Skills:
    Python, TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy
    NLP, Deep Learning, Computer Vision, Reinforcement Learning
    AWS, Docker, Kubernetes, MLflow, Airflow
    
    Projects:
    - Built sentiment analysis system with 95% accuracy
    - Developed object detection pipeline for autonomous vehicles
    - Created recommendation engine serving 10M users
    """
    
    interview_qa = [
        {
            "question": "Can you describe your experience with deep learning frameworks?",
            "answer": "I've been working with TensorFlow for 5 years and PyTorch for 3 years. I prefer PyTorch for research and prototyping due to its dynamic computation graph, while I use TensorFlow for production deployments. I've built CNNs, RNNs, and Transformers for various tasks."
        },
        {
            "question": "How do you handle model deployment and monitoring in production?",
            "answer": "I use Docker to containerize models, deploy them on Kubernetes for scalability, and monitor with MLflow and Prometheus. I implement A/B testing to compare model versions and set up alerts for performance degradation. I also maintain model versioning and rollback capabilities."
        },
        {
            "question": "Tell me about a challenging ML project you worked on.",
            "answer": "I led the development of a real-time object detection system for autonomous vehicles. The challenge was achieving 30 FPS inference while maintaining 95% accuracy. I optimized the model using TensorRT, implemented efficient preprocessing pipelines, and deployed it on edge devices with limited compute. The system is now running in 500+ vehicles."
        }
    ]
    
    print("📝 Job Description:")
    print(job_description[:200] + "...\n")
    
    print("📄 Resume:")
    print(resume_text[:200] + "...\n")
    
    print("💬 Interview Q&A:")
    for i, qa in enumerate(interview_qa, 1):
        print(f"  Q{i}: {qa['question'][:60]}...")
        print(f"  A{i}: {qa['answer'][:60]}...\n")
    
    print("="*80)
    print("⚙️  RUNNING PIPELINE...")
    print("="*80 + "\n")
    
    # Build and run pipeline
    pipeline = build_pipeline()
    result = await run_pipeline(
        pipeline,
        job_description=job_description,
        resume_text=resume_text,
        interview_qa=interview_qa
    )
    
    # Display results
    print("\n" + "="*80)
    print("📊 PIPELINE RESULTS")
    print("="*80 + "\n")
    
    # 1. JD Analysis
    jd_analysis = result.get("jd_analysis", {})
    print("1️⃣  JOB DESCRIPTION ANALYSIS")
    print("-" * 40)
    print(f"   Role: {jd_analysis.get('role', 'N/A')}")
    print(f"   Required Skills: {', '.join(jd_analysis.get('required_skills', [])[:5])}")
    print(f"   Min Experience: {jd_analysis.get('minimum_experience', 'N/A')}")
    print()
    
    # 2. Resume Evaluation
    resume_eval = result.get("resume_eval", {})
    print("2️⃣  RESUME SCREENING")
    print("-" * 40)
    print(f"   Skill Match: {resume_eval.get('skill_match', 0)}%")
    print(f"   Matched Skills: {', '.join(resume_eval.get('matched_skills', [])[:5])}")
    print(f"   Missing Skills: {', '.join(resume_eval.get('missing_skills', [])[:3]) or 'None'}")
    print(f"   Comment: {resume_eval.get('comment', 'N/A')}")
    print()
    
    # 3. Interview Evaluation
    interview_eval = result.get("interview_eval", {})
    print("3️⃣  INTERVIEW EVALUATION")
    print("-" * 40)
    print(f"   Overall Score: {interview_eval.get('overall_score', 0)}%")
    print(f"   Strengths: {', '.join(interview_eval.get('strengths', [])[:3])}")
    print(f"   Concerns: {', '.join(interview_eval.get('concerns', [])[:2]) or 'None'}")
    print()
    
    # 4. Final Evaluation
    final_eval = result.get("final_evaluation", {})
    print("4️⃣  FINAL EVALUATION")
    print("-" * 40)
    print(f"   Overall Score: {final_eval.get('overall_score', 0)}%")
    print(f"   Resume Score: {final_eval.get('resume_score', 0)}%")
    print(f"   Interview Score: {final_eval.get('interview_score', 0)}%")
    print(f"   Recommendation: ⭐ {final_eval.get('recommendation', 'N/A')} ⭐")
    print()
    print(f"   Summary:")
    print(f"   {final_eval.get('summary', 'N/A')}")
    print()
    print(f"   Key Strengths:")
    for strength in final_eval.get('key_strengths', [])[:5]:
        print(f"   ✅ {strength}")
    print()
    if final_eval.get('key_concerns'):
        print(f"   Key Concerns:")
        for concern in final_eval.get('key_concerns', [])[:3]:
            print(f"   ⚠️  {concern}")
    
    print("\n" + "="*80)
    print("✅ PIPELINE TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
