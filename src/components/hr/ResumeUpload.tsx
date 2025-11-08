import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Upload, Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { screenResume, uploadResumeFile, uploadEvaluateCandidateFile, evaluateCandidate } from "@/services/api";

interface ResumeUploadProps {
  jobDescription: string;
  onCandidatesUpdate: (candidates: any[]) => void;
}

const ResumeUpload = ({ jobDescription, onCandidatesUpdate }: ResumeUploadProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFiles(e.target.files);
  };

  const handleScreenResumes = async () => {
    if (!jobDescription) {
      toast({
        title: "Error",
        description: "Please analyze a job description first",
        variant: "destructive",
      });
      return;
    }

    if (!selectedFiles || selectedFiles.length === 0) {
      toast({
        title: "Error",
        description: "Please select resume files",
        variant: "destructive",
      });
      return;
    }

    setIsProcessing(true);

    try {
      const candidates = [];
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        let res;
        if (file.type === "application/pdf") {
          // If a file (PDF) is uploaded, run the full pipeline on the server (LangGraph)
          const pipelineRes = await uploadEvaluateCandidateFile(file, jobDescription);

          const finalEval: any = pipelineRes.final_evaluation || {};
          const resumeEval: any = pipelineRes.resume_eval || { matched_skills: [], missing_skills: [], skill_match: 0 };

          const matchScore = Math.round(finalEval.overall_score || resumeEval.skill_match || 0);
          candidates.push({
            candidateName: file.name.replace(/\.[^/.]+$/, ""),
            fileName: file.name,
            matchScore,
            matchedSkills: resumeEval.matched_skills || [],
            missingSkills: resumeEval.missing_skills || [],
            summary: finalEval.summary || resumeEval.comment || "",
          });
        } else {
          // Fallback: send raw text to the complete pipeline (text path)
          const text = await file.text();
          const pipelineRes = await evaluateCandidate(jobDescription, text);

          const finalEval: any = pipelineRes.final_evaluation || {};
          const resumeEval: any = pipelineRes.resume_eval || { matched_skills: [], missing_skills: [], skill_match: 0 };
          const matchScore = Math.round(finalEval.overall_score || resumeEval.skill_match || 0);

          candidates.push({
            candidateName: file.name.replace(/\.[^/.]+$/, ""),
            fileName: file.name,
            matchScore,
            matchedSkills: resumeEval.matched_skills || [],
            missingSkills: resumeEval.missing_skills || [],
            summary: finalEval.summary || resumeEval.comment || "",
          });
        }
      }

      onCandidatesUpdate(candidates);
            
      toast({
        title: "Screening Complete",
        description: `Processed ${candidates.length} candidate(s)`,
      });
    } catch (error) {
      console.error("Screening error:", error);
      toast({
        title: "Error",
        description: "Failed to screen resumes. Make sure the backend is running.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <Card className="shadow-lg border-success/20">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-success" />
          <CardTitle>Resume Screener</CardTitle>
        </div>
        <CardDescription>
          Upload candidate resumes
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div 
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors relative ${
            !jobDescription 
              ? 'border-muted/50 bg-muted/5 cursor-not-allowed' 
              : 'border-muted hover:border-primary'
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            e.stopPropagation();
            e.currentTarget.classList.add('border-primary');
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            e.stopPropagation();
            e.currentTarget.classList.remove('border-primary');
          }}
          onDrop={(e) => {
            e.preventDefault();
            e.stopPropagation();
            e.currentTarget.classList.remove('border-primary');
            const files = e.dataTransfer.files;
            if (files?.length) {
              setSelectedFiles(files);
            }
          }}
        >
          <Input
            type="file"
            id="resume-upload"
            accept=".txt,.pdf,.doc,.docx"
            multiple
            onChange={handleFileChange}
            className="hidden"
            disabled={!jobDescription}
          />
          
          <div className="space-y-4">
            <Upload className={`h-12 w-12 mx-auto ${!jobDescription ? 'text-muted-foreground/50' : 'text-muted-foreground'}`} />
            
            <div className="space-y-2">
              {!jobDescription ? (
                <div className="space-y-3">
                  <Button
                    variant="outline"
                    disabled
                    className="opacity-50 cursor-not-allowed"
                  >
                    Choose Files
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => document.getElementById('resume-upload')?.click()}
                >
                  Choose Files
                </Button>
              )}
              
              <p className="text-sm font-medium">
                {selectedFiles 
                  ? `${selectedFiles.length} ${selectedFiles.length === 1 ? 'resume' : 'resumes'} selected` 
                  : jobDescription 
                    ? 'Drag & drop files here or click Choose Files'
                    : ''}
              </p>
              
              {selectedFiles && selectedFiles.length > 0 && (
                <ul className="text-sm text-muted-foreground space-y-1 max-h-32 overflow-y-auto mx-auto max-w-md">
                  {Array.from(selectedFiles).map((file, i) => (
                    <li key={i} className="truncate">{file.name}</li>
                  ))}
                </ul>
              )}
            </div>
            
            <p className="text-xs text-muted-foreground">
              Supports .pdf files
            </p>
          </div>
        </div>

        <Button
          onClick={handleScreenResumes}
          disabled={isProcessing || !jobDescription || !selectedFiles}
          className="w-full"
          variant="default"
        >
          {isProcessing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing Resumes...
            </>
          ) : (
            <>
              <Users className="mr-2 h-4 w-4" />
              Screen Candidates
            </>
          )}
        </Button>

        {!jobDescription && (
          <p className="text-sm text-warning text-center">
            ⚠️ Please analyze a job description first
          </p>
        )}
      </CardContent>
    </Card>
  );
};

export default ResumeUpload;
