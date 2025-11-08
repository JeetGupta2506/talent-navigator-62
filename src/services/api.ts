// API client for FastAPI backend

const BACKEND_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface JDAnalysisResponse {
  word_count: number;
  top_skills: string[];
  notes?: string;
}

interface InterviewQuestionsResponse {
  questions: string[];
}

interface ScoreResponse {
  score: number;
  feedback: string;
}

interface ScreenResult {
  pass_rate: number;
  highlights: string[];
}

export const analyzeJobDescription = async (
  description: string,
  jobTitle?: string
): Promise<JDAnalysisResponse> => {
  const response = await fetch(`${BACKEND_URL}/analyze-jd`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      description,
      job_title: jobTitle,
    }),
  });

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.statusText}`);
  }

  return response.json();
};

export const generateInterviewQuestions = async (
  jobTitle?: string,
  description?: string,
  numQuestions: number = 5
): Promise<InterviewQuestionsResponse> => {
  const response = await fetch(`${BACKEND_URL}/generate-interview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_title: jobTitle,
      description,
      num_questions: numQuestions,
    }),
  });

  if (!response.ok) {
    throw new Error(`Question generation failed: ${response.statusText}`);
  }

  return response.json();
};

export const scoreAnswer = async (
  answerText: string,
  questionId?: string,
  rubrics?: string[],
  jobDescription?: string,
  questionText?: string
): Promise<ScoreResponse> => {
  const response = await fetch(`${BACKEND_URL}/score-answer`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      answer_text: answerText,
      question_id: questionId,
      rubrics,
      job_description: jobDescription,
      question_text: questionText,
    }),
  });

  if (!response.ok) {
    throw new Error(`Answer scoring failed: ${response.statusText}`);
  }

  return response.json();
};

export const screenResume = async (
  resumeText: string,
  jobDescription?: string
): Promise<ScreenResult> => {
  const response = await fetch(`${BACKEND_URL}/screen-resume`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      resume_text: resumeText,
      job_description: jobDescription,
    }),
  });

  if (!response.ok) {
    throw new Error(`Resume screening failed: ${response.statusText}`);
  }

  return response.json();
};

export const uploadResumeFile = async (file: File, jobDescription?: string): Promise<ScreenResult> => {
  const form = new FormData();
  form.append("file", file);
  if (jobDescription) form.append("job_description", jobDescription);

  const response = await fetch(`${BACKEND_URL}/screen-resume-file`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    throw new Error(`Resume file screening failed: ${response.statusText}`);
  }

  return response.json();
};

export const checkHealth = async (): Promise<{ status: string; gemini?: string; api_key_set?: boolean }> => {
  const response = await fetch(`${BACKEND_URL}/health`);
  
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
};

// ============================================================================
// LangGraph Pipeline - Complete Candidate Evaluation
// ============================================================================

interface InterviewQA {
  question: string;
  answer: string;
}

interface JDAnalysisDetailed {
  role: string;
  required_skills: string[];
  tools: string[];
  minimum_experience: string;
  responsibilities: string[];
  education: string;
  employment_type: string;
}

interface ResumeEvaluation {
  skill_match: number;
  matched_skills: string[];
  missing_skills: string[];
  comment: string;
}

interface QuestionScore {
  question: string;
  score: number;
  feedback: string;
}

interface InterviewEvaluation {
  overall_score: number;
  question_scores: QuestionScore[];
  strengths: string[];
  concerns: string[];
}

interface FinalEvaluation {
  overall_score: number;
  resume_score: number;
  interview_score: number;
  recommendation: "Strong Hire" | "Hire" | "Maybe" | "No Hire";
  summary: string;
  key_strengths: string[];
  key_concerns: string[];
}

export interface PipelineResult {
  jd_analysis: JDAnalysisDetailed;
  resume_eval: ResumeEvaluation;
  interview_eval: InterviewEvaluation;
  final_evaluation: FinalEvaluation;
}

export const evaluateCandidate = async (
  jobDescription: string,
  resumeText: string,
  interviewQA?: InterviewQA[]
): Promise<PipelineResult> => {
  const response = await fetch(`${BACKEND_URL}/evaluate-candidate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description: jobDescription,
      resume_text: resumeText,
      interview_qa: interviewQA || [],
    }),
  });

  if (!response.ok) {
    throw new Error(`Candidate evaluation failed: ${response.statusText}`);
  }

  return response.json();
};

export const uploadEvaluateCandidateFile = async (file: File, jobDescription?: string, interviewQA?: InterviewQA[]): Promise<PipelineResult> => {
  const form = new FormData();
  form.append("file", file);
  if (jobDescription) form.append("job_description", jobDescription);
  if (interviewQA) form.append("interview_qa", JSON.stringify(interviewQA));

  const response = await fetch(`${BACKEND_URL}/evaluate-candidate-file`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    throw new Error(`Candidate file evaluation failed: ${response.statusText}`);
  }

  return response.json();
};
