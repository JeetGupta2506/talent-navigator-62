# LangGraph Multi-Agent Recruitment Pipeline

A sophisticated AI-powered recruitment system using LangGraph to orchestrate multiple specialized agents for comprehensive candidate evaluation.

## 🏗️ Architecture

The pipeline implements a **multi-agent workflow** with four specialized agents:

```
┌─────────────────┐
│ Job Description │
│    Analyzer     │ ────┐
└─────────────────┘     │
                        ▼
                  ┌──────────┐
                  │ Resume   │
                  │ Screener │ ────┐
                  └──────────┘     │
                                   ▼
                             ┌──────────┐
                             │Interview │
                             │Evaluator │ ────┐
                             └──────────┘     │
                                              ▼
                                        ┌───────────┐
                                        │  Score    │
                                        │Aggregator │
                                        └───────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │Final Evaluation │
                                     │& Recommendation │
                                     └─────────────────┘
```

## 📋 Components

### 1. **JD Analyzer Agent** (`langgraph_nodes/jd_analyzer.py`)
- **Purpose**: Extracts structured information from job descriptions
- **Output**: 
  - Role/position title
  - Required skills
  - Tools and technologies
  - Minimum experience
  - Responsibilities
  - Education requirements
  - Employment type

### 2. **Resume Screener Agent** (`langgraph_nodes/resume_screener.py`)
- **Purpose**: Matches candidate resume against job requirements
- **Output**:
  - Skill match percentage (0-100)
  - List of matched skills
  - List of missing skills
  - Summary comment

### 3. **Interview Evaluator Agent** (`langgraph_nodes/interview_evaluator.py`)
- **Purpose**: Evaluates interview responses for technical depth and relevance
- **Output**:
  - Overall interview score (0-100)
  - Individual question scores with feedback
  - Identified strengths
  - Identified concerns

### 4. **Score Aggregator Agent** (`langgraph_nodes/score_aggregator.py`)
- **Purpose**: Combines all evaluations into final hiring recommendation
- **Scoring Weights**:
  - Resume: 40%
  - Interview: 60%
- **Output**:
  - Overall score (0-100)
  - Recommendation: "Strong Hire" | "Hire" | "Maybe" | "No Hire"
  - Executive summary
  - Key strengths and concerns

## 🚀 Usage

### API Endpoint

```bash
POST http://localhost:8000/evaluate-candidate
```

**Request Body:**
```json
{
  "job_description": "Senior Python Developer...",
  "resume_text": "John Doe, 5 years Python experience...",
  "interview_qa": [
    {
      "question": "Tell me about your Python experience",
      "answer": "I have 5 years of Python development..."
    }
  ]
}
```

**Response:**
```json
{
  "jd_analysis": {
    "role": "Senior Python Developer",
    "required_skills": ["Python", "Django", "PostgreSQL"],
    "minimum_experience": "5 years"
  },
  "resume_eval": {
    "skill_match": 85,
    "matched_skills": ["Python", "Django"],
    "missing_skills": ["PostgreSQL"],
    "comment": "Strong technical background..."
  },
  "interview_eval": {
    "overall_score": 78,
    "strengths": ["Deep Python expertise", "Clear communication"],
    "concerns": ["Limited database experience"]
  },
  "final_evaluation": {
    "overall_score": 81,
    "resume_score": 85,
    "interview_score": 78,
    "recommendation": "Strong Hire",
    "summary": "Candidate evaluated for Senior Python Developer...",
    "key_strengths": ["Strong skill match: Python, Django", ...],
    "key_concerns": ["Missing skills: PostgreSQL"]
  }
}
```

### Python API

```python
from backend.recruitment_pipeline import build_pipeline, run_pipeline

# Build the pipeline once
pipeline = build_pipeline()

# Run evaluation
result = await run_pipeline(
    pipeline,
    job_description="...",
    resume_text="...",
    interview_qa=[...]
)

# Access results
final_eval = result["final_evaluation"]
print(f"Recommendation: {final_eval['recommendation']}")
print(f"Score: {final_eval['overall_score']}%")
```

### Quick Evaluation

```python
from backend.recruitment_pipeline import quick_evaluate

# One-liner evaluation
result = await quick_evaluate(
    job_description="...",
    resume_text="...",
    interview_qa=[...]
)

print(result)  # Returns final_evaluation dict
```

## 🧪 Testing

Run the test script to see the pipeline in action:

```bash
cd backend
python test_pipeline.py
```

This will run a complete evaluation with sample data and display all intermediate results.

## 📊 Evaluation Criteria

### Resume Screening
- Technical skills match
- Experience level alignment
- Educational background
- Relevant projects and achievements
- Domain knowledge

