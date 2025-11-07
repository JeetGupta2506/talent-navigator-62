import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

API_KEY = os.environ.get("GOOGLE_API_KEY")

_llm = None
_available = False

if API_KEY:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True
        )
        _available = True
        logger.info("LangChain Gemini client initialized successfully")
    except Exception as e:
        logger.warning("Failed to import/configure LangChain Gemini: %s", e)
        _available = False
else:
    logger.info("GOOGLE_API_KEY not set — Gemini client unavailable")


def available() -> bool:
    return _available and _llm is not None


class SkillExtraction(BaseModel):
    """Structured output for skill extraction from job descriptions."""
    skills: List[str] = Field(description="List of technical skills, tools, frameworks, or technologies mentioned")
    
    
async def analyze_jd(description: str, job_title: Optional[str] = None) -> dict:
    """Use LangChain + Gemini to extract top skills from job description."""
    from re import findall

    word_count = len(findall(r"\w+", description or ""))
    top_skills: List[str] = []
    notes = ""

    if not available():
        return {"word_count": word_count, "top_skills": top_skills, "notes": "gemini not configured"}

    try:
        # Use structured output with LangChain
        structured_llm = _llm.with_structured_output(SkillExtraction)
        
        prompt = f"""Analyze the following job description and extract all technical skills, programming languages, frameworks, tools, and technologies mentioned.

Job Title: {job_title or 'Not specified'}

Job Description:
{description}

Extract and list the key technical skills. Focus on concrete skills like programming languages (Python, Java), frameworks (React, Django), tools (Docker, Git), databases (PostgreSQL, MongoDB), cloud platforms (AWS, GCP), etc. Return up to 15 most important skills."""

        result = structured_llm.invoke(prompt)
        
        # Extract skills from structured output
        if hasattr(result, 'skills'):
            top_skills = result.skills[:15]
        else:
            top_skills = []
            
        notes = f"Extracted by Gemini via LangChain - found {len(top_skills)} skills"
        logger.info(f"Extracted skills: {top_skills}")
        
    except Exception as e:
        logger.exception("Gemini analyze_jd failed: %s", e)
        notes = f"gemini error: {e}"

    return {"word_count": word_count, "top_skills": top_skills, "notes": notes}


async def generate_interview(description: Optional[str], job_title: Optional[str], num_questions: int = 5) -> List[str]:
    """Generate interview questions using LangChain + Gemini."""
    if not available():
        # fallback simple deterministic questions
        title = job_title or description or "Candidate"
        base_questions = [
            f"Tell me about your experience related to {title}.",
            "Describe a challenging problem you solved recently.",
            "How do you prioritize tasks when working under pressure?",
            "Explain a project where you worked with a team — what was your role?",
            "How do you approach debugging and root-cause analysis?",
        ]
        n = max(1, min(20, num_questions))
        return (base_questions * ((n // len(base_questions)) + 1))[:n]

    try:
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert technical interviewer who creates targeted, insightful interview questions based on job requirements."),
            ("user", """Generate {num_questions} interview questions for the following role:

Job Title: {job_title}
Job Description: {description}

Create questions that:
1. Directly assess the SPECIFIC technical skills mentioned in the job description
2. Evaluate hands-on experience with the required tools and technologies
3. Explore real-world scenarios relevant to the role's responsibilities
4. Test problem-solving abilities in the context of this position
5. Assess depth of knowledge in the key areas mentioned

Make the questions:
- Specific and targeted to the actual requirements listed
- Technical enough to distinguish experienced candidates
- Open-ended to encourage detailed responses
- Based on real challenges they would face in this role

Return ONLY the questions, one per line, numbered. No explanations or extra text.""")
        ])
        
        chain = prompt | _llm
        response = chain.invoke({
            "num_questions": num_questions,
            "job_title": job_title or "Not specified",
            "description": description or "Not specified"
        })
        
        # Parse response to extract questions
        content = response.content if hasattr(response, 'content') else str(response)
        questions = []
        for line in content.split('\n'):
            line = line.strip()
            # Remove numbering like "1.", "1)", etc.
            import re
            cleaned = re.sub(r'^\d+[\.)]\s*', '', line)
            if cleaned and len(cleaned) > 10:  # Ensure it's a real question
                questions.append(cleaned)
        
        if not questions:
            # Fallback if parsing fails
            return await generate_interview(description, job_title, num_questions)
            
        logger.info(f"Generated {len(questions)} interview questions for {job_title or 'position'}")
        return questions[:num_questions]
        
    except Exception as e:
        logger.exception("Gemini generate_interview failed: %s", e)
        # Return fallback questions
        title = job_title or "the position"
        return [
            f"Tell me about your experience related to {title}.",
            "Describe a challenging problem you solved recently.",
            "How do you prioritize tasks when working under pressure?",
            "Explain a project where you worked with a team — what was your role?",
            "How do you approach debugging and root-cause analysis?",
        ][:num_questions]


async def score_answer(
    answer_text: str, 
    rubrics: Optional[List[str]] = None,
    job_description: Optional[str] = None,
    question_text: Optional[str] = None
) -> dict:
    """Score candidate answer using LangChain + Gemini, considering job description relevance."""
    # Fallback: simple length-based score if gemini unavailable
    if not available():
        length = len((answer_text or "").strip())
        score = min(100.0, (length / 500.0) * 100.0)
        feedback = "Answer is short." if length < 100 else "Answer length is reasonable."
        return {"score": round(score, 1), "feedback": feedback}

    try:
        from langchain_core.prompts import ChatPromptTemplate
        
        rubric_text = "\n".join(rubrics) if rubrics else "General quality, completeness, and relevance"
        
        # Build context-aware prompt
        context_parts = []
        if job_description:
            context_parts.append(f"Job Description:\n{job_description}\n")
        if question_text:
            context_parts.append(f"Interview Question:\n{question_text}\n")
        
        context = "\n".join(context_parts) if context_parts else "No additional context provided."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an experienced technical interviewer who evaluates candidate responses objectively based on job requirements."),
            ("user", """Evaluate the following candidate answer in the context of the job requirements.

{context}

Evaluation Criteria:
{rubrics}

Candidate Answer:
{answer}

Provide:
1. A score from 0-100 based on:
   - Relevance to the job description and required skills (40%)
   - Technical depth and accuracy (30%)
   - Communication clarity (15%)
   - Examples and specificity (15%)
2. Brief constructive feedback (2-3 sentences) highlighting strengths and areas for improvement

Format your response exactly as:
SCORE: <number>
FEEDBACK: <feedback text>""")
        ])
        
        chain = prompt | _llm
        response = chain.invoke({
            "context": context,
            "rubrics": rubric_text,
            "answer": answer_text
        })
        
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse score and feedback
        score = 0.0
        feedback = ""
        for line in content.split('\n'):
            line = line.strip()
            if line.upper().startswith("SCORE:"):
                try:
                    score_text = line.split(":", 1)[1].strip()
                    # Extract just the number
                    import re
                    match = re.search(r'\d+(\.\d+)?', score_text)
                    if match:
                        score = float(match.group())
                except Exception as e:
                    logger.warning(f"Failed to parse score: {e}")
            elif line.upper().startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
        
        if not feedback:
            feedback = "Evaluation completed."
            
        return {"score": round(min(100.0, max(0.0, score)), 1), "feedback": feedback}
        
    except Exception as e:
        logger.exception("Gemini score_answer failed: %s", e)
        return {"score": 0.0, "feedback": f"Error scoring answer: {str(e)}"}


