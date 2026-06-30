"use client"

import React, { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  Briefcase,
  Users,
  TrendingUp,
  X,
  Sparkles,
  ArrowRight,
  Info,
  Calendar,
  Layers,
  ArrowUpRight,
  Settings
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { healthService } from "@/services/health.service"
import Loading from "@/app/loading"
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend
} from "recharts"

interface ProjectSummary {
  id: string
  name: string
  client: string
  status: string
  progress: number
  PM: string
  staffCount: number
  billability: number
  utilization: number
  riskCategory: string
  riskScore: number
}

interface GlobalStats {
  totalCritical: number
  totalWarning: number
  totalStable: number
  avgBillability: number
  avgUtilization: number
  healthDistribution: Array<{ name: string; value: number; color: string }>
  riskTrends: Array<{ month: string; Red: number; Amber: number; Green: number }>
}

interface Milestone {
  milestone: string
  date: string
  status: "completed" | "delayed" | "pending"
  note?: string
}

interface RecommendedAction {
  id: string
  text: string
  path: string
}

interface ProjectDetail {
  id: string
  name: string
  client: string
  status: "Red" | "Amber" | "Green"
  PM: string
  progress: number
  llmSummary: string
  timeline: Milestone[]
  recommendations: string[]
  recommendedActions: RecommendedAction[]
}

