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
              Supports multiple .txt, .pdf, .doc, or .docx files
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
