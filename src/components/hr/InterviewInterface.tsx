import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Loader2, MessageSquare, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface InterviewInterfaceProps {
  candidates: any[];
}

const InterviewInterface = ({ candidates }: InterviewInterfaceProps) => {
  const [selectedCandidate, setSelectedCandidate] = useState<string>("");
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isScoring, setIsScoring] = useState(false);
  const { toast } = useToast();

  const handleGenerateQuestions = async () => {
    if (!selectedCandidate) {
      toast({
        title: "Error",
        description: "Please select a candidate",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/generate-interview`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY}`,
          },
          body: JSON.stringify({ candidateName: selectedCandidate }),
        }
      );

      if (!response.ok) throw new Error("Failed to generate questions");

      const data = await response.json();
      setQuestions(data.questions || []);
      
      toast({
        title: "Questions Generated",
        description: `Generated ${data.questions?.length || 0} interview questions`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate interview questions",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmitAnswer = async (questionIndex: number) => {
    if (!currentAnswer.trim()) {
      toast({
        title: "Error",
        description: "Please provide an answer",
        variant: "destructive",
      });
      return;
    }

    setIsScoring(true);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/score-answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY}`,
          },
          body: JSON.stringify({
            question: questions[questionIndex].question,
            answer: currentAnswer,
          }),
        }
      );

      if (!response.ok) throw new Error("Failed to score answer");

      const data = await response.json();
      
      const updatedQuestions = [...questions];
      updatedQuestions[questionIndex] = {
        ...updatedQuestions[questionIndex],
        answer: currentAnswer,
        score: data.score,
        feedback: data.feedback,
      };
      
      setQuestions(updatedQuestions);
      setCurrentAnswer("");
      
      toast({
        title: "Answer Scored",
        description: `Score: ${data.score}/10`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to score answer",
        variant: "destructive",
      });
    } finally {
      setIsScoring(false);
    }
  };

  if (candidates.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">No candidates available for interview</p>
          <p className="text-sm text-muted-foreground mt-2">
            Screen candidates first in the Upload tab
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            <CardTitle>AI Interview Bot</CardTitle>
          </div>
          <CardDescription>
            Generate and conduct AI-powered interviews
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Select value={selectedCandidate} onValueChange={setSelectedCandidate}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Select a candidate" />
              </SelectTrigger>
              <SelectContent>
                {candidates.map((candidate, index) => (
                  <SelectItem key={index} value={candidate.candidateName}>
                    {candidate.candidateName} ({candidate.matchScore}%)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              onClick={handleGenerateQuestions}
              disabled={isGenerating || !selectedCandidate}
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate Questions"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {questions.length > 0 && (
        <div className="space-y-4">
          {questions.map((q, index) => (
            <Card key={index}>
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-start justify-between">
                  <h3 className="font-semibold">Question {index + 1}</h3>
                  {q.score && (
                    <Badge variant={q.score >= 7 ? "default" : q.score >= 5 ? "secondary" : "destructive"}>
                      {q.score}/10
                    </Badge>
                  )}
                </div>
                
                <p className="text-muted-foreground">{q.question}</p>

                {!q.answer ? (
                  <div className="space-y-2">
                    <Textarea
                      placeholder="Candidate's answer..."
                      value={currentAnswer}
                      onChange={(e) => setCurrentAnswer(e.target.value)}
                      className="min-h-[100px]"
                    />
                    <Button
                      onClick={() => handleSubmitAnswer(index)}
                      disabled={isScoring}
                      size="sm"
                    >
                      {isScoring ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Scoring...
                        </>
                      ) : (
                        <>
                          <Send className="mr-2 h-4 w-4" />
                          Submit Answer
                        </>
                      )}
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2 border-t pt-4">
                    <div>
                      <h4 className="text-sm font-medium mb-1">Answer:</h4>
                      <p className="text-sm text-muted-foreground">{q.answer}</p>
                    </div>
                    {q.feedback && (
                      <div>
                        <h4 className="text-sm font-medium mb-1">AI Feedback:</h4>
                        <p className="text-sm text-muted-foreground">{q.feedback}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default InterviewInterface;
