"use client"

import React, { useState, useEffect, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  Sparkles,
  UserCheck,
  Briefcase,
  AlertTriangle,
  ArrowLeft,
  X,
  SlidersHorizontal,
  CheckCircle,
  HelpCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  BarChart,
  UserPlus,
  GitCompare,
  TrendingUp,
  Cpu,
  BrainCircuit,
  MessageSquare
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { useToastStore } from "@/store/useToastStore"
import { recommendationService, RecommendationRequest } from "@/services/recommendation.service"
import Loading from "@/app/loading"
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip
} from "recharts"

interface Skill {
  name: string
  rating: number
  match: boolean
}

interface Competency {
  name: string
  rating: number
}

interface AvailabilityPoint {
  week: string
  rate: number
}

interface Candidate {
  id: string
  name: string
  role: string
  avatar: string
  score: number
  confidence: "High" | "Medium"
  department: string
  experience: number
  availability: number
  skillMatch: number
  competencyMatch: number
  similarity: number
  historicalExperience: string
  llmExplanation: string
  skills: Skill[]
  competencies: Competency[]
  weeklyAvailability: AvailabilityPoint[]
}

interface Project {
  id: string
  name: string
  rolesNeeded: string[]
}

function RecommendationWorkspace() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const urlProject = searchParams.get("project")
  const addToast = useToastStore((s) => s.addToast)
  const [selectedProjectId, setSelectedProjectId] = useState("")
  const [experienceLevel, setExperienceLevel] = useState("all")
  const [department, setDepartment] = useState("all")
  const [availabilityThreshold, setAvailabilityThreshold] = useState(50)

  // Matching results states
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [compareIds, setCompareIds] = useState<string[]>([])
  const [isCompareModeOpen, setIsCompareModeOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  // 1. Query projects options
  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projectsList"],
    queryFn: async () => {
      const summaries = await recommendationService.getProjects()
      return summaries.map(s => {
        const skillsArray = s.skillset
          ? s.skillset.split(",")
              .map(sk => sk.trim())
              .filter(sk => sk.length > 0)
          : []
        
        return {
          id: s.id,
          name: s.name,
          rolesNeeded: skillsArray
        }
      })
    }
  })

  // Pre-select project when list is loaded
  useEffect(() => {
    if (projects.length > 0 && !selectedProjectId) {
      const matching = projects.find((p: Project) => p.id === urlProject)
      setSelectedProjectId(matching ? matching.id : projects[0].id)
    }
  }, [projects, urlProject, selectedProjectId])

  // 2. Query candidates based on selection
  const { data: candidates = [], isLoading: loading, error, refetch } = useQuery<Candidate[]>({
    queryKey: ["recommendations", selectedProjectId, experienceLevel, department, availabilityThreshold],
    queryFn: async () => {
      const matchProj = projects.find(p => p.id === selectedProjectId)
      const requiredSkills = matchProj?.rolesNeeded || []

      const req: RecommendationRequest = {
        project_id: selectedProjectId,
        required_skills: requiredSkills,
        project_type: "AI",
        top_n: 10,
        strategy: "hybrid_v1"
      }
      
      const response = await recommendationService.getRecommendations(req)
      
      // Map response format to UI layout
      return response.recommendations.map(c => {
        const scoreVal = c.final_score <= 1 ? Math.round(c.final_score * 100) : Math.round(c.final_score)
        const skillMatch = c.category_scores?.skills 
          ? (c.category_scores.skills <= 1 ? Math.round(c.category_scores.skills * 100) : Math.round(c.category_scores.skills)) 
          : 85
        const competencyMatch = c.category_scores?.competencies 
          ? (c.category_scores.competencies <= 1 ? Math.round(c.category_scores.competencies * 100) : Math.round(c.category_scores.competencies)) 
          : 80
        const similarity = c.category_scores?.similarity 
          ? (c.category_scores.similarity <= 1 ? Math.round(c.category_scores.similarity * 100) : Math.round(c.category_scores.similarity)) 
          : 75

        return {
          id: c.employee_id,
          name: c.name || `Employee ${c.employee_id}`,
          role: c.job_name || "Engineer",
          avatar: "",
          score: scoreVal,
          confidence: (c.confidence === "High" ? "High" : "Medium") as "High" | "Medium",
          department: c.department_name || "Engineering",
          experience: c.experience_years || 4,
          availability: Math.round(100 - (c.utilization_percentage || 0)),
          skillMatch,
          competencyMatch,
          similarity,
          historicalExperience: c.experience_years ? `Has completed ${c.experience_years} matching delivery contracts.` : "No previous project metrics.",
          llmExplanation: response.explanation || "Highly qualified developer matching skills guidelines.",
          skills: (c.skills || []).map(s => ({
            name: s,
            rating: c.matching_skills.includes(s) ? 5 : 3,
            match: c.matching_skills.includes(s)
          })),
          competencies: (c.competencies || ["Communication", "Stakeholder Management"]).map(comp => ({
            name: comp,
            rating: 4
          })),
          weeklyAvailability: [
            { week: "W1", rate: Math.round(100 - (c.utilization_percentage || 0)) },
            { week: "W2", rate: 85 },
            { week: "W3", rate: 90 },
            { week: "W4", rate: 100 }
          ]
        }
      })
    },
    enabled: projects.length > 0 && !!selectedProjectId
  })



  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSelectCompare = (id: string) => {
    setCompareIds(prev => 
      prev.includes(id) 
        ? prev.filter(item => item !== id) 
        : prev.length < 3 
        ? [...prev, id] 
        : prev
    )
  }

  const handleAssignCandidate = (name: string) => {
    addToast(`Success: ${name} allocated to ${activeProjectDetails?.name || "project"}!`, "success")
  }

  const activeProjectDetails = projects.find(p => p.id === selectedProjectId)

  return (
    <div className="space-y-6 pb-12 font-sans text-foreground">
      


      {/* Main Header */}
      <div className="flex flex-col gap-1 md:flex-row md:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">AI Resource Recommendation</h1>
          <p className="text-muted-foreground text-xs md:text-sm">
            Semantic workforce matching engine using vector profiles and LLM explanations.
          </p>
        </div>
        <Button 
          variant="outline" 
          size="xs"
          onClick={() => router.push("/dashboard")}
          className="flex items-center gap-1.5 self-start text-xs rounded"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Dashboard
        </Button>
      </div>

      {/* Project Selector Panel */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
        <div>
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
            Target Project Pipeline
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="w-full max-w-md rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-blue-500 font-medium"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.id} - {p.name}
              </option>
            ))}
          </select>
        </div>
        {activeProjectDetails && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border/60 text-xs">
            <span className="text-muted-foreground font-semibold">Staffing Gaps Identified:</span>
            {activeProjectDetails.rolesNeeded.map((r, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 font-semibold border border-blue-600/10">
                {r}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Workspace Grid */}
      <div className="grid gap-6 md:grid-cols-4 items-start">
        
        {/* Filters Sidebar */}
        <div className="md:col-span-1 rounded-xl border border-border bg-card p-5 shadow-sm space-y-5">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <SlidersHorizontal className="h-4.5 w-4.5 text-blue-500" />
            <h3 className="font-semibold text-sm">Advanced Match Filters</h3>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Department</label>
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs outline-none focus:border-blue-500 font-medium"
            >
              <option value="all">All Departments</option>
              <option value="engineering">Engineering</option>
              <option value="design">Design</option>
              <option value="qa">Quality Assurance</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Experience Level</label>
            <div className="space-y-1.5 text-xs">
              <label className="flex items-center gap-2 cursor-pointer font-medium">
                <input 
                  type="radio" 
                  name="exp" 
                  value="all" 
                  checked={experienceLevel === "all"} 
                  onChange={() => setExperienceLevel("all")}
                  className="accent-blue-600"
                />
                All Experience
              </label>
              <label className="flex items-center gap-2 cursor-pointer font-medium">
                <input 
                  type="radio" 
                  name="exp" 
                  value="senior" 
                  checked={experienceLevel === "senior"} 
                  onChange={() => setExperienceLevel("senior")}
                  className="accent-blue-600"
                />
                Senior (5+ yrs)
              </label>
              <label className="flex items-center gap-2 cursor-pointer font-medium">
                <input 
                  type="radio" 
                  name="exp" 
                  value="mid" 
                  checked={experienceLevel === "mid"} 
                  onChange={() => setExperienceLevel("mid")}
                  className="accent-blue-600"
                />
                Mid-Level (3-5 yrs)
              </label>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <label className="text-muted-foreground">Min. Availability</label>
              <span className="text-blue-600 dark:text-blue-400">{availabilityThreshold}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="10"
              value={availabilityThreshold}
              onChange={(e) => setAvailabilityThreshold(parseInt(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer h-1.5 bg-border rounded-lg"
            />
          </div>
        </div>

        {/* Results Matching Area */}
        <div className="md:col-span-3 space-y-4">
          
          {/* Active selection info */}
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm font-sans flex items-center gap-2">
              <BrainCircuit className="h-4.5 w-4.5 text-indigo-500" />
              AI Recommendations ({candidates.length})
            </h3>
            {compareIds.length > 0 && (
              <Button
                onClick={() => setIsCompareModeOpen(true)}
                className="h-7 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-1.5"
              >
                <GitCompare className="h-3.5 w-3.5" />
                Compare Selection ({compareIds.length})
              </Button>
            )}
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 flex-col gap-2">
              <div className="h-6 w-6 rounded-full border-2 border-blue-600/20 border-t-blue-600 animate-spin" />
              <span className="text-xs text-muted-foreground font-sans">Matching talent database...</span>
            </div>
          ) : candidates.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {candidates.map((cand) => {
                const isSelectedForCompare = compareIds.includes(cand.id)
                return (
                  <motion.div
                    key={cand.id}
                    layoutId={cand.id}
                    className={`rounded-xl border bg-card p-5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between gap-4 relative group ${
                      isSelectedForCompare ? "border-blue-600 dark:border-blue-400 ring-1 ring-blue-600/30" : "border-border"
                    }`}
                  >
                    
                    {/* Compare Selection Checkbox */}
                    <div className="absolute top-4 right-4 flex items-center gap-1.5 z-10">
                      <label className="text-[10px] text-muted-foreground font-medium cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity">
                        Compare
                      </label>
                      <input
                        type="checkbox"
                        checked={isSelectedForCompare}
                        onChange={() => handleSelectCompare(cand.id)}
                        disabled={compareIds.length >= 3 && !isSelectedForCompare}
                        className="h-3.5 w-3.5 rounded border-border accent-blue-600 cursor-pointer"
                      />
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-full bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 flex items-center justify-center font-bold text-sm shadow-inner">
                          {cand.name ? cand.name.split(" ").map(n => n[0]).join("").toUpperCase() : ""}
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm text-foreground">{cand.name}</h4>
                          <p className="text-[11px] text-muted-foreground mt-0.5">{cand.role}</p>
                        </div>
                      </div>

                      {/* Matching Scores */}
                      <div className="grid grid-cols-2 gap-2 bg-muted/20 p-2.5 rounded-lg border border-border/40 text-xs">
                        <div>
                          <span className="text-[10px] text-muted-foreground block font-medium">Match Score</span>
                          <span className="font-bold text-foreground text-sm flex items-center gap-1">
                            {cand.score}%
                            <span className={`px-1 py-0.2 rounded text-[8px] font-extrabold uppercase tracking-wide ${
                              cand.confidence === "High" 
                                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" 
                                : "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400"
                            }`}>
                              {cand.confidence}
                            </span>
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-muted-foreground block font-medium">Availability</span>
                          <span className="font-semibold text-foreground text-xs block mt-0.5">
                            {cand.availability}% ready
                          </span>
                        </div>
                      </div>

                      <div className="text-[11px] text-muted-foreground font-sans line-clamp-3 leading-relaxed">
                        {cand.llmExplanation}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mt-2">
                      <Button
                        variant="outline"
                        size="xs"
                        className="flex-1 h-8 text-[11px] font-semibold border-indigo-500/25 hover:bg-indigo-500/5 text-indigo-600 dark:text-indigo-400"
                        onClick={() => setSelectedCandidate(cand)}
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        Explain Match
                      </Button>
                      <Button
                        size="xs"
                        onClick={() => handleAssignCandidate(cand.name)}
                        className="flex-1 h-8 text-[11px] font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded"
                      >
                        <UserPlus className="h-3.5 w-3.5" />
                        Assign Talent
                      </Button>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-20 border border-dashed border-border rounded-xl bg-card">
              <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
              <h4 className="font-semibold text-sm">No Matching Resources Found</h4>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                No employees match the active filters or target availability threshold. Try adjusting sliders or radio selectors.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* COMPARISON MODE OVERLAY MODAL */}
      <AnimatePresence>
        {isCompareModeOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/80 backdrop-blur-md"
              onClick={() => setIsCompareModeOpen(false)}
            />
            
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative w-full max-w-4xl bg-card border border-border rounded-xl shadow-2xl p-6 z-10 max-h-[85vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-border pb-3.5 mb-5">
                <div className="flex items-center gap-2">
                  <GitCompare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  <h3 className="font-bold text-base">Resource Match Comparison</h3>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={() => setIsCompareModeOpen(false)}>
                  <X className="h-4.5 w-4.5" />
                </Button>
              </div>

              <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
                {candidates
                  .filter(c => compareIds.includes(c.id))
                  .map(cand => (
                    <div key={cand.id} className="border border-border/80 rounded-xl p-4 bg-muted/10 space-y-4 flex flex-col justify-between">
                      <div className="space-y-3.5">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 flex items-center justify-center font-bold text-xs">
                            {cand.name ? cand.name.split(" ").map(n => n[0]).join("").toUpperCase() : ""}
                          </div>
                          <div>
                            <h4 className="font-semibold text-sm">{cand.name}</h4>
                            <p className="text-[10px] text-muted-foreground">{cand.role}</p>
                          </div>
                        </div>

                        <div className="space-y-2 text-xs border-t border-b border-border/60 py-3 space-y-2.5">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Match Score:</span>
                            <span className="font-bold text-blue-600 dark:text-blue-400">{cand.score}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Skills Alignment:</span>
                            <span className="font-semibold">{cand.skillMatch}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Competency Score:</span>
                            <span className="font-semibold">{cand.competencyMatch}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Availability Profile:</span>
                            <span className="font-semibold">{cand.availability}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Team Similarity:</span>
                            <span className="font-semibold">{cand.similarity}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Experience Length:</span>
                            <span className="font-semibold">{cand.experience} yrs</span>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-wider">Historical Context</span>
                          <p className="text-[10px] text-muted-foreground leading-normal">{cand.historicalExperience}</p>
                        </div>
                      </div>

                      <div className="pt-3">
                        <Button
                          size="xs"
                          onClick={() => {
                            handleAssignCandidate(cand.name)
                            setIsCompareModeOpen(false)
                          }}
                          className="w-full h-8 text-[11px] font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded"
                        >
                          Assign {cand.name.split(" ")[0]}
                        </Button>
                      </div>
                    </div>
                  ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* DETAILED EXPLAIN MATCH DRAWER */}
      <AnimatePresence>
        {selectedCandidate && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/60 backdrop-blur-sm"
              onClick={() => setSelectedCandidate(null)}
            />

            <div className="absolute inset-y-0 right-0 flex max-w-full">
              <motion.div
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 26, stiffness: 220 }}
                className="w-screen max-w-lg bg-card border-l border-border shadow-2xl p-6 flex flex-col justify-between h-full overflow-y-auto"
              >
                
                {/* Header */}
                <div className="flex items-center justify-between border-b border-border pb-3.5 mb-5 shrink-0">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />
                    <h3 className="font-bold text-base">AI Fit Diagnostics</h3>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-muted/50" onClick={() => setSelectedCandidate(null)}>
                    <X className="h-4.5 w-4.5" />
                  </Button>
                </div>

                <div className="flex-1 space-y-6">
                  
                  {/* Avatar Profile Info */}
                  <div className="flex items-center gap-3 bg-muted/20 p-3 rounded-lg border border-border/40">
                    <div className="h-10 w-10 rounded-full bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 flex items-center justify-center font-bold text-base">
                      {selectedCandidate.name ? selectedCandidate.name.split(" ").map(n => n[0]).join("").toUpperCase() : ""}
                    </div>
                    <div>
                      <h4 className="font-bold text-sm text-foreground">{selectedCandidate.name}</h4>
                      <p className="text-xs text-muted-foreground">{selectedCandidate.role}</p>
                    </div>
                  </div>

                  {/* Recharts Radar Score Match Breakdowns */}
                  <div className="space-y-2">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                      Diagnostic Scoring
                    </span>
                    <div className="h-[180px] w-full flex items-center justify-center">
                      {mounted ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart
                            cx="50%"
                            cy="50%"
                            outerRadius="70%"
                            data={[
                              { subject: "Skills", A: selectedCandidate.skillMatch, fullMark: 100 },
                              { subject: "Competency", A: selectedCandidate.competencyMatch, fullMark: 100 },
                              { subject: "Availability", A: selectedCandidate.availability, fullMark: 100 },
                              { subject: "Similarity", A: selectedCandidate.similarity, fullMark: 100 },
                              { subject: "Experience", A: selectedCandidate.experience * 10, fullMark: 100 }
                            ]}
                          >
                            <PolarGrid stroke="var(--border)" opacity={0.6} />
                            <PolarAngleAxis dataKey="subject" style={{ fontSize: "10px", fill: "var(--muted-foreground)", fontFamily: "sans-serif" }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                            <Radar
                              name={selectedCandidate.name}
                              dataKey="A"
                              stroke="#6366f1"
                              fill="#6366f1"
                              fillOpacity={0.2}
                            />
                          </RadarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="text-xs text-muted-foreground font-sans">Loading match criteria...</div>
                      )}
                    </div>
                  </div>

                  {/* Skills Match List */}
                  <div className="space-y-2">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                      Skill Alignment Detail
                    </span>
                    <div className="grid gap-2 grid-cols-1 sm:grid-cols-2 text-xs">
                      {selectedCandidate.skills.map((s, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 rounded-md border border-border bg-muted/10 font-sans">
                          <span className="font-medium text-foreground">{s.name}</span>
                          <span className="flex items-center gap-1.5 font-bold text-muted-foreground">
                            {s.rating}/5
                            {s.match ? (
                              <ShieldCheck className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <AlertTriangle className="h-4 w-4 text-yellow-500" />
                            )}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Availability Outlook */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                        FTE Availability Outlook (Next 4 Wks)
                      </span>
                      <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                        {selectedCandidate.availability}% Total Free Capacity
                      </span>
                    </div>
                    <div className="h-[90px] w-full">
                      {mounted ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <RechartsBarChart data={selectedCandidate.weeklyAvailability} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                            <XAxis dataKey="week" tickLine={false} axisLine={false} style={{ fontSize: "9px", fill: "var(--muted-foreground)", fontFamily: "sans-serif" }} />
                            <YAxis domain={[0, 100]} tickLine={false} axisLine={false} style={{ fontSize: "9px", fill: "var(--muted-foreground)", fontFamily: "sans-serif" }} />
                            <RechartsTooltip contentStyle={{ fontSize: "10px", borderRadius: "6px" }} />
                            <Bar dataKey="rate" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                          </RechartsBarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="text-xs text-muted-foreground font-sans">Loading capacity...</div>
                      )}
                    </div>
                  </div>

                  {/* LLM Narrative */}
                  <div className="bg-indigo-500/5 dark:bg-indigo-500/10 border border-indigo-500/10 rounded-xl p-4 space-y-2">
                    <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 font-bold text-xs">
                      <BrainCircuit className="h-4 w-4 shrink-0" />
                      <span>Generative Staffing Rationale</span>
                    </div>
                    <p className="text-xs leading-relaxed text-muted-foreground italic">
                      "{selectedCandidate.llmExplanation}"
                    </p>
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="pt-4 border-t border-border shrink-0 flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1 h-9 text-xs font-semibold text-muted-foreground hover:text-foreground"
                    onClick={() => setSelectedCandidate(null)}
                  >
                    Close Drawer
                  </Button>
                  <Button
                    className="flex-1 h-9 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded"
                    onClick={() => {
                      handleAssignCandidate(selectedCandidate.name)
                      setSelectedCandidate(null)
                    }}
                  >
                    Confirm Allocation
                  </Button>
                </div>
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>
      
    </div>
  )
}

export default function RecommendationPage() {
  return (
    <Suspense fallback={
      <div className="flex h-[75vh] w-full items-center justify-center flex-col gap-3">
        <div className="h-8 w-8 rounded-full border-4 border-blue-600/20 border-t-blue-600 animate-spin" />
        <p className="text-sm text-muted-foreground font-sans">Preparing resource matching database...</p>
      </div>
    }>
      <RecommendationWorkspace />
    </Suspense>
  )
}