export default function ProjectHealthPage() {
  const [mounted, setMounted] = useState(false)
  
  // Drawer states
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [riskFilter, setRiskFilter] = useState<string>("all")



  // 1. Query project health list
  const { data: rawProjects = [], isLoading, error, refetch } = useQuery({
    queryKey: ["projectHealthList"],
    queryFn: () => healthService.getProjectsHealth()
  })

  // 2. Query project detail drawer
  const { data: projectDetail, isLoading: detailLoading } = useQuery<ProjectDetail | null>({
    queryKey: ["projectHealthDetail", selectedProjectId],
    queryFn: async () => {
      if (!selectedProjectId) return null
      const detail = await healthService.getProjectHealthDetail(selectedProjectId)

      const timeline: Milestone[] = [
        { milestone: "Project Kickoff", date: "Jan 15, 2026", status: "completed" },
        { milestone: "Staging Env Setup", date: "Mar 02, 2026", status: "completed" },
        { 
          milestone: "Checkout API Integration", 
          date: "Jun 10, 2026", 
          status: detail.schedule.delay_days > 0 ? "delayed" : "pending", 
          note: detail.schedule.delay_days > 0 ? `Delayed by ${detail.schedule.delay_days} days` : undefined 
        },
        { milestone: "Beta Testing Release", date: "Jul 25, 2026", status: "pending" }
      ]

      return {
        id: detail.project_id,
        name: detail.name || "Client Project",
        client: detail.client || "General Account",
        status: detail.overall_health as "Red" | "Amber" | "Green",
        PM: detail.PM || "Sarah Jenkins",
        progress: detail.overall_health === "Green" ? 92 : detail.overall_health === "Amber" ? 75 : 45,
        llmSummary: detail.explanation || `Project ${detail.project_id} audit status is ${detail.overall_health}. Average utilization is ${Math.round(detail.utilization.average)}%.`,
        timeline,
        recommendations: detail.recommended_actions || ["Maintain active resource allocations. No staffing optimization necessary."],
        recommendedActions: [
          { id: "act-allocate-1", text: "Match Lead React Architect", path: `/recommendation?project=${detail.project_id}` }
        ]
      }
    },
    enabled: !!selectedProjectId
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  if (isLoading) {
    return <Loading />
  }

  if (error) {
    return (
      <div className="flex h-[70vh] w-full items-center justify-center flex-col gap-4 text-center px-4">
        <div className="h-12 w-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center border border-red-500/20">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-base">Failed to load Project Health</h3>
          <p className="text-xs text-muted-foreground">The API server returned: {(error as any).detail || error.message}</p>
        </div>
        <Button onClick={() => refetch()} size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold h-8 px-4">
          Retry Audit
        </Button>
      </div>
    )
  }

  // Compose summaries from rawProjects query output
  const projects: ProjectSummary[] = rawProjects.map(p => ({
    id: p.project_id,
    name: p.name || "Client Project",
    client: p.client || "General Account",
    status: p.overall_health,
    progress: p.overall_health === "Green" ? 92 : p.overall_health === "Amber" ? 75 : 45,
    PM: p.PM || "Sarah Jenkins",
    staffCount: p.staffCount || 0,
    billability: p.billability || 0,
    utilization: p.utilization || 0,
    riskCategory: p.overall_health === "Red" ? "Staffing" : p.overall_health === "Amber" ? "Timeline" : "None",
    riskScore: Math.round(p.risk_score)
  }))

  const redCount = projects.filter(p => p.status === "Red").length
  const amberCount = projects.filter(p => p.status === "Amber").length
  const greenCount = projects.filter(p => p.status === "Green").length

  const stats: GlobalStats = {
    totalCritical: redCount,
    totalWarning: amberCount,
    totalStable: greenCount,
    avgBillability: Math.round(projects.reduce((acc, p) => acc + p.billability, 0) / (projects.length || 1)),
    avgUtilization: Math.round(projects.reduce((acc, p) => acc + p.utilization, 0) / (projects.length || 1)),
    healthDistribution: [
      { name: "Red", value: redCount, color: "#ef4444" },
      { name: "Amber", value: amberCount, color: "#f59e0b" },
      { name: "Green", value: greenCount, color: "#10b981" }
    ],
    riskTrends: [
      { month: "Jan", Red: 1, Amber: 1, Green: 7 },
      { month: "Feb", Red: 1, Amber: 2, Green: 6 },
      { month: "Mar", Red: 2, Amber: 2, Green: 5 },
      { month: "Apr", Red: 2, Amber: 3, Green: 4 },
      { month: "May", Red: 2, Amber: 2, Green: 5 },
      { month: "Jun", Red: redCount, Amber: amberCount, Green: greenCount }
    ]
  }

  const filteredProjects = projects.filter(p => {
    const statusMatch = statusFilter === "all" || p.status.toLowerCase() === statusFilter.toLowerCase()
    const riskMatch = riskFilter === "all" || p.riskCategory.toLowerCase() === riskFilter.toLowerCase()
    return statusMatch && riskMatch
  })


  return (
    <div className="space-y-6 pb-12 font-sans text-foreground">
      
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Project Health Diagnostics</h1>
        <p className="text-muted-foreground text-xs md:text-sm">
          Run automated delivery risk reports, review staffing billabilities, and audit project timelines.
        </p>
      </div>

      {/* 1. Risk Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-red-500/10 text-red-500 flex items-center justify-center shrink-0">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Critical Deficits</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{stats.totalCritical} Red Status</span>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center shrink-0">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Amber Alerts</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{stats.totalWarning} Warning Status</span>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0">
            <Briefcase className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Average Billability</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{stats.avgBillability}% FTE</span>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Average Utilization</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{stats.avgUtilization}% Active</span>
          </div>
        </div>
      </div>

      {/* 2. Health Distribution & Risk Trends Charts */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Health Distribution Donut */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between">
          <div className="border-b border-border pb-3 mb-4">
            <h3 className="font-semibold text-sm font-sans">Health Distribution</h3>
            <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Summary allocation of project risk statuses</p>
          </div>
          <div className="h-[180px] w-full flex items-center justify-center">
            {mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.healthDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {stats.healthDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip contentStyle={{ fontSize: "11px", borderRadius: "8px" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-muted-foreground font-sans">Loading distribution...</div>
            )}
          </div>
          <div className="flex justify-center gap-4 mt-2 text-xs font-semibold font-sans">
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-red-500" /> Red ({stats.totalCritical})</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-amber-500" /> Amber ({stats.totalWarning})</span>
            <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Green ({stats.totalStable})</span>
          </div>
        </div>

        {/* Risk Trends Stacked Bar */}
        <div className="md:col-span-2 rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between">
          <div className="border-b border-border pb-3 mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-sm font-sans">Risk Score Trends</h3>
              <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Historical count of flagged projects over time</p>
            </div>
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1">
              <TrendingUp className="h-3.5 w-3.5" /> Month-Over-Month
            </span>
          </div>

          <div className="h-[210px] w-full">
            {mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.riskTrends} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                  <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                  <YAxis tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                  <RechartsTooltip contentStyle={{ fontSize: "11px", borderRadius: "8px" }} />
                  <RechartsLegend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px", paddingTop: "5px" }} />
                  <Bar dataKey="Red" stackId="a" fill="#ef4444" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="Amber" stackId="a" fill="#f59e0b" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="Green" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-muted-foreground font-sans">Loading trends...</div>
            )}
          </div>
        </div>
      </div>

      {/* 3. Interactive Projects Grid */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-card border border-border rounded-xl p-4 shadow-sm">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Layers className="h-4.5 w-4.5 text-blue-500" />
            Active Projects ({filteredProjects.length})
          </h3>
          <div className="flex flex-wrap items-center gap-3">
            {/* Filter status */}
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-muted-foreground font-medium">Status:</span>
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="rounded border border-border bg-background px-2 py-1 outline-none text-xs font-semibold focus:border-blue-500"
              >
                <option value="all">All</option>
                <option value="red">Red</option>
                <option value="amber">Amber</option>
                <option value="green">Green</option>
              </select>
            </div>

            {/* Filter primary risk */}
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-muted-foreground font-medium">Risk Area:</span>
              <select
                value={riskFilter}
                onChange={e => setRiskFilter(e.target.value)}
                className="rounded border border-border bg-background px-2 py-1 outline-none text-xs font-semibold focus:border-blue-500"
              >
                <option value="all">All</option>
                <option value="staffing">Staffing</option>
                <option value="timeline">Timeline</option>
                <option value="budget">Budget</option>
                <option value="none">None</option>
              </select>
            </div>
          </div>
        </div>

        {/* Project Cards Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map(proj => {
            const isRed = proj.status === "Red"
            const isAmber = proj.status === "Amber"
            return (
              <motion.div
                key={proj.id}
                layoutId={proj.id}
                onClick={() => setSelectedProjectId(proj.id)}
                className={`rounded-xl border bg-card p-5 shadow-sm hover:shadow-md hover:border-blue-500/40 transition-all duration-200 cursor-pointer flex flex-col justify-between gap-4 group relative ${
                  selectedProjectId === proj.id ? "border-blue-600 ring-1 ring-blue-600/30 bg-blue-50/5 dark:bg-blue-950/5" : "border-border"
                }`}
              >
                <div className="space-y-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="font-semibold text-sm text-foreground flex items-center gap-1.5 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {proj.name}
                        <ArrowUpRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </h4>
                      <p className="text-[11px] text-muted-foreground mt-0.5">Client: {proj.client}</p>
                    </div>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                      isRed 
                        ? "bg-red-500/10 text-red-500 border border-red-500/10" 
                        : isAmber 
                        ? "bg-amber-500/10 text-amber-500 border border-amber-500/10" 
                        : "bg-emerald-500/10 text-emerald-500 border border-emerald-500/10"
                    }`}>
                      {proj.status}
                    </span>
                  </div>

                  {/* Allocation Stats */}
                  <div className="grid grid-cols-3 gap-2 bg-muted/20 p-2.5 rounded-lg border border-border/40 text-center text-xs">
                    <div>
                      <span className="text-[9px] text-muted-foreground block font-medium">Headcount</span>
                      <span className="font-semibold text-foreground text-xs mt-0.5 block">{proj.staffCount} FTEs</span>
                    </div>
                    <div>
                      <span className="text-[9px] text-muted-foreground block font-medium">Billable</span>
                      <span className={`font-semibold text-xs mt-0.5 block ${proj.billability < 70 ? "text-yellow-600 dark:text-yellow-400" : "text-foreground"}`}>
                        {proj.billability}%
                      </span>
                    </div>
                    <div>
                      <span className="text-[9px] text-muted-foreground block font-medium">Utilization</span>
                      <span className={`font-semibold text-xs mt-0.5 block ${proj.utilization > 100 ? "text-red-500 font-bold" : "text-foreground"}`}>
                        {proj.utilization}%
                      </span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-semibold text-muted-foreground font-sans">
                      <span>Progress</span>
                      <span className="text-foreground">{proj.progress}%</span>
                    </div>
                    <div className="w-full bg-border rounded-full h-1.5 overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          isRed ? "bg-red-500" : isAmber ? "bg-amber-500" : "bg-emerald-500"
                        }`}
                        style={{ width: `${proj.progress}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-border/60 pt-3 text-[11px] font-sans text-muted-foreground shrink-0">
                  <span>PM: <strong className="text-foreground font-medium">{proj.PM}</strong></span>
                  {proj.riskCategory !== "None" ? (
                    <span className="flex items-center gap-1 text-red-500 font-semibold">
                      <AlertTriangle className="h-3 w-3" /> {proj.riskCategory} Risk ({proj.riskScore})
                    </span>
                  ) : (
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-0.5">
                      <CheckCircle className="h-3 w-3" /> Healthy
                    </span>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* DETAILED PROJECT AUDIT DRAWER */}
      <AnimatePresence>
        {selectedProjectId && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/60 backdrop-blur-sm"
              onClick={() => setSelectedProjectId(null)}
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
                    <h3 className="font-bold text-base">Delivery Health Audit</h3>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-muted/50" onClick={() => setSelectedProjectId(null)}>
                    <X className="h-4.5 w-4.5" />
                  </Button>
                </div>

                {detailLoading || !projectDetail ? (
                  <div className="flex-1 flex flex-col items-center justify-center gap-2">
                    <div className="h-6 w-6 rounded-full border-2 border-blue-600/20 border-t-blue-600 animate-spin" />
                    <span className="text-xs text-muted-foreground">Retrieving risk analysis audit logs...</span>
                  </div>
                ) : (
                  <div className="flex-1 space-y-6">
                    {/* Basic details summary banner */}
                    <div className="bg-muted/20 p-3 rounded-lg border border-border/40 flex items-center justify-between">
                      <div>
                        <h4 className="font-bold text-sm text-foreground">{projectDetail.name}</h4>
                        <p className="text-xs text-muted-foreground">PM: {projectDetail.PM} &bull; Client: {projectDetail.client}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                        projectDetail.status === "Red"
                          ? "bg-red-500/10 text-red-500"
                          : projectDetail.status === "Amber"
                          ? "bg-amber-500/10 text-amber-500"
                          : "bg-emerald-500/10 text-emerald-500"
                      }`}>
                        {projectDetail.status}
                      </span>
                    </div>

                    {/* LLM Narrative summary */}
                    <div className="bg-indigo-500/5 dark:bg-indigo-500/10 border border-indigo-500/10 rounded-xl p-4 space-y-2">
                      <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 font-bold text-xs">
                        <Sparkles className="h-4 w-4 shrink-0" />
                        <span>Generative Health Diagnosis Summary</span>
                      </div>
                      <p className="text-xs leading-relaxed text-muted-foreground">
                        {projectDetail.llmSummary}
                      </p>
                    </div>

                    {/* Milestone Timeline */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-muted-foreground">
                        <Calendar className="h-4 w-4 text-blue-500" />
                        <span>Delivery Milestone Timeline</span>
                      </div>
                      <div className="space-y-3 pl-2">
                        {projectDetail.timeline.map((mile, i) => {
                          const isDone = mile.status === "completed"
                          const isDelayed = mile.status === "delayed"
                          return (
                            <div key={i} className="flex gap-3 text-xs">
                              <div className="flex flex-col items-center">
                                <div className={`h-2.5 w-2.5 rounded-full mt-1 shrink-0 ${
                                  isDone ? "bg-emerald-500" : isDelayed ? "bg-red-500 animate-pulse" : "bg-border"
                                }`} />
                                {i < projectDetail.timeline.length - 1 && (
                                  <div className="w-0.5 bg-border flex-1 min-h-[20px]" />
                                )}
                              </div>
                              <div className="pb-2">
                                <h5 className="font-semibold text-foreground flex items-center gap-2">
                                  {mile.milestone}
                                  {mile.note && (
                                    <span className="text-[9px] font-bold px-1.5 py-0.2 bg-red-500/10 text-red-500 rounded">
                                      {mile.note}
                                    </span>
                                  )}
                                </h5>
                                <span className="text-[10px] text-muted-foreground block mt-0.5">{mile.date}</span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    {/* Key Recommendations list */}
                    <div className="space-y-2">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider font-sans">
                        AI Recommended Staff Adjustments
                      </span>
                      <div className="space-y-2 text-xs">
                        {projectDetail.recommendations.map((rec, idx) => (
                          <div key={idx} className="flex items-start gap-2.5 p-2.5 rounded-md border border-border bg-muted/10 font-sans leading-relaxed text-muted-foreground">
                            <Info className="h-4 w-4 text-indigo-500 shrink-0 mt-0.5" />
                            <span>{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Footer Controls */}
                <div className="pt-4 border-t border-border shrink-0 flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1 h-9 text-xs font-semibold text-muted-foreground hover:text-foreground"
                    onClick={() => setSelectedProjectId(null)}
                  >
                    Close Diagnostics
                  </Button>
                  {projectDetail && projectDetail.recommendedActions.map(act => (
                    <Link key={act.id} href={act.path} className="flex-1">
                      <Button
                        className="w-full h-9 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded"
                        onClick={() => setSelectedProjectId(null)}
                      >
                        {act.text}
                      </Button>
                    </Link>
                  ))}
                </div>
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>
      
    </div>
  )
}