### Interview Evaluation
- **Relevance to job** (40%): How well answers demonstrate required skills
- **Technical depth** (30%): Accuracy and expertise shown
- **Communication** (15%): Clarity and structure of responses
- **Examples** (15%): Use of specific examples and details

### Final Scoring
```
Overall Score = (Resume Score × 0.4) + (Interview Score × 0.6)

Recommendation Thresholds:
- 80-100: Strong Hire
- 65-79:  Hire
- 50-64:  Maybe
- 0-49:   No Hire
```

## 🔧 Configuration

### Environment Variables
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

### Customization

**Adjust scoring weights** in `score_aggregator.py`:
```python
# Current: Resume 40%, Interview 60%
overall_score = int((resume_score * 0.4) + (interview_score * 0.6))

# Example: Equal weight
overall_score = int((resume_score * 0.5) + (interview_score * 0.5))
```

**Modify recommendation thresholds** in `score_aggregator.py`:
```python
if overall_score >= 80:
    recommendation = "Strong Hire"
# ... adjust as needed
```

## 🏃 Running the Pipeline

### Option 1: FastAPI Endpoint
```bash
# Start the server
cd backend
uvicorn main:app --reload

# Call the endpoint
curl -X POST http://localhost:8000/evaluate-candidate \
  -H "Content-Type: application/json" \
  -d @sample_request.json
```

### Option 2: Python Script
```python
import asyncio
from recruitment_pipeline import build_pipeline, run_pipeline

async def main():
    pipeline = build_pipeline()
    result = await run_pipeline(
        pipeline,
        job_description="...",
        resume_text="...",
        interview_qa=[...]
    )
    print(result["final_evaluation"])

asyncio.run(main())
```

### Option 3: Direct Import
```python
# In your existing code
from backend.recruitment_pipeline import build_pipeline

pipeline = build_pipeline()
# Use pipeline in your application
```

## 📁 File Structure

```
backend/
├── recruitment_pipeline.py          # Main pipeline orchestration
├── langgraph_nodes/
│   ├── __init__.py
│   ├── jd_analyzer.py              # Job description analysis
│   ├── resume_screener.py          # Resume screening
│   ├── interview_evaluator.py      # Interview evaluation
│   └── score_aggregator.py         # Final scoring
├── test_pipeline.py                 # Test script
└── main.py                          # FastAPI endpoints
```

## 🔍 Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

Check pipeline status:
```bash
# Health check endpoint
curl http://localhost:8000/health

# Response:
{
  "status": "ok",
  "gemini": "available",
  "api_key_set": true
}
```

## 🚨 Error Handling

The pipeline includes robust fallbacks:
- If Gemini API fails, uses keyword matching for resume screening
- If interview data is missing, skips that evaluation step
- Each agent has try-catch error handling with detailed logging

## 🎯 Best Practices

1. **Always provide interview Q&A** for most accurate results
2. **Use detailed job descriptions** with clear requirements
3. **Include complete resumes** with skills, experience, and projects
4. **Review intermediate outputs** to understand the evaluation flow
5. **Adjust weights and thresholds** based on your hiring criteria

## 📝 Example Use Cases

### 1. Batch Candidate Processing
```python
candidates = [...]  # List of candidates
results = []

for candidate in candidates:
    result = await run_pipeline(
        pipeline,
        job_description=jd,
        resume_text=candidate["resume"],
        interview_qa=candidate.get("interview", [])
    )
    results.append(result["final_evaluation"])

# Sort by score
results.sort(key=lambda x: x["overall_score"], reverse=True)
```

### 2. Resume-Only Screening
```python
# Skip interview if not available
result = await run_pipeline(
    pipeline,
    job_description=jd,
    resume_text=resume,
    interview_qa=[]  # Empty list
)
```

### 3. Integration with Existing Systems
```python
# Your application
from recruitment_pipeline import build_pipeline

# Initialize once
recruitment_pipeline = build_pipeline()

# Use in your evaluation flow
def evaluate_applicant(applicant_data):
    result = await run_pipeline(
        recruitment_pipeline,
        **applicant_data
    )
    return result
```

## 🔗 Related Endpoints

- `POST /analyze-jd` - Standalone JD analysis
- `POST /screen-resume` - Standalone resume screening
- `POST /screen-resume-file` - Resume screening with file upload
- `POST /generate-interview` - Generate interview questions
- `POST /score-answer` - Score individual interview answers
- `POST /evaluate-candidate` - **Complete pipeline** (recommended)

---

**Built with:** LangGraph, LangChain, Google Gemini, FastAPI