async def screen_resume(resume_text: str, job_description: Optional[str] = None) -> dict:
    """Screen resume using LangChain + Gemini with structured output."""
    # fallback simple screening
    if not available():
        logger.warning("Gemini not available - using keyword fallback for resume screening")
        from re import findall

        jd_words = set(w.lower() for w in findall(r"\w+", job_description or ""))
        resume_words = set(w.lower() for w in findall(r"\w+", resume_text or ""))
        if jd_words:
            matches = len(jd_words & resume_words)
            pass_rate = matches / len(jd_words)
        else:
            pass_rate = 0.0
        highlights = list((jd_words & resume_words))[:10]
        logger.info(f"Fallback screening - Pass rate: {pass_rate}, {len(highlights)} keywords matched")
        return {"pass_rate": round(pass_rate, 3), "highlights": highlights}

    try:
        from langchain_core.prompts import ChatPromptTemplate
        
        logger.info(f"Using Gemini to screen resume (JD length: {len(job_description or '')}, Resume length: {len(resume_text)})")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert HR analyst with deep experience in technical recruiting and resume evaluation."),
            ("user", """Analyze how well this candidate's resume matches the job requirements. Evaluate based on:
1. Required technical skills and technologies
2. Years of experience and seniority level
3. Educational background and certifications
4. Relevant projects and achievements
5. Domain knowledge and industry experience

Job Description:
{job_description}

Resume:
{resume}

Provide a detailed assessment:
1. A match score from 0.0 to 1.0 where:
   - 0.9-1.0: Excellent match, highly qualified candidate
   - 0.7-0.89: Strong match, qualified candidate
   - 0.5-0.69: Moderate match, some gaps
   - 0.3-0.49: Weak match, significant gaps
   - 0.0-0.29: Poor match, not qualified
2. List the key skills/qualifications that match (up to 10 most important)

Be generous but fair - if a candidate has most required skills and relevant experience, they should score 0.7+.
Consider related skills and transferable experience positively.

Format your response exactly as:
MATCH_SCORE: <decimal between 0.0 and 1.0>
MATCHED_SKILLS: <comma-separated list of matched skills/qualifications>""")
        ])
        
        chain = prompt | _llm
        response = chain.invoke({
            "job_description": job_description or "Not specified",
            "resume": resume_text
        })
        
        content = response.content if hasattr(response, 'content') else str(response)
        
        logger.info(f"Gemini response for screening: {content[:200]}...")
        
        # Parse response
        pass_rate = 0.0
        highlights = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.upper().startswith("MATCH_SCORE:") or line.upper().startswith("PASS_RATE:"):
                try:
                    rate_text = line.split(":", 1)[1].strip()
                    import re
                    match = re.search(r'0?\.\d+|\d+\.?\d*', rate_text)
                    if match:
                        pass_rate = float(match.group())
                        pass_rate = min(1.0, max(0.0, pass_rate))
                except Exception as e:
                    logger.warning(f"Failed to parse pass_rate: {e}")
            elif line.upper().startswith("MATCHED_SKILLS:") or line.upper().startswith("HIGHLIGHTS:"):
                try:
                    highlights_text = line.split(":", 1)[1].strip()
                    highlights = [h.strip() for h in highlights_text.split(",") if h.strip()]
                    highlights = highlights[:10]
                except Exception as e:
                    logger.warning(f"Failed to parse highlights: {e}")
        
        logger.info(f"Resume screening - Pass rate: {pass_rate}, Highlights: {highlights}")
        return {"pass_rate": round(pass_rate, 3), "highlights": highlights}
        
    except Exception as e:
        logger.exception("Gemini screen_resume failed: %s", e)
        # Fallback to simple keyword matching
        from re import findall
        jd_words = set(w.lower() for w in findall(r"\w+", job_description or ""))
        resume_words = set(w.lower() for w in findall(r"\w+", resume_text or ""))
        if jd_words:
            matches = len(jd_words & resume_words)
            pass_rate = matches / len(jd_words)
        else:
            pass_rate = 0.0
        highlights = list((jd_words & resume_words))[:10]
        return {"pass_rate": round(pass_rate, 3), "highlights": highlights}


