# 🧠 Recruitment Assistant - Multi-Agent HR Evaluation System (LangGraph + GenAI)
🚀 An intelligent AI-powered HR Assistant that analyzes job descriptions, screens resumes, evaluates interview answers, and provides final hiring recommendations — all powered by LangGraph, Gemini LLM, and FastAPI.

## 📋 Overview

Talent Navigator AI is a multi-agent HR automation system that simulates how a hiring team works — using multiple cooperating AI agents:

- **1.🧾 JD Analyzer** - Extracts key skills, tools, and experience from a job description
- **2.👤 Resume Screener** - Matches a candidate’s resume against the JD
- **3.🎤 Interview Evaluator** - Scores the candidate’s answers based on clarity, confidence, and accuracy
- **4.⭐ Score Aggregator** - Combines all evaluations and gives a final Hire / Maybe / Reject decision

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
- **Purpose**: Combines all evaluations into final hiring recommendation using LLM-generated summary
- **Scoring Weights**:
  - Resume: 50%
  - Interview: 50%
- **Output** (`final_report`):
  - Overall score (0-100, float)
  - Recommendation: "Hire" | "Maybe" | "Reject"
  - HR-style summary paragraph (AI-generated, context-aware)
- **Features**:
  - Uses Gemini LLM to generate professional evaluation summaries
  - Analyzes strengths and concerns from all agents
  - Provides actionable hiring recommendations
  - JSON parsing with regex fallback for reliability

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
Overall Score = (Resume Score × 0.5) + (Interview Score × 0.5)

Recommendation Thresholds:
- 80-100: Strong Hire
- 65-79:  Hire
- 50-64:  Maybe
- 0-49:   No Hire
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


