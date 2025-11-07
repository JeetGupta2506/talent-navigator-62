import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Sparkles, CheckCircle2, AlertCircle, TrendingUp, TrendingDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { evaluateCandidate, PipelineResult } from "@/services/api";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

interface CompletePipelineProps {
  jobDescription: string;
  candidates: any[];
}

const CompletePipeline = ({ jobDescription, candidates }: CompletePipelineProps) => {
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<string>("");
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const { toast } = useToast();

  const handleEvaluate = async () => {
    if (!selectedCandidate || !jobDescription) {
      toast({
        title: "Missing Information",
        description: "Please select a candidate and ensure a job description is analyzed.",
        variant: "destructive",
      });
      return;
    }

    const candidate = candidates.find(c => c.candidateName === selectedCandidate);
    if (!candidate) return;

    setIsEvaluating(true);

    try {
      // Get resume text (you may need to store this in candidate data)
      // For now, we'll create a summary from available data
      const resumeText = `
Candidate: ${candidate.candidateName}
Skills: ${candidate.matchedSkills.join(", ")}
Match Score: ${candidate.matchScore}%
${candidate.summary || ""}
      `.trim();

      // Get interview Q&A if available (you'd need to store these)
      const interviewQA = candidate.interview_qa || [];

      // Call the pipeline
      const result = await evaluateCandidate(
        jobDescription,
        resumeText,
        interviewQA
      );

      setPipelineResult(result);

      toast({
        title: "Evaluation Complete! 🎉",
        description: `Recommendation: ${result.final_evaluation.recommendation}`,
      });
    } catch (error) {
      console.error("Pipeline evaluation error:", error);
      toast({
        title: "Evaluation Failed",
        description: "Could not complete the pipeline evaluation. Check backend logs.",
        variant: "destructive",
      });
    } finally {
      setIsEvaluating(false);
    }
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case "Strong Hire": return "bg-green-500";
      case "Hire": return "bg-blue-500";
      case "Maybe": return "bg-yellow-500";
      case "No Hire": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 65) return "text-blue-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            <CardTitle>AI Pipeline Evaluation</CardTitle>
          </div>
          <CardDescription>
            Complete multi-agent evaluation using LangGraph
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <select
              value={selectedCandidate}
              onChange={(e) => setSelectedCandidate(e.target.value)}
              className="flex-1 px-3 py-2 border rounded-md"
              disabled={candidates.length === 0}
            >
              <option value="">Select a candidate...</option>
              {candidates.map((candidate, index) => (
                <option key={index} value={candidate.candidateName}>
                  {candidate.candidateName} ({candidate.matchScore}%)
                </option>
              ))}
            </select>

            <Button
              onClick={handleEvaluate}
              disabled={isEvaluating || !selectedCandidate || !jobDescription}
            >
              {isEvaluating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Run Pipeline
                </>
              )}
            </Button>
          </div>

          {!jobDescription && (
            <p className="text-sm text-warning">
              ⚠️ Please analyze a job description first
            </p>
          )}
        </CardContent>
      </Card>

      {pipelineResult && (
        <div className="space-y-6">
          {/* Final Recommendation */}
          <Card className="border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-white">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Final Recommendation</span>
                <Badge className={`${getRecommendationColor(pipelineResult.final_evaluation.recommendation)} text-white text-lg px-4 py-2`}>
                  {pipelineResult.final_evaluation.recommendation}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center space-y-2">
                <div className={`text-6xl font-bold ${getScoreColor(pipelineResult.final_evaluation.overall_score)}`}>
                  {pipelineResult.final_evaluation.overall_score}%
                </div>
                <p className="text-sm text-muted-foreground">Overall Score</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">
                    {pipelineResult.final_evaluation.resume_score}%
                  </div>
                  <p className="text-sm text-muted-foreground">Resume Match</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600">
                    {pipelineResult.final_evaluation.interview_score}%
                  </div>
                  <p className="text-sm text-muted-foreground">Interview Score</p>
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">Summary</h4>
                <p className="text-sm text-muted-foreground">
                  {pipelineResult.final_evaluation.summary}
                </p>
              </div>

              {pipelineResult.final_evaluation.key_strengths.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                    Key Strengths
                  </h4>
                  <ul className="space-y-1">
                    {pipelineResult.final_evaluation.key_strengths.map((strength, i) => (
                      <li key={i} className="text-sm flex items-start gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5" />
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {pipelineResult.final_evaluation.key_concerns.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <TrendingDown className="h-4 w-4 text-yellow-500" />
                    Key Concerns
                  </h4>
                  <ul className="space-y-1">
                    {pipelineResult.final_evaluation.key_concerns.map((concern, i) => (
                      <li key={i} className="text-sm flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5" />
                        <span>{concern}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Resume Evaluation Details */}
          <Card>
            <CardHeader>
              <CardTitle>Resume Evaluation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Skill Match</span>
                  <span className="text-sm font-bold">{pipelineResult.resume_eval.skill_match}%</span>
                </div>
                <Progress value={pipelineResult.resume_eval.skill_match} />
              </div>

              {pipelineResult.resume_eval.matched_skills.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Matched Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {pipelineResult.resume_eval.matched_skills.map((skill, i) => (
                      <Badge key={i} variant="default" className="bg-green-100 text-green-800">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {pipelineResult.resume_eval.missing_skills.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Missing Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {pipelineResult.resume_eval.missing_skills.map((skill, i) => (
                      <Badge key={i} variant="outline" className="border-red-200 text-red-600">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <p className="text-sm text-muted-foreground italic">
                {pipelineResult.resume_eval.comment}
              </p>
            </CardContent>
          </Card>

          {/* Interview Evaluation Details */}
          {pipelineResult.interview_eval.question_scores.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Interview Evaluation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-sm font-medium">Overall Interview Score</span>
                    <span className="text-sm font-bold">{pipelineResult.interview_eval.overall_score}%</span>
                  </div>
                  <Progress value={pipelineResult.interview_eval.overall_score} />
                </div>

                <Separator />

                <div className="space-y-3">
                  {pipelineResult.interview_eval.question_scores.map((qs, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg space-y-2">
                      <div className="flex justify-between items-start">
                        <p className="text-sm font-medium">Q{i + 1}: {qs.question}</p>
                        <Badge variant={qs.score >= 70 ? "default" : "secondary"}>
                          {qs.score}/100
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{qs.feedback}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* JD Analysis Details */}
          <Card>
            <CardHeader>
              <CardTitle>Job Requirements Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <span className="text-sm font-medium">Role: </span>
                <span className="text-sm">{pipelineResult.jd_analysis.role}</span>
              </div>
              {pipelineResult.jd_analysis.required_skills.length > 0 && (
                <div>
                  <span className="text-sm font-medium">Required Skills: </span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {pipelineResult.jd_analysis.required_skills.map((skill, i) => (
                      <Badge key={i} variant="outline">{skill}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {pipelineResult.jd_analysis.minimum_experience && (
                <div>
                  <span className="text-sm font-medium">Experience: </span>
                  <span className="text-sm">{pipelineResult.jd_analysis.minimum_experience}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default CompletePipeline;
