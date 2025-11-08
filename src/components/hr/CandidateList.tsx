import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";

interface CandidateListProps {
  candidates: any[];
}

const CandidateList = ({ candidates }: CandidateListProps) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-success";
    if (score >= 60) return "text-warning";
    return "text-destructive";
  };

  const getScoreIcon = (score: number) => {
    if (score >= 80) return <CheckCircle2 className="h-5 w-5 text-success" />;
    if (score >= 60) return <AlertCircle className="h-5 w-5 text-warning" />;
    return <XCircle className="h-5 w-5 text-destructive" />;
  };

  if (candidates.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">No candidates screened yet</p>
          <p className="text-sm text-muted-foreground mt-2">
            Upload resumes in the Upload tab to get started
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Candidate Screening Results</CardTitle>
        </CardHeader>
      </Card>

      {candidates.map((candidate, index) => (
        <Card key={index} className="hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-4">
              <div className="space-y-1">
                <h3 className="text-lg font-semibold">{candidate.candidateName}</h3>
                <p className="text-sm text-muted-foreground">{candidate.fileName}</p>
                {candidate.interviewCompleted && (
                  <Badge variant="secondary" className="mt-1">
                    Interview Completed ✓
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                {candidate.interviewCompleted ? (
                  <>
                    {getScoreIcon(candidate.finalScore)}
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getScoreColor(candidate.finalScore)}`}>
                        {candidate.finalScore}%
                      </p>
                      <p className="text-xs text-muted-foreground">Final Score</p>
                    </div>
                  </>
                ) : (
                  <>
                    {getScoreIcon(candidate.matchScore)}
                    <span className={`text-2xl font-bold ${getScoreColor(candidate.matchScore)}`}>
                      {candidate.matchScore}%
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="space-y-4">
              {/* Show final evaluation if interview completed */}
              {candidate.interviewCompleted && (
                <div className="bg-muted/50 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-base">Final Evaluation</h4>
                    <Badge 
                      variant={
                        candidate.recommendation === "Strong Hire" || candidate.recommendation === "Hire" 
                          ? "default" 
                          : candidate.recommendation === "Maybe" 
                          ? "secondary" 
                          : "destructive"
                      }
                      className="text-sm"
                    >
                      {candidate.recommendation}
                    </Badge>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div className="bg-background rounded p-2">
                      <p className="text-muted-foreground text-xs">Resume Match</p>
                      <p className="font-semibold">{candidate.matchScore}% (50%)</p>
                    </div>
                    <div className="bg-background rounded p-2">
                      <p className="text-muted-foreground text-xs">Interview Score</p>
                      <p className="font-semibold">{candidate.interviewScore}% (50%)</p>
                    </div>
                    <div className="bg-background rounded p-2">
                      <p className="text-muted-foreground text-xs">Combined</p>
                      <p className={`font-bold ${getScoreColor(candidate.finalScore)}`}>
                        {candidate.finalScore}%
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Resume match score (shown when no interview yet) */}
              {!candidate.interviewCompleted && (
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-muted-foreground">Resume Match Score</span>
                    <span className={`font-medium ${getScoreColor(candidate.matchScore)}`}>
                      {candidate.matchScore}%
                    </span>
                  </div>
                  <Progress value={candidate.matchScore} className="h-2" />
                </div>
              )}

              {candidate.matchedSkills && candidate.matchedSkills.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Matched Skills:</h4>
                  <div className="flex flex-wrap gap-2">
                    {candidate.matchedSkills.map((skill: string, idx: number) => (
                      <Badge key={idx} variant="default" className="bg-success">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {candidate.missingSkills && candidate.missingSkills.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Missing Skills:</h4>
                  <div className="flex flex-wrap gap-2">
                    {candidate.missingSkills.map((skill: string, idx: number) => (
                      <Badge key={idx} variant="outline" className="border-destructive text-destructive">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {candidate.summary && (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium mb-2">AI Summary:</h4>
                  <p className="text-sm text-muted-foreground">{candidate.summary}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default CandidateList;