def resume_screener(state: dict) -> dict:
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
    print("🔍 Resume Screener agent starting...")
    
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
        print("⚠️ Resume Screener: No resume text provided.")
        return default_response
    
    if not jd_analysis:
        print("⚠️ Resume Screener: No JD analysis provided.")
        return default_response
    
    # Check if Gemini is available
    if not available():
        print("⚠️ Resume Screener: Gemini not configured, using fallback.")
        # Simple keyword matching fallback
        import re
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
    
    try:
        from langchain_core.messages import HumanMessage
        import json
        import re
        
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

        # Call the LLM using HumanMessage
        print("📤 Calling Gemini for resume screening...")
        response = _llm.invoke([HumanMessage(content=prompt)])
        
        # Extract content
        response_text = response.content if hasattr(response, 'content') else str(response)
        print(f"📥 Gemini response received: {response_text[:200]}...")
        
        # Try to parse as JSON
        try:
            # Clean up potential markdown code blocks
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            parsed = json.loads(cleaned)
            
            # Validate and normalize the structure
            resume_eval = {
                "skill_match": int(parsed.get("skill_match", 0)),
                "matched_skills": parsed.get("matched_skills", []),
                "missing_skills": parsed.get("missing_skills", []),
                "comment": parsed.get("comment", "No comment provided.")
            }
            
            # Ensure skill_match is in valid range
            resume_eval["skill_match"] = max(0, min(100, resume_eval["skill_match"]))
            
            print(f"✅ Resume Screener ran successfully. Match: {resume_eval['skill_match']}%")
            
            return {"resume_eval": resume_eval}
            
        except json.JSONDecodeError as je:
            print(f"⚠️ JSON parsing failed: {je}")
            
            # Regex fallback to extract fields
            skill_match = 0
            matched_skills = []
            missing_skills = []
            comment = ""
            
            # Try to extract skill_match
            match_pattern = re.search(r'"skill_match"\s*:\s*(\d+)', response_text)
            if match_pattern:
                skill_match = int(match_pattern.group(1))
            
            # Try to extract matched_skills array
            matched_pattern = re.search(r'"matched_skills"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
            if matched_pattern:
                matched_str = matched_pattern.group(1)
                matched_skills = [s.strip(' "\'') for s in matched_str.split(',') if s.strip()]
            
            # Try to extract missing_skills array
            missing_pattern = re.search(r'"missing_skills"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
            if missing_pattern:
                missing_str = missing_pattern.group(1)
                missing_skills = [s.strip(' "\'') for s in missing_str.split(',') if s.strip()]
            
            # Try to extract comment
            comment_pattern = re.search(r'"comment"\s*:\s*"([^"]*)"', response_text)
            if comment_pattern:
                comment = comment_pattern.group(1)
            
            if not comment:
                comment = "Parsed with fallback regex."
            
            print(f"✅ Resume Screener completed with regex fallback. Match: {skill_match}%")
            
            return {
                "resume_eval": {
                    "skill_match": max(0, min(100, skill_match)),
                    "matched_skills": matched_skills,
                    "missing_skills": missing_skills,
                    "comment": comment
                }
            }
    
    except Exception as e:
        logger.exception("Resume Screener failed: %s", e)
        print(f"❌ Resume Screener error: {e}")
        return {
            "resume_eval": {
                "skill_match": 0,
                "matched_skills": [],
                "missing_skills": [],
                "comment": f"Error during screening: {str(e)}"
            }
        }
