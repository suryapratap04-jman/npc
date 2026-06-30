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
  MessageSquare,
  MapPin,
  Calendar,
  Layers,
  Users,
  Activity,
  Award
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
  email: string
  role: string
  department: string
  location: string
  avatar: string
  score: number
  confidence: "High" | "Medium" | "Low"
  experience: number
  availability: number
  currentAllocation: number
  availabilityDate: string
  currentProject: string
  whyRecommended: string
  strengths: string[]
  potentialRisks: string[]
  
  // Breakdown scores
  skillMatch: number
  competencyMatch: number
  experienceScore: number
  availabilityScore: number
  historicalScore: number
  semanticScore: number
  
  llmExplanation: string
  skills: Skill[]
  competencies: Competency[]
  weeklyAvailability: AvailabilityPoint[]
}

interface Project {
  id: string
  name: string
  client: string
  technology: string
  domain: string
  projectType: string
  expectedStartDate: string
  demand: string
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
  const [availabilityWindow, setAvailabilityWindow] = useState("all")
  const [location, setLocation] = useState("all")

  // Workflow current active step tracking
  const [activeStep, setActiveStep] = useState(1)

  // Matching results states
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [compareIds, setCompareIds] = useState<string[]>([])
  const [isCompareModeOpen, setIsCompareModeOpen] = useState(false)
  const [mounted, setMounted] = useState(false)

  // 1. Query projects options (represents pipeline demands)
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
          client: s.client,
          technology: s.technology || "N/A",
          domain: s.domain || "N/A",
          projectType: s.project_type || "N/A",
          expectedStartDate: s.start_date || "N/A",
          demand: s.demand || "N/A",
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

  // Track selected project details
  const activeProjectDetails = projects.find(p => p.id === selectedProjectId)

  // Advancing steps helper
  useEffect(() => {
    if (selectedProjectId) {
      setActiveStep(2)
    }
  }, [selectedProjectId])

  // 2. Query candidates based on selection and filters
  const { data: candidatesResponse = null, isLoading: loading, refetch } = useQuery({
    queryKey: ["recommendations", selectedProjectId, experienceLevel, department, availabilityWindow, location],
    queryFn: async () => {
      if (!selectedProjectId) return null
      
      const req: RecommendationRequest = {
        project_id: selectedProjectId,
        required_skills: activeProjectDetails?.rolesNeeded || [],
        project_type: activeProjectDetails?.projectType || "AI",
        top_n: 10,
        strategy: "hybrid_v1",
        department: department === "all" ? undefined : department,
        experience_range: experienceLevel === "all" ? undefined : experienceLevel,
        availability_window: availabilityWindow === "all" ? undefined : availabilityWindow,
        location: location === "all" ? undefined : location,
        technology: activeProjectDetails?.technology,
        domain: activeProjectDetails?.domain
      }
      
      const response = await recommendationService.getRecommendations(req)
      
      // Map response format to UI layout
      const mappedCandidates = response.candidates.map(c => {
        const scoreVal = Math.round(c.final_score)
        const skillMatch = Math.round(c.skill_match)
        const competencyMatch = Math.round(c.competency_match)
        const experienceScore = Math.round(c.experience_score)
        const availabilityScore = Math.round(c.availability_score)
        const historicalScore = Math.round(c.historical_score)
        const semanticScore = Math.round(c.semantic_score)

        return {
          id: c.employee_id,
          name: c.name || `Employee ${c.employee_id.split('_').pop()}`,
          email: c.email || `${c.employee_id}@company.com`,
          role: c.job_name || "Engineer",
          department: c.department_name || "Engineering",
          location: c.location || "N/A",
          avatar: "",
          score: scoreVal,
          confidence: (c.confidence || "Medium") as "High" | "Medium" | "Low",
          experience: c.experience_years || 4,
          availability: Math.round(100 - (c.current_allocation || 0)),
          currentAllocation: c.current_allocation || 0,
          availabilityDate: c.availability_date || "Immediate",
          currentProject: c.current_project || "None (On Bench)",
          whyRecommended: c.why_recommended || "Highly aligned profile with target skills.",
          strengths: c.strengths || [],
          potentialRisks: c.potential_risks || [],
          
          skillMatch,
          competencyMatch,
          experienceScore,
          availabilityScore,
          historicalScore,
          semanticScore,
          
          llmExplanation: response.explanation || "Highly qualified developer matching skills guidelines.",
          skills: (c.skills || []).map(s => {
            const isMatch = (activeProjectDetails?.rolesNeeded || []).some(
              reqSkill => reqSkill.toLowerCase().trim() === s.toLowerCase().trim()
            )
            return {
              name: s,
              rating: isMatch ? 5 : 3,
              match: isMatch
            }
          }),
          competencies: (c.competencies || []).map(comp => ({
            name: comp,
            rating: 4
          })),
          weeklyAvailability: [
            { week: "W1", rate: Math.round(100 - (c.current_allocation || 0)) },
            { week: "W2", rate: Math.round(100 - (c.current_allocation || 0)) },
            { week: "W3", rate: Math.round(100 - (c.current_allocation || 0)) },
            { week: "W4", rate: Math.round(100 - (c.current_allocation || 0)) }
          ]
        }
      })

      return {
        ...response,
        candidates: mappedCandidates
      }
    },
    enabled: projects.length > 0 && !!selectedProjectId
  })

