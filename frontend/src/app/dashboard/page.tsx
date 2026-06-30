"use client"

import React, { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { dashboardService } from "@/services/dashboard.service"
import { healthService } from "@/services/health.service"
import Loading from "@/app/loading"
import Link from "next/link"
import { motion } from "framer-motion"
import {
  Sparkles,
  TrendingUp,
  ShieldAlert,
  UserCheck,
  Briefcase,
  AlertTriangle,
  Users,
  CheckCircle,
  Calendar,
  Clock,
  ArrowUpRight,
  ArrowRight,
  Database,
  Search,
  Plus,
  Info,
  Activity,
  Flame,
  FileSpreadsheet
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts"

interface KPICard {
  id: string
  title: string
  value: string
  change: string
  status: string
  detail: string
  color: string
}

interface ProjectHealth {
  id: string
  name: string
  client: string
  status: string
  progress: number
  PM: string
  staffCount: number
  riskDetail: string
}

interface Availability {
  id: string
  name: string
  skill: string
  project: string
  date: string
  daysRemaining: number
}

interface PipelineDeal {
  id: string
  client: string
  project: string
  start: string
  probability: string
  size: string
  roles: string[]
}

interface ActivityLog {
  id: string
  time: string
  category: string
  text: string
}

interface AIAction {
  id: string
  title: string
  description: string
  type: string
  path: string
}

interface CapacityPoint {
  month: string
  Supply: number
  Demand: number
  Pipeline: number
}

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["dashboardData"],
    queryFn: () => dashboardService.getDashboardData(),
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  if (isLoading || !data) {
    return <Loading />
  }

  if (error) {
    return (
      <div className="flex h-[70vh] w-full items-center justify-center flex-col gap-4 text-center px-4">
        <div className="h-12 w-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center border border-red-500/20">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-base">Failed to load Dashboard data</h3>
          <p className="text-xs text-muted-foreground">The API server returned: {(error as any).detail || error.message}</p>
        </div>
        <Button onClick={() => refetch()} size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold h-8 px-4">
          Retry Connection
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      
      {/* 1. Welcome Header */}
      <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground font-sans">
            Decision Intelligence Center
          </h1>
          <p className="text-muted-foreground text-xs md:text-sm font-sans">
            Here is what is happening across the organization today, June 27, 2026.
          </p>
        </div>
        <div className="flex items-center gap-2 mt-2 md:mt-0">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            Data Sync: Active
          </span>
          <Button
            variant="outline"
            size="xs"
            onClick={async () => {
              try {
                await healthService.syncAIProfiles()
                alert("Vector Database trigger indexing completed successfully.")
              } catch (e: any) {
                alert(`Failed to synchronize embeddings: ${e.detail || e.message}`)
              }
            }}
            className="flex items-center gap-1.5 text-xs text-muted-foreground"
          >
            <Database className="h-3.5 w-3.5" />
            Sync AI Profiles
          </Button>
        </div>
      </div>

      {/* 2. Today's AI Summary */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-indigo-500/10 dark:border-indigo-400/15 bg-gradient-to-r from-violet-500/5 to-indigo-500/5 dark:from-violet-500/10 dark:to-indigo-500/10 p-5 shadow-sm"
      >
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-4.5 w-4.5 text-indigo-500 dark:text-indigo-400" />
          <span className="font-semibold text-sm text-indigo-600 dark:text-indigo-400 font-sans tracking-wide">
            Today's AI Summary
          </span>
        </div>
        <p className="text-sm leading-relaxed text-foreground/90 font-sans">
          {data.aiSummary}
        </p>
      </motion.div>

      {/* 3. KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {data.kpiCards.map((card, idx) => {
          const isRed = card.color === "red"
          const isGreen = card.color === "green"
          const isYellow = card.color === "yellow"
          return (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow-md transition-all duration-200 group cursor-pointer"
            >
              <div className="flex items-center justify-between pb-2">
                <span className="text-xs font-semibold text-muted-foreground font-sans uppercase tracking-wider">
                  {card.title}
                </span>
                {isRed && <ShieldAlert className="h-4 w-4 text-red-500" />}
                {isGreen && <UserCheck className="h-4 w-4 text-emerald-500" />}
                {isYellow && <Briefcase className="h-4 w-4 text-yellow-500" />}
                {card.color === "blue" && <TrendingUp className="h-4 w-4 text-blue-500" />}
              </div>
              <div className="text-2xl font-bold font-sans tracking-tight text-foreground">
                {card.value && card.value !== "N/A" && card.value !== "" ? card.value : "Insufficient Data"}
              </div>
              <div className="flex items-center justify-between mt-1 text-[11px] font-sans">
                <span className={`font-semibold ${
                  isRed ? "text-red-500" : isGreen ? "text-emerald-500" : isYellow ? "text-yellow-600 dark:text-yellow-400" : "text-blue-500"
                }`}>
                  {card.change}
                </span>
                <span className="text-muted-foreground">{card.detail}</span>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* 4. Main Charts and AI Action Suggestions */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Current Capacity (2 columns) */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
            <div>
              <h3 className="font-semibold text-sm text-foreground font-sans">Current Capacity Planning</h3>
              <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Supply capacity vs. pipeline contract demands (FTEs)</p>
            </div>
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1">
              <TrendingUp className="h-3.5 w-3.5" /> 6 Month Outlook
            </span>
          </div>

          <div className="w-full flex-1">
            {mounted && data.capacityChart && data.capacityChart.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={data.capacityChart} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorSupply" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorPipeline" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                  <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)", fontFamily: "sans-serif" }} />
                  <YAxis tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)", fontFamily: "sans-serif" }} />
                  <Tooltip 
                    formatter={(value: any, name: any) => [`${Math.round(value)} FTE`, name]}
                    contentStyle={{ 
                      backgroundColor: "var(--card)", 
                      borderColor: "var(--border)",
                      borderRadius: "8px", 
                      fontSize: "11px",
                      fontFamily: "sans-serif",
                      boxShadow: "0 10px 15px -3px rgba(0,0,0,0.1)"
                    }}
                  />
                  <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px", fontFamily: "sans-serif", paddingTop: "10px" }} />
                  <Area type="monotone" dataKey="Supply" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#colorSupply)" />
                  <Area type="monotone" dataKey="Demand" stroke="#2563eb" strokeWidth={2} fillOpacity={1} fill="url(#colorDemand)" />
                  <Area type="monotone" dataKey="Pipeline" stroke="#10b981" strokeWidth={2} strokeDasharray="4 4" fillOpacity={1} fill="url(#colorPipeline)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[260px] flex items-center justify-center text-muted-foreground text-xs font-sans bg-muted/5 border border-dashed border-border rounded-lg">
                Insufficient Data
              </div>
            )}
          </div>
        </div>

        {/* Suggested AI Actions (1 column) */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col">
          <div className="flex items-center gap-2 border-b border-border pb-3 mb-4">
            <Sparkles className="h-4.5 w-4.5 text-indigo-500 dark:text-indigo-400" />
            <h3 className="font-semibold text-sm text-foreground font-sans">Suggested AI Actions</h3>
          </div>
          <div className="flex-1 space-y-3.5">
            {data.aiActions.map((action) => {
              const isHiring = action.type === "hiring"
              const isAllocation = action.type === "allocation"
              return (
                <div 
                  key={action.id}
                  className="rounded-lg border border-border/80 bg-muted/20 p-3 hover:bg-muted/40 transition-all flex flex-col gap-2 relative group"
                >
                  <div>
                    <h4 className="font-semibold text-xs text-foreground font-sans flex items-center gap-1.5">
                      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                        isHiring ? "bg-yellow-500" : isAllocation ? "bg-red-500" : "bg-blue-500"
                      }`} />
                      {action.title}
                    </h4>
                    <p className="text-[10px] text-muted-foreground font-sans leading-relaxed mt-1">
                      {action.description}
                    </p>
                  </div>
                  <div className="flex justify-end mt-1">
                    <Link href={action.path}>
                      <Button variant="outline" size="xs" className="h-6 gap-1 text-[10px] font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300">
                        {isAllocation ? "Match Resource" : isHiring ? "Initiate Hiring" : "View Details"}
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* 5. Project Health & Upcoming Availability Timeline */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Project Health (2 columns) */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
            <div>
              <h3 className="font-semibold text-sm text-foreground font-sans">Active Project Health</h3>
              <p className="text-[11px] text-muted-foreground font-sans mt-0.5">RAG status tracking and scope progress indicators</p>
            </div>
            <Link href="/project-health">
              <span className="text-xs font-semibold text-muted-foreground hover:text-foreground cursor-pointer flex items-center gap-1">
                View all health audits <ArrowUpRight className="h-3 w-3" />
              </span>
            </Link>
          </div>

          <div className="space-y-3.5">
            {data.projectHealth && data.projectHealth.length > 0 ? (
              data.projectHealth.map((project) => {
                const isRed = project.status === "Red"
                const isAmber = project.status === "Amber"
                return (
                  <div 
                    key={project.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg border border-border/80 bg-muted/10 hover:bg-muted/30 transition-all"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-foreground font-sans">{project.name}</span>
                        <span className="text-[10px] text-muted-foreground font-sans font-medium">({project.client})</span>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide ${
                          isRed 
                            ? "bg-red-500/10 text-red-500" 
                            : isAmber 
                            ? "bg-amber-500/10 text-amber-500" 
                            : "bg-emerald-500/10 text-emerald-500"
                        }`}>
                          {project.status}
                        </span>
                      </div>
                      <p className="text-[10px] text-muted-foreground font-sans">
                        PM: <span className="text-foreground">{project.PM}</span> &bull; Allocated FTEs: <span className="text-foreground">{project.staffCount}</span>
                      </p>
                    </div>

                    <div className="flex items-center gap-4 shrink-0 sm:w-64">
                      <div className="flex-1 space-y-1">
                        <div className="flex justify-between text-[10px] font-semibold text-muted-foreground font-sans">
                          <span>Progress</span>
                          <span className="text-foreground">{project.progress}%</span>
                        </div>
                        <div className="w-full bg-border rounded-full h-1.5 overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${
                              isRed ? "bg-red-500" : isAmber ? "bg-amber-500" : "bg-emerald-500"
                            }`}
                            style={{ width: `${project.progress}%` }}
                          />
                        </div>
                      </div>
                      
                      {isRed ? (
                        <Link href={`/recommendation?project=${project.id}`}>
                          <Button variant="outline" size="xs" className="h-7 border-red-500/20 text-red-500 hover:bg-red-500/5 font-semibold text-[10px]">
                            Resolve Gap
                          </Button>
                        </Link>
                      ) : (
                        <div className="w-20 text-right text-[10px] font-semibold text-muted-foreground truncate font-sans">
                          {project.riskDetail}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="py-12 flex items-center justify-center text-muted-foreground text-xs font-sans bg-muted/5 border border-dashed border-border rounded-lg">
                Insufficient Data
              </div>
            )}
          </div>
        </div>

        {/* Upcoming Availability Timeline (1 column) */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 border-b border-border pb-3 mb-4">
              <Calendar className="h-4.5 w-4.5 text-blue-500" />
              <h3 className="font-semibold text-sm text-foreground font-sans">Upcoming Bench Roll-offs</h3>
            </div>
            <div className="space-y-3.5">
              {data.availabilityTimeline && data.availabilityTimeline.length > 0 ? (
                data.availabilityTimeline.map((item) => {
                  const isNear = item.daysRemaining <= 10
                  return (
                    <div 
                      key={item.id}
                      className="flex justify-between items-start gap-2 text-xs font-sans pb-3.5 border-b border-border/40 last:border-b-0 last:pb-0"
                    >
                      <div>
                        <h4 className="font-semibold text-foreground">{item.name}</h4>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{item.skill}</p>
                        <p className="text-[9px] text-muted-foreground/80 mt-1">
                          Currently: {item.project} &bull; Roll-off: {item.date}
                        </p>
                      </div>
                      <span className={`shrink-0 px-2 py-0.5 rounded-full text-[9px] font-bold ${
                        isNear 
                          ? "bg-red-500/10 text-red-500" 
                          : "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                      }`}>
                        {item.daysRemaining} days left
                      </span>
                    </div>
                  )
                })
              ) : (
                <div className="py-12 flex items-center justify-center text-muted-foreground text-xs font-sans bg-muted/5 border border-dashed border-border rounded-lg">
                  Insufficient Data
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-border/60">
            <Link href="/recommendation">
              <Button className="w-full text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-md h-8">
                Optimize Bench Staffing
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* 6. Pipeline & Recent Activities */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* CRM Pipeline (2 columns) */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
            <div>
              <h3 className="font-semibold text-sm text-foreground font-sans">CRM Pipeline Sync</h3>
              <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Incoming sales contracts and anticipated staffing needs</p>
            </div>
            <span className="text-xs text-muted-foreground font-sans font-medium">Synced: 1 hr ago</span>
          </div>

          <div className="space-y-3.5">
            {data.pipelineDeals && data.pipelineDeals.length > 0 ? (
              data.pipelineDeals.map((deal) => (
                <div 
                  key={deal.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg border border-border/80 bg-muted/5 hover:bg-muted/15 transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-xs text-foreground font-sans">{deal.project}</span>
                      <span className="text-[10px] text-muted-foreground font-sans font-medium">({deal.client})</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {deal.roles.map((r, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-muted text-[9px] text-muted-foreground font-medium border border-border/40">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between sm:justify-end gap-6 text-xs font-sans shrink-0">
                    <div className="text-left sm:text-right">
                      <p className="text-[9px] text-muted-foreground uppercase tracking-wider font-semibold">Deal Size</p>
                      <p className="font-semibold text-foreground mt-0.5">{deal.size}</p>
                    </div>
                    <div className="text-left sm:text-right">
                      <p className="text-[9px] text-muted-foreground uppercase tracking-wider font-semibold">Probability</p>
                      <p className="font-semibold text-emerald-500 mt-0.5">{deal.probability}</p>
                    </div>
                    <div className="text-left sm:text-right">
                      <p className="text-[9px] text-muted-foreground uppercase tracking-wider font-semibold">Start Month</p>
                      <p className="font-semibold text-foreground mt-0.5">{deal.start}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 flex items-center justify-center text-muted-foreground text-xs font-sans bg-muted/5 border border-dashed border-border rounded-lg">
                Insufficient Data
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity Log (1 column) */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 border-b border-border pb-3 mb-4">
              <Activity className="h-4.5 w-4.5 text-blue-500" />
              <h3 className="font-semibold text-sm text-foreground font-sans">Recent Activity</h3>
            </div>
            <div className="space-y-4">
              {data.recentActivity && data.recentActivity.length > 0 ? (
                data.recentActivity.map((log) => {
                  const isRisk = log.category === "risk"
                  const isAlloc = log.category === "allocation"
                  return (
                    <div key={log.id} className="flex gap-3 text-xs font-sans">
                      <div className="mt-0.5 shrink-0">
                        <div className={`h-2 w-2 rounded-full mt-1.5 ${
                          isRisk ? "bg-red-500" : isAlloc ? "bg-blue-500" : "bg-muted-foreground"
                        }`} />
                      </div>
                      <div>
                        <p className="text-foreground leading-normal">{log.text}</p>
                        <span className="text-[10px] text-muted-foreground font-medium block mt-1">{log.time}</span>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="py-12 flex items-center justify-center text-muted-foreground text-xs font-sans bg-muted/5 border border-dashed border-border rounded-lg">
                  Insufficient Data
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-border/60">
            <Button 
              variant="outline" 
              className="w-full text-xs font-semibold rounded-md h-8 text-muted-foreground hover:text-foreground"
              onClick={() => alert("Simulation: Historical logs exported successfully.")}
            >
              Export Activity Logs
            </Button>
          </div>
        </div>
      </div>

    </div>
  )
}
