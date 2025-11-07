import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Loader2, CheckCircle, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { analyzeJobDescription } from "@/services/api";

interface JobDescriptionUploadProps {
  onJobDescriptionSubmit: (jd: string) => void;
}

const JobDescriptionUpload = ({ onJobDescriptionSubmit }: JobDescriptionUploadProps) => {
  const [jobDescription, setJobDescription] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const { toast } = useToast();

  const handleAnalyze = async () => {
    if (!jobDescription.trim()) {
      toast({
        title: "Error",
        description: "Please enter a job description",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    
    try {
      const data = await analyzeJobDescription(jobDescription);
      setExtractedSkills(data.top_skills || []);
      onJobDescriptionSubmit(jobDescription);
      
      toast({
        title: "Analysis Complete",
        description: `Extracted ${data.top_skills?.length || 0} key skills (${data.word_count} words)`,
      });
    } catch (error) {
      console.error("Analysis error:", error);
      toast({
        title: "Error",
        description: "Failed to analyze job description. Make sure the backend is running.",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <Card className="shadow-lg border-primary/20">
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <CardTitle>Job Description Analyzer</CardTitle>
        </div>
        <CardDescription>
          Upload or paste a job description to extract key requirements
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          placeholder="Paste job description here..."
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          className="min-h-[200px] font-mono text-sm"
        />
        
        <Button 
          onClick={handleAnalyze} 
          disabled={isAnalyzing || !jobDescription.trim()}
          className="w-full"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <CheckCircle className="mr-2 h-4 w-4" />
              Analyze Job Description
            </>
          )}
        </Button>

        {extractedSkills.length > 0 && (
          <div className="space-y-2 pt-4 border-t">
            <h4 className="text-sm font-semibold">Extracted Skills:</h4>
            <div className="flex flex-wrap gap-2">
              {extractedSkills.map((skill, index) => (
                <Badge key={index} variant="secondary">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default JobDescriptionUpload;
