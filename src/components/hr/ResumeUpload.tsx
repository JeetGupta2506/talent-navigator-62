import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Upload, Users } from "lucide-react";
import { Input } from "@/components/ui/input";

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
      // Process each resume
      const candidates = [];
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const text = await file.text();
        
        const response = await fetch(
          `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/screen-resume`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY}`,
            },
            body: JSON.stringify({
              jobDescription,
              resume: text,
              candidateName: file.name.replace(/\.[^/.]+$/, ""),
            }),
          }
        );

        if (!response.ok) throw new Error(`Failed to screen ${file.name}`);

        const data = await response.json();
        candidates.push({ ...data, fileName: file.name });
      }

      onCandidatesUpdate(candidates);
      
      toast({
        title: "Screening Complete",
        description: `Processed ${candidates.length} candidate(s)`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to screen resumes",
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
          Upload candidate resumes for AI-powered screening
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="border-2 border-dashed border-muted rounded-lg p-8 text-center hover:border-primary transition-colors">
          <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <Input
            type="file"
            accept=".txt,.pdf,.doc,.docx"
            multiple
            onChange={handleFileChange}
            className="max-w-xs mx-auto"
          />
          <p className="text-sm text-muted-foreground mt-4">
            {selectedFiles 
              ? `${selectedFiles.length} file(s) selected`
              : "Support for .txt, .pdf, .doc, .docx files"}
          </p>
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
