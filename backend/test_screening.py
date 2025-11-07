"""
Test script to diagnose resume screening scores
"""
import asyncio
import os

# Sample JD (you can replace with your actual JD)
SAMPLE_JD = """
Data Scientist / ML Engineer

Required Skills:
- Python programming
- Machine Learning (Scikit-learn, XGBoost, ensemble methods)
- Deep Learning (NLP, Generative AI)
- Data preprocessing and feature engineering
- Statistical analysis
- Model deployment and MLOps
"""

# Sample resume content (simulating what was extracted from PDF)
SAMPLE_RESUME = """
Driti Rathod - SVNIT

Education: B.Tech in Computer Science

Skills:
- Python, Machine Learning, Deep Learning
- Data preprocessing, NLP, Generative AI
- Scikit-learn, XGBoost, Ensemble Learning, Streamlit
"""

async def test_screening():
    print("=" * 60)
    print("RESUME SCREENING DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Check if API key is set
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        print(f"✓ GOOGLE_API_KEY is set (first 10 chars: {api_key[:10]}...)")
    else:
        print("✗ GOOGLE_API_KEY is NOT set - will use fallback keyword matching")
    
    print("\n" + "-" * 60)
    print("Job Description:")
    print("-" * 60)
    print(SAMPLE_JD)
    
    print("\n" + "-" * 60)
    print("Resume:")
    print("-" * 60)
    print(SAMPLE_RESUME)
    
    # Import and test the screening function
    try:
        import gemini_client
        
        print("\n" + "-" * 60)
        print("Testing resume screening...")
        print("-" * 60)
        
        result = await gemini_client.screen_resume(SAMPLE_RESUME, SAMPLE_JD)
        
        print(f"\n✓ Screening completed!")
        print(f"  Pass Rate: {result['pass_rate']} ({result['pass_rate'] * 100:.1f}%)")
        print(f"  Matched Skills: {result['highlights']}")
        
        if result['pass_rate'] < 0.3:
            print("\n⚠️ WARNING: Score is unexpectedly low!")
            print("   This might indicate an issue with the screening logic.")
            print("   Expected score for this sample should be 0.7-0.9 (70-90%)")
        elif result['pass_rate'] >= 0.7:
            print("\n✓ Score looks reasonable!")
        else:
            print("\n⚡ Score is moderate (30-70%)")
        
    except Exception as e:
        print(f"\n✗ Error during screening: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_screening())
