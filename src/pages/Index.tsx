import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { FileText, Users, MessageSquare } from "lucide-react";
import JobDescriptionUpload from "@/components/hr/JobDescriptionUpload";
import ResumeUpload from "@/components/hr/ResumeUpload";
import CandidateList from "@/components/hr/CandidateList";
import InterviewInterface from "@/components/hr/InterviewInterface";
import CompletePipeline from "@/components/hr/CompletePipeline";

const Index = () => {
  const [activeTab, setActiveTab] = useState("upload");
  const [jobDescription, setJobDescription] = useState<string>("");
  const [candidates, setCandidates] = useState<any[]>([]);

  const handleCandidateUpdate = (candidateName: string, interviewData: any) => {
    setCandidates(prevCandidates => 
      prevCandidates.map(candidate => 
        candidate.candidateName === candidateName
          ? { ...candidate, ...interviewData }
          : candidate
      )
    );
    
    // Automatically switch to candidates tab to show results
    setActiveTab("candidates");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">AI Recruitment Assistant</h1>
              <p className="text-muted-foreground mt-1">Multi-Agent HR Intelligence System</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-sm text-muted-foreground">AI Agents Active</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[450px]">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">Upload</span>
            </TabsTrigger>
            <TabsTrigger value="interview" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              <span className="hidden sm:inline">Interview</span>
            </TabsTrigger>
            <TabsTrigger value="candidates" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              <span className="hidden sm:inline">Candidates</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <JobDescriptionUpload onJobDescriptionSubmit={setJobDescription} />
              <ResumeUpload 
                jobDescription={jobDescription} 
                onCandidatesUpdate={setCandidates}
              />
            </div>
          </TabsContent>

          <TabsContent value="interview">
            <InterviewInterface 
              candidates={candidates} 
              jobDescription={jobDescription}
              onCandidateUpdate={handleCandidateUpdate}
            />
          </TabsContent>

          <TabsContent value="candidates">
            <CandidateList candidates={candidates} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Index;