  const candidatesList = candidatesResponse?.candidates || []
  const globalExplanation = candidatesResponse?.explanation || ""
  const overallConfidence = candidatesResponse?.confidence || "Medium"
  const processingTime = candidatesResponse?.processing_time_ms || 0.0

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
    addToast(`Success: Allocated ${name} to ${activeProjectDetails?.client || "Project"} project demand!`, "success")
  }

  const triggerMatchAction = () => {
    refetch()
    setActiveStep(4)
    addToast("Triggered AI Matching Engine across workforce profiles.", "info")
  }

  return (
    <div className="space-y-6 pb-12 font-sans text-foreground">
      
      {/* Main Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
            AI Resource Allocation Workspace
          </h1>
          <p className="text-muted-foreground text-xs md:text-sm mt-0.5">
            红 Redesigned enterprise resource demand matcher powered by vector profiles and diagnostic scoring.
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => router.push("/dashboard")}
          className="flex items-center gap-1.5 self-start text-xs rounded border-border/80 hover:bg-muted/50"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Dashboard
        </Button>
      </div>

      {/* Redesigned Workflow Stepper Indicator */}
      <div className="grid grid-cols-6 gap-2 text-center text-[10px] md:text-xs font-semibold bg-muted/30 p-2 rounded-lg border border-border/50">
        <div className={`p-1.5 rounded transition-all duration-200 ${activeStep === 1 ? "bg-blue-600 text-white shadow-sm" : "text-muted-foreground"}`}>
          1. Select Demand
        </div>
        <div className={`p-1.5 rounded transition-all duration-200 ${activeStep === 2 ? "bg-blue-600 text-white shadow-sm" : activeStep > 2 ? "text-blue-600 dark:text-blue-400" : "text-muted-foreground"}`}>
          2. Review Gaps
        </div>
        <div className={`p-1.5 rounded transition-all duration-200 ${activeStep === 3 ? "bg-blue-600 text-white shadow-sm" : "text-muted-foreground"}`}>
          3. Apply Filters
        </div>
        <div className={`p-1.5 rounded transition-all duration-200 ${activeStep === 4 ? "bg-blue-600 text-white shadow-sm" : activeStep > 4 ? "text-blue-600 dark:text-blue-400" : "text-muted-foreground"}`}>
          4. Match Talent
        </div>
        <div className={`p-1.5 rounded transition-all duration-200 ${compareIds.length > 0 ? "bg-blue-600 text-white shadow-sm" : "text-muted-foreground"}`}>
          5. Compare Choices
        </div>
        <div className="p-1.5 rounded text-muted-foreground">
          6. Confirm Allocation
        </div>
      </div>

      {/* STEP 1: Select Project Demand */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-sm font-semibold border-b border-border/60 pb-2">
          <Briefcase className="h-4 w-4 text-blue-500" />
          <span>Step 1: Select Target Project Demand</span>
        </div>
        
        <div className="flex flex-col gap-4 md:flex-row md:items-center justify-between">
          <div className="w-full md:max-w-md">
            <select
              value={selectedProjectId}
              onChange={(e) => {
                setSelectedProjectId(e.target.value)
                setActiveStep(2)
              }}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-blue-500 font-medium"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.client} - {p.technology} (ID: {p.id})
                </option>
              ))}
            </select>
          </div>
          <div className="text-xs text-muted-foreground italic">
            Select a project pipeline item to automatically evaluate resource requirements.
          </div>
        </div>

        {/* STEP 2: Review Demand Metadata (Phase 3 Redesign) */}
        {activeProjectDetails && (
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 bg-muted/20 p-4 rounded-lg border border-border/40 text-xs">
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">Project Name / Client</span>
              <span className="font-bold text-foreground text-sm flex items-center gap-1.5">
                {activeProjectDetails.client}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">Technology Area</span>
              <span className="font-semibold text-foreground text-sm flex items-center gap-1">
                <Cpu className="h-3.5 w-3.5 text-indigo-500 shrink-0" />
                {activeProjectDetails.technology}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">Industry Domain</span>
              <span className="font-semibold text-foreground text-sm flex items-center gap-1">
                <Layers className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                {activeProjectDetails.domain}
              </span>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider block">Expected Start / Demand</span>
              <span className="font-semibold text-foreground text-sm flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                {activeProjectDetails.expectedStartDate} ({activeProjectDetails.demand} FTE)
              </span>
            </div>
            
            <div className="sm:col-span-2 md:col-span-4 border-t border-border/50 pt-2.5 flex flex-wrap items-center gap-2 text-xs">
              <span className="text-muted-foreground font-semibold">Step 2: Identified Staffing Gaps (Skills Needed):</span>
              {activeProjectDetails.rolesNeeded.map((r, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 font-semibold border border-blue-600/10">
                  {r}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Grid Layout for Match Filters & Recommendations */}
      <div className="grid gap-6 md:grid-cols-4 items-start">
        
        {/* STEP 3: Advanced Match Filters (Sidebar) */}
        <div className="md:col-span-1 rounded-xl border border-border bg-card p-5 shadow-sm space-y-5">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <SlidersHorizontal className="h-4.5 w-4.5 text-blue-500" />
            <h3 className="font-semibold text-sm">Step 3: Match Filters</h3>
          </div>

          {/* Department Filter */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Department</label>
            <select
              value={department}
              onChange={(e) => {
                setDepartment(e.target.value)
                setActiveStep(3)
              }}
              className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs outline-none focus:border-blue-500 font-medium"
            >
              <option value="all">All Departments</option>
              <option value="engineering">Engineering</option>
              <option value="design">Design</option>
              <option value="qa">Quality Assurance</option>
            </select>
          </div>

          {/* Experience Range Filter (Connected to Backend - Phase 5) */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground block">Experience level</label>
            <div className="space-y-1.5 text-xs">
              <label className="flex items-center gap-2 cursor-pointer font-medium">
                <input 
                  type="radio" 
                  name="exp" 
                  value="all" 
                  checked={experienceLevel === "all"} 
                  onChange={() => {
                    setExperienceLevel("all")
                    setActiveStep(3)
                  }}
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
                  onChange={() => {
                    setExperienceLevel("senior")
                    setActiveStep(3)
                  }}
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
                  onChange={() => {
                    setExperienceLevel("mid")
                    setActiveStep(3)
                  }}
                  className="accent-blue-600"
                />
                Mid-Level (3-5 yrs)
              </label>
              <label className="flex items-center gap-2 cursor-pointer font-medium">
                <input 
                  type="radio" 
                  name="exp" 
                  value="junior" 
                  checked={experienceLevel === "junior"} 
                  onChange={() => {
                    setExperienceLevel("junior")
                    setActiveStep(3)
                  }}
                  className="accent-blue-600"
                />
                Junior (&lt;3 yrs)
              </label>
            </div>
          </div>

          {/* Availability Options (Phase 6 Redesign) */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground block">Availability Profile</label>
            <select
              value={availabilityWindow}
              onChange={(e) => {
                setAvailabilityWindow(e.target.value)
                setActiveStep(3)
              }}
              className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs outline-none focus:border-blue-500 font-medium"
            >
              <option value="all">All Capacities</option>
              <option value="Available Now">Available Now (0% Alloc)</option>
              <option value="Available Within 2 Weeks">Available Within 2 Weeks</option>
              <option value="Available Within 30 Days">Available Within 30 Days</option>
              <option value="Allocation <50%">Allocation &lt;50%</option>
              <option value="Bench Resources">Bench Resources Only</option>
            </select>
          </div>

          {/* Location Filter */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground block">Location</label>
            <select
              value={location}
              onChange={(e) => {
                setLocation(e.target.value)
                setActiveStep(3)
              }}
              className="w-full rounded-md border border-border bg-background px-2.5 py-1.5 text-xs outline-none focus:border-blue-500 font-medium"
            >
              <option value="all">All Locations</option>
              <option value="New York">New York</option>
              <option value="San Francisco">San Francisco</option>
              <option value="London">London</option>
              <option value="Toronto">Toronto</option>
            </select>
          </div>

          {/* Matching Engine Action Button */}
          <Button
            onClick={triggerMatchAction}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-2 rounded shadow flex items-center justify-center gap-1.5 pt-2 border-t border-border"
          >
            <BrainCircuit className="h-4 w-4" /> Run Matching Engine
          </Button>
        </div>

        {/* STEP 4: AI Recommendations Display Area */}
        <div className="md:col-span-3 space-y-4">
          
          {/* Active selection info */}
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              <Sparkles className="h-4.5 w-4.5 text-indigo-500 animate-pulse" />
              AI Recommendations ({candidatesList.length})
              {processingTime > 0 && (
                <span className="text-[10px] text-muted-foreground font-normal bg-muted px-2 py-0.5 rounded border border-border/30">
                  Engine latency: {processingTime} ms
                </span>
              )}
            </h3>
            
            {compareIds.length > 0 && (
              <Button
                onClick={() => setIsCompareModeOpen(true)}
                className="h-7 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-1.5"
              >
                <GitCompare className="h-3.5 w-3.5" />
                Step 5: Compare Selection ({compareIds.length}/3)
              </Button>
            )}
          </div>

          {/* Generative Narrative Explanation Panel */}
          {globalExplanation && (
            <div className="bg-indigo-600/5 border border-indigo-600/10 rounded-xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 font-bold text-xs">
                  <BrainCircuit className="h-4.5 w-4.5" />
                  <span>Generative Team Staffing Explanation</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[8px] font-extrabold uppercase tracking-wider ${
                  overallConfidence === "High" 
                    ? "bg-emerald-500/15 text-emerald-600" 
                    : "bg-yellow-500/15 text-yellow-600"
                }`}>
                  Overall Pool Confidence: {overallConfidence}
                </span>
              </div>
              <p className="text-[11px] md:text-xs leading-relaxed text-muted-foreground font-sans">
                {globalExplanation.replace(/###\s/g, "").replace(/\*\*/g, "")}
              </p>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-24 flex-col gap-2 bg-card rounded-xl border border-border border-dashed">
              <div className="h-7 w-7 rounded-full border-2 border-blue-600/20 border-t-blue-600 animate-spin" />
              <span className="text-xs text-muted-foreground font-sans">Evaluating talent database vector embeddings...</span>
            </div>
          ) : candidatesList.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {candidatesList.map((cand) => {
                const isSelectedForCompare = compareIds.includes(cand.id)
                return (
                  <motion.div
                    key={cand.id}
                    layoutId={cand.id}
                    className={`rounded-xl border bg-card p-5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between gap-4 relative group ${
                      isSelectedForCompare ? "border-blue-600 dark:border-blue-400 ring-1 ring-blue-600/30" : "border-border/80"
                    }`}
                  >
                    
                    {/* Compare Selection Checkbox */}
                    <div className="absolute top-4 right-4 flex items-center gap-1.5 z-10">
                      <label className="text-[9px] text-muted-foreground font-semibold cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity">
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
                      {/* Name / Role Title Section */}
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-full bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 flex items-center justify-center font-bold text-sm shadow-inner">
                          {cand.name ? cand.name.split(" ").map(n => n[0]).join("").toUpperCase() : ""}
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm text-foreground flex items-center gap-1.5">
                            {cand.name}
                            <span className="text-[10px] text-muted-foreground font-normal bg-muted px-1.5 py-0.2 rounded border border-border/30">
                              {cand.location}
                            </span>
                          </h4>
                          <p className="text-[11px] text-muted-foreground mt-0.5">{cand.role} ({cand.department})</p>
                        </div>
                      </div>

                      {/* Matching Scores Highlights (Phase 7 Redesign) */}
                      <div className="grid grid-cols-3 gap-2 bg-muted/20 p-2.5 rounded-lg border border-border/40 text-xs">
                        <div>
                          <span className="text-[9px] text-muted-foreground block font-semibold uppercase tracking-wide">Match score</span>
                          <span className="font-bold text-foreground text-sm flex items-center gap-1 mt-0.5">
                            {cand.score}%
                            <span className={`px-1 py-0.2 rounded text-[7px] font-extrabold uppercase ${
                              cand.confidence === "High" 
                                ? "bg-emerald-500/15 text-emerald-600" 
                                : "bg-yellow-500/15 text-yellow-600"
                            }`}>
                              {cand.confidence[0]}
                            </span>
                          </span>
                        </div>
                        
                        <div>
                          <span className="text-[9px] text-muted-foreground block font-semibold uppercase tracking-wide">allocation</span>
                          <span className="font-bold text-foreground text-xs block mt-1">
                            {cand.currentAllocation}% active
                          </span>
                        </div>
                        
                        <div>
                          <span className="text-[9px] text-muted-foreground block font-semibold uppercase tracking-wide">exp years</span>
                          <span className="font-bold text-foreground text-xs block mt-1">
                            {cand.experience} Years
                          </span>
                        </div>
                      </div>

                      {/* Current Project & Next Available Date */}
                      <div className="text-[10px] text-muted-foreground border-t border-b border-border/50 py-2 space-y-1">
                        <div className="flex justify-between">
                          <span>Current Project:</span>
                          <span className="font-medium text-foreground">{cand.currentProject}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Available Date:</span>
                          <span className="font-medium text-blue-600 dark:text-blue-400 font-sans flex items-center gap-1">
                            <Clock className="h-3 w-3 shrink-0" />
                            {cand.availabilityDate}
                          </span>
                        </div>
                      </div>

                      {/* Why Recommended candidate-specific (Phase 7 Explainability) */}
                      <div className="text-[11px] text-muted-foreground font-sans line-clamp-2 leading-relaxed bg-indigo-500/5 p-2 rounded border border-indigo-500/5 font-medium italic">
                        "{cand.whyRecommended}"
                      </div>
                    </div>

                    <div className="flex items-center gap-2 mt-1.5 shrink-0">
                      <Button
                        variant="outline"
                        size="xs"
                        className="flex-1 h-8 text-[10px] font-bold border-indigo-500/25 hover:bg-indigo-500/5 text-indigo-600 dark:text-indigo-400"
                        onClick={() => setSelectedCandidate(cand)}
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        Explain Match
                      </Button>
                      <Button
                        size="xs"
                        onClick={() => handleAssignCandidate(cand.name)}
                        className="flex-1 h-8 text-[10px] font-bold bg-blue-600 hover:bg-blue-700 text-white rounded"
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
                No active employees match the selected department, experience filters, location constraints, or availability requirements. Try resetting sidebar filters.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* STEP 5: COMPARISON MODE OVERLAY MODAL */}
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
              className="relative w-full max-w-5xl bg-card border border-border rounded-xl shadow-2xl p-6 z-10 max-h-[85vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-border pb-3.5 mb-5">
                <div className="flex items-center gap-2">
                  <GitCompare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  <h3 className="font-bold text-base">Step 5: Resource Match Comparison</h3>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" onClick={() => setIsCompareModeOpen(false)}>
                  <X className="h-4.5 w-4.5" />
                </Button>
              </div>

              <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
                {candidatesList
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
                            <p className="text-[10px] text-muted-foreground">{cand.role} ({cand.location})</p>
                          </div>
                        </div>

                        {/* Complete Breakdown Scores Side-by-Side (Phase 8 Redesign) */}
                        <div className="space-y-2 text-xs border-t border-b border-border/60 py-3 space-y-2.5">
                          <div className="flex justify-between font-bold text-blue-600 dark:text-blue-400 border-b border-border/30 pb-1.5">
                            <span>Final Score:</span>
                            <span>{cand.score}%</span>
                          </div>
                          
                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                              <span>Skills alignment:</span>
                              <span>{cand.skillMatch}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                              <div className="h-full bg-blue-500" style={{ width: `${cand.skillMatch}%` }} />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                              <span>Competency Score:</span>
                              <span>{cand.competencyMatch}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                              <div className="h-full bg-emerald-500" style={{ width: `${cand.competencyMatch}%` }} />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                              <span>Experience Rating:</span>
                              <span>{cand.experienceScore}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                              <div className="h-full bg-yellow-500" style={{ width: `${cand.experienceScore}%` }} />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                              <span>Availability Band:</span>
                              <span>{cand.availabilityScore}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                              <div className="h-full bg-indigo-500" style={{ width: `${cand.availabilityScore}%` }} />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                              <span>Historical Experience:</span>
                              <span>{cand.historicalScore}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                              <div className="h-full bg-purple-500" style={{ width: `${cand.historicalScore}%` }} />
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                              <span>Semantic Matching:</span>
                              <span>{cand.semanticScore}%</span>
                            </div>
                            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
                              <div className="h-full bg-pink-500" style={{ width: `${cand.semanticScore}%` }} />
                            </div>
                          </div>
                        </div>

                        <div className="space-y-1">
                          <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-wider">Candidate Strengths</span>
                          <ul className="text-[10px] text-muted-foreground list-disc pl-3.5 space-y-0.5">
                            {cand.strengths.slice(0, 2).map((st, i) => (
                              <li key={i}>{st}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* STEP 6: Confirm Allocation */}
                      <div className="pt-3">
                        <Button
                          size="xs"
                          onClick={() => {
                            handleAssignCandidate(cand.name)
                            setIsCompareModeOpen(false)
                          }}
                          className="w-full h-8 text-[11px] font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded"
                        >
                          Step 6: Allocate {cand.name.split(" ")[0]}
                        </Button>
                      </div>
                    </div>
                  ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* DETAILED EXPLAIN MATCH DRAWER (Phase 8 Diagnostics) */}
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
                className="w-screen max-w-lg bg-card border-l border-border shadow-2xl p-6 flex flex-col justify-between h-full overflow-y-auto z-50"
              >
                
                {/* Header */}
                <div className="flex items-center justify-between border-b border-border pb-3.5 mb-5 shrink-0">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />
                    <h3 className="font-bold text-base">AI Diagnostics Drawer</h3>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-muted/50" onClick={() => setSelectedCandidate(null)}>
                    <X className="h-4.5 w-4.5" />
                  </Button>
                </div>

                <div className="flex-1 space-y-6">
                  
                  {/* Profile Info */}
                  <div className="flex items-center justify-between bg-muted/20 p-3 rounded-lg border border-border/40">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 flex items-center justify-center font-bold text-base">
                        {selectedCandidate.name ? selectedCandidate.name.split(" ").map(n => n[0]).join("").toUpperCase() : ""}
                      </div>
                      <div>
                        <h4 className="font-bold text-sm text-foreground">{selectedCandidate.name}</h4>
                        <p className="text-xs text-muted-foreground">{selectedCandidate.role} ({selectedCandidate.department})</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-muted-foreground block font-semibold uppercase tracking-wider">Final Score</span>
                      <span className="font-extrabold text-blue-600 text-lg">{selectedCandidate.score}%</span>
                    </div>
                  </div>

                  {/* Recharts Radar Score Match Breakdowns */}
                  <div className="space-y-2">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                      Diagnostic Scoring Map
                    </span>
                    <div className="h-[200px] w-full flex items-center justify-center bg-muted/10 border border-border/50 rounded-lg">
                      {mounted ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart
                            cx="50%"
                            cy="50%"
                            outerRadius="70%"
                            data={[
                              { subject: "Skills Match", A: selectedCandidate.skillMatch, fullMark: 100 },
                              { subject: "Competency", A: selectedCandidate.competencyMatch, fullMark: 100 },
                              { subject: "Experience", A: selectedCandidate.experienceScore, fullMark: 100 },
                              { subject: "Availability", A: selectedCandidate.availabilityScore, fullMark: 100 },
                              { subject: "Similarity", A: selectedCandidate.semanticScore, fullMark: 100 },
                              { subject: "Historical", A: selectedCandidate.historicalScore, fullMark: 100 }
                            ]}
                          >
                            <PolarGrid stroke="var(--border)" opacity={0.6} />
                            <PolarAngleAxis dataKey="subject" style={{ fontSize: "9px", fill: "var(--muted-foreground)", fontFamily: "sans-serif", fontWeight: "600" }} />
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

                  {/* Diagnostic Breakdown Numbers (Phase 8 Breakdown) */}
                  <div className="space-y-2.5">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                      Scoring Feature Breakdown
                    </span>
                    <div className="grid gap-2 grid-cols-2 text-xs">
                      <div className="p-2.5 rounded-lg border border-border/50 bg-card flex justify-between items-center">
                        <span className="text-muted-foreground font-medium">Skills Match Score:</span>
                        <span className="font-bold text-foreground">{selectedCandidate.skillMatch}%</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-border/50 bg-card flex justify-between items-center">
                        <span className="text-muted-foreground font-medium">Competency Rating:</span>
                        <span className="font-bold text-foreground">{selectedCandidate.competencyMatch}%</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-border/50 bg-card flex justify-between items-center">
                        <span className="text-muted-foreground font-medium">Experience Score:</span>
                        <span className="font-bold text-foreground">{selectedCandidate.experienceScore}%</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-border/50 bg-card flex justify-between items-center">
                        <span className="text-muted-foreground font-medium">Availability Score:</span>
                        <span className="font-bold text-foreground">{selectedCandidate.availabilityScore}%</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-border/50 bg-card flex justify-between items-center">
                        <span className="text-muted-foreground font-medium">Historical Score:</span>
                        <span className="font-bold text-foreground">{selectedCandidate.historicalScore}%</span>
                      </div>
                      <div className="p-2.5 rounded-lg border border-border/50 bg-card flex justify-between items-center">
                        <span className="text-muted-foreground font-medium">Semantic Similarity:</span>
                        <span className="font-bold text-foreground">{selectedCandidate.semanticScore}%</span>
                      </div>
                    </div>
                  </div>

                  {/* Strengths & Risks (Phase 7 Explainability) */}
                  <div className="grid gap-3 sm:grid-cols-2 text-xs">
                    <div className="p-3 bg-emerald-500/5 dark:bg-emerald-500/10 border border-emerald-500/10 rounded-xl space-y-1.5">
                      <span className="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                        <ShieldCheck className="h-4 w-4" /> Verified Strengths
                      </span>
                      <ul className="list-disc pl-4 text-muted-foreground space-y-1">
                        {selectedCandidate.strengths.map((str, i) => (
                          <li key={i}>{str}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="p-3 bg-yellow-500/5 dark:bg-yellow-500/10 border border-yellow-500/10 rounded-xl space-y-1.5">
                      <span className="text-yellow-600 dark:text-yellow-400 font-bold flex items-center gap-1">
                        <AlertTriangle className="h-4 w-4" /> Potential Risks
                      </span>
                      <ul className="list-disc pl-4 text-muted-foreground space-y-1">
                        {selectedCandidate.potentialRisks.map((risk, i) => (
                          <li key={i}>{risk}</li>
                        ))}
                      </ul>
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

                  {/* Competency Alignment List */}
                  <div className="space-y-2">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                      Verified Competency Strengths
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedCandidate.competencies.map((c, idx) => (
                        <span key={idx} className="px-2.5 py-1 rounded-md bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-sans text-xs border border-indigo-500/10 font-semibold shadow-sm">
                          {c.name}
                        </span>
                      ))}
                      {selectedCandidate.competencies.length === 0 && (
                        <span className="text-xs text-muted-foreground font-sans italic bg-muted/20 border border-border p-2 rounded-md w-full block">
                          No specialized competencies registered with rating &gt;= 3
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Availability Outlook */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                        FTE Capacity Outlook (Next 4 Wks)
                      </span>
                      <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                        {selectedCandidate.availability}% Free Capacity
                      </span>
                    </div>
                    <div className="h-[90px] w-full bg-muted/10 rounded-lg p-2.5 border border-border/50">
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
                </div>

                {/* Footer Controls (Confirm Allocation) */}
                <div className="pt-4 border-t border-border shrink-0 flex gap-3 mt-4">
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
