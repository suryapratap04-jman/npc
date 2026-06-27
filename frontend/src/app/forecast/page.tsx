"use client"

import React, { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import {
  Sparkles,
  TrendingUp,
  Users,
  Briefcase,
  GitCompare,
  ArrowRight,
  UserCheck,
  UserPlus,
  Activity,
  Calendar,
  Layers,
  ChevronRight,
  LineChart,
  AreaChart,
  BarChart3,
  Play,
  RotateCcw,
  AlertTriangle,
  ShieldAlert
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { forecastService } from "@/services/forecast.service"
import Loading from "@/app/loading"
import {
  ResponsiveContainer,
  AreaChart as RechartsAreaChart,
  Area,
  LineChart as RechartsLineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend
} from "recharts"

interface CapacityPoint {
  month: string
  Capacity: number
  Demand: number
  Gap: number
}

interface GapRecord {
  role: string
  demand: number
  supply: number
  gap: number
  hiringNeeded: number
  redeploymentCandidates: number
}

interface HiringItem {
  id: string
  role: string
  department: string
  status: string
  count: number
  priority: string
}

interface RedeploymentItem {
  id: string
  name: string
  role: string
  rollOffDate: string
  sourceProject: string
  targetProject: string
  status: string
}

interface ScenarioGapRecord {
  role: string
  gap: number
  type: string
}

interface Scenario {
  id: string
  name: string
  description: string
  impactSummary: string
  capacityChart: CapacityPoint[]
  gaps: ScenarioGapRecord[]
}

interface ForecastOutlookData {
  summary: {
    totalDemand: number
    totalCapacity: number
    openHiring: number
    redeploymentReady: number
  }
  baselineForecast: CapacityPoint[]
  baselineGaps: GapRecord[]
  hiringStats: HiringItem[]
  redeploymentStats: RedeploymentItem[]
  scenarios: Scenario[]
}

export default function ForecastPage() {
  const [mounted, setMounted] = useState(false)
  
  // Interactive Toggles
  const [chartType, setChartType] = useState<"area" | "line" | "bar">("area")
  const [activeScenarioId, setActiveScenarioId] = useState<string>("baseline")
  
  // Drill-down states
  const [selectedRole, setSelectedRole] = useState<string | null>(null)



  // Query forecast outlook
  const { data: rawForecast, isLoading: loading, error, refetch } = useQuery({
    queryKey: ["forecastOutlook"],
    queryFn: () => forecastService.getForecastOutlook()
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  if (loading || !rawForecast) {
    return <Loading />
  }

  if (error) {
    return (
      <div className="flex h-[70vh] w-full items-center justify-center flex-col gap-4 text-center px-4">
        <div className="h-12 w-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center border border-red-500/20">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-base">Failed to load Forecast data</h3>
          <p className="text-xs text-muted-foreground">The API server returned: {(error as any).detail || error.message}</p>
        </div>
        <Button onClick={() => refetch()} size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold h-8 px-4">
          Retry Connection
        </Button>
      </div>
    )
  }

  // Build the complete ForecastOutlookData with scenarios dynamically from rawForecast
  const data: ForecastOutlookData = {
    summary: rawForecast.summary,
    baselineForecast: rawForecast.baselineForecast,
    baselineGaps: rawForecast.baselineGaps,
    hiringStats: rawForecast.hiringStats,
    redeploymentStats: rawForecast.redeploymentStats,
    scenarios: [
      {
        id: "baseline",
        name: "Baseline Forecast",
        description: "Baseline capacity calculations based on active signed agreements and current headcount trends.",
        impactSummary: "Workforce demand aligns stable. Gaps resolve by late Q3 through organic hiring.",
        capacityChart: rawForecast.baselineForecast,
        gaps: rawForecast.baselineGaps.map(g => ({
          role: g.role,
          gap: g.gap,
          type: g.gap < 0 ? "Deficit" : g.gap > 0 ? "Surplus" : "Balanced"
        }))
      },
      {
        id: "delta-win",
        name: "Delta Retail Win (+15 Demand)",
        description: "Simulate Delta Retail signing the expansion agreement, raising Next.js and backend demand from April.",
        impactSummary: "Deficit in engineering roles increases by 4 FTEs. Critical hiring acceleration needed.",
        capacityChart: rawForecast.baselineForecast.map((f, i) => {
          const offset = i >= 3 ? 15 : 0
          return {
            ...f,
            Demand: Math.round(f.Demand + offset),
            Gap: Math.round(f.Capacity - (f.Demand + offset))
          }
        }),
        gaps: rawForecast.baselineGaps.map(g => {
          const isEng = g.role.includes("React") || g.role.includes("Node")
          const offset = isEng ? -2 : 0
          return {
            role: g.role,
            gap: g.gap + offset,
            type: (g.gap + offset) < 0 ? "Deficit" : (g.gap + offset) > 0 ? "Surplus" : "Balanced"
          }
        })
      },
      {
        id: "apex-pause",
        name: "Apex Database Pause (-10 Demand)",
        description: "Simulate Apex Logistics pausing database sync scope due to budget reassessments from April.",
        impactSummary: "DBA deficits resolved. AWS and Python specialists roll onto bench, increasing surplus.",
        capacityChart: rawForecast.baselineForecast.map((f, i) => {
          const offset = i >= 3 ? -10 : 0
          return {
            ...f,
            Demand: Math.round(Math.max(0, f.Demand + offset)),
            Gap: Math.round(f.Capacity - Math.max(0, f.Demand + offset))
          }
        }),
        gaps: rawForecast.baselineGaps.map(g => {
          const isDba = g.role.includes("Postgres") || g.role.includes("DBA")
          const offset = isDba ? 1 : 0
          return {
            role: g.role,
            gap: g.gap + offset,
            type: (g.gap + offset) < 0 ? "Deficit" : (g.gap + offset) > 0 ? "Surplus" : "Balanced"
          }
        })
      },
      {
        id: "optimize-util",
        name: "Utilization Optimize (+8% Cap)",
        description: "Simulate internal cross-training and overtime utilization raising effective capacity by 8%.",
        impactSummary: "Staff deficits bridged without onboarding costs. Average utilization hits 92%.",
        capacityChart: rawForecast.baselineForecast.map(f => {
          const newCap = Math.round(f.Capacity * 1.08)
          return {
            ...f,
            Capacity: newCap,
            Gap: Math.round(newCap - f.Demand)
          }
        }),
        gaps: rawForecast.baselineGaps.map(g => {
          const offset = g.gap < 0 ? 1 : 0
          return {
            role: g.role,
            gap: g.gap + offset,
            type: (g.gap + offset) < 0 ? "Deficit" : (g.gap + offset) > 0 ? "Surplus" : "Balanced"
          }
        })
      }
    ]
  }

  // Derived Scenario State
  const activeScenario = data.scenarios.find(s => s.id === activeScenarioId) || data.scenarios[0]
  const chartData = activeScenario.capacityChart
  const gapsData = activeScenario.gaps

  // Filter hiring and redeployments based on selected role drill-down
  const filteredHiring = selectedRole 
    ? data.hiringStats.filter(h => h.role === selectedRole)
    : data.hiringStats

  const filteredRedeployment = selectedRole
    ? data.redeploymentStats.filter(r => r.role === selectedRole)
    : data.redeploymentStats

  return (
    <div className="space-y-6 pb-12 font-sans text-foreground">
      
      {/* Page Header */}
      <div className="flex flex-col gap-1 md:flex-row md:items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Capacity & Demand Forecasting</h1>
          <p className="text-muted-foreground text-xs md:text-sm">
            Model pipeline scenarios, analyze resource gaps, and coordinate benched engineer redeployments.
          </p>
        </div>
        <div className="flex gap-2">
          {activeScenarioId !== "baseline" && (
            <Button
              variant="outline"
              size="xs"
              onClick={() => {
                setActiveScenarioId("baseline")
                setSelectedRole(null)
              }}
              className="flex items-center gap-1.5 text-xs rounded text-muted-foreground"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Reset Scenario
            </Button>
          )}
        </div>
      </div>

      {/* 1. Outlook KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 flex items-center justify-center shrink-0">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Active Contracts</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{data.summary.totalDemand} FTEs</span>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-indigo-500/10 text-indigo-500 flex items-center justify-center shrink-0">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Workforce Supply</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{data.summary.totalCapacity} Headcount</span>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 flex items-center justify-center shrink-0">
            <UserPlus className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Open Requisitions</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{data.summary.openHiring} Reqs</span>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <UserCheck className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground block">Bench Roll-offs</span>
            <span className="text-2xl font-bold font-sans mt-0.5">{data.summary.redeploymentReady} Ready</span>
          </div>
        </div>
      </div>

      {/* 2. Interactive What-If Scenario Workbench */}
      <div className="space-y-3">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <Sparkles className="h-4.5 w-4.5 text-indigo-500 dark:text-indigo-400 animate-pulse" />
          What-If Scenario Workbench
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data.scenarios.map(sc => {
            const isActive = sc.id === activeScenarioId
            return (
              <div
                key={sc.id}
                onClick={() => {
                  setActiveScenarioId(sc.id)
                  setSelectedRole(null)
                }}
                className={`rounded-xl border p-4 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer flex flex-col justify-between gap-3 ${
                  isActive 
                    ? "border-indigo-600 dark:border-indigo-400 bg-indigo-500/5 dark:bg-indigo-500/10 ring-1 ring-indigo-500/30" 
                    : "border-border bg-card"
                }`}
              >
                <div>
                  <h4 className="font-semibold text-xs text-foreground flex items-center gap-1.5 justify-between">
                    {sc.name}
                    {isActive && <Play className="h-3 w-3 text-indigo-500 dark:text-indigo-400 fill-indigo-500" />}
                  </h4>
                  <p className="text-[10px] text-muted-foreground mt-1.5 leading-relaxed">
                    {sc.description}
                  </p>
                </div>
                <div className="border-t border-border/50 pt-2 text-[9px] text-muted-foreground italic leading-snug">
                  Impact: <span className="text-foreground font-semibold">{sc.impactSummary}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 3. Main Forecast Chart & Resource Gap Drill-down */}
      <div className="grid gap-6 lg:grid-cols-3">
        
        {/* Forecast Chart Panel */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border pb-3 gap-2">
            <div>
              <h3 className="font-semibold text-sm text-foreground flex items-center gap-1.5">
                Monthly Supply & Demand Forecast
              </h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Modeling: <strong className="text-indigo-600 dark:text-indigo-400">{activeScenario.name}</strong>
              </p>
            </div>
            
            {/* Chart Type Toggler */}
            <div className="flex items-center gap-1 bg-muted/65 p-1 rounded-md border border-border/50 self-start shrink-0">
              <Button
                variant={chartType === "area" ? "secondary" : "ghost"}
                size="xs"
                onClick={() => setChartType("area")}
                className="h-6 gap-1 text-[10px] px-2 rounded-sm"
              >
                <AreaChart className="h-3 w-3" /> Area
              </Button>
              <Button
                variant={chartType === "line" ? "secondary" : "ghost"}
                size="xs"
                onClick={() => setChartType("line")}
                className="h-6 gap-1 text-[10px] px-2 rounded-sm"
              >
                <LineChart className="h-3 w-3" /> Line
              </Button>
              <Button
                variant={chartType === "bar" ? "secondary" : "ghost"}
                size="xs"
                onClick={() => setChartType("bar")}
                className="h-6 gap-1 text-[10px] px-2 rounded-sm"
              >
                <BarChart3 className="h-3 w-3" /> Bar
              </Button>
            </div>
          </div>

          <div className="w-full flex-1">
            {mounted ? (
              <ResponsiveContainer width="100%" height={260}>
                {chartType === "area" ? (
                  <RechartsAreaChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorCap" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorDem" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                    <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                    <RechartsTooltip contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", borderRadius: "8px", fontSize: "11px" }} />
                    <RechartsLegend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px", paddingTop: "10px" }} />
                    <Area type="monotone" dataKey="Capacity" stroke="#4f46e5" strokeWidth={2} fillOpacity={1} fill="url(#colorCap)" />
                    <Area type="monotone" dataKey="Demand" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorDem)" />
                  </RechartsAreaChart>
                ) : chartType === "line" ? (
                  <RechartsLineChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                    <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                    <RechartsTooltip contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", borderRadius: "8px", fontSize: "11px" }} />
                    <RechartsLegend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px", paddingTop: "10px" }} />
                    <Line type="monotone" dataKey="Capacity" stroke="#4f46e5" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                    <Line type="monotone" dataKey="Demand" stroke="#ef4444" strokeWidth={2.5} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </RechartsLineChart>
                ) : (
                  <RechartsBarChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                    <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: "10px", fill: "var(--muted-foreground)" }} />
                    <RechartsTooltip contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--border)", borderRadius: "8px", fontSize: "11px" }} />
                    <RechartsLegend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: "10px", paddingTop: "10px" }} />
                    <Bar dataKey="Capacity" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Demand" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </RechartsBarChart>
                )}
              </ResponsiveContainer>
            ) : (
              <div className="h-[260px] flex items-center justify-center text-muted-foreground text-xs">
                Loading capacity visualizer...
              </div>
            )}
          </div>
        </div>

        {/* Resource Gaps List with Drill-Down */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="border-b border-border pb-3 mb-4">
              <h3 className="font-semibold text-sm font-sans">Role Capacity Gaps</h3>
              <p className="text-[11px] text-muted-foreground font-sans mt-0.5">Click any role to drill down into hiring & redeployment status</p>
            </div>
            
            <div className="space-y-2.5">
              {gapsData.map((item, idx) => {
                const isDeficit = item.gap < 0
                const isSurplus = item.gap > 0
                const isSelected = selectedRole === item.role
                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedRole(isSelected ? null : item.role)}
                    className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center justify-between text-xs font-sans ${
                      isSelected 
                        ? "border-blue-600 bg-blue-50/5 dark:bg-blue-950/10 shadow-sm" 
                        : "border-border hover:bg-muted/30"
                    }`}
                  >
                    <div className="space-y-0.5">
                      <span className="font-semibold text-foreground">{item.role}</span>
                      <span className="text-[9px] text-muted-foreground block">
                        {isSelected ? "Click to collapse details" : "Click to view allocations"}
                      </span>
                    </div>

                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      isDeficit 
                        ? "bg-red-500/10 text-red-500" 
                        : isSurplus 
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" 
                        : "bg-muted text-muted-foreground"
                    }`}>
                      {isDeficit ? `${item.gap} FTE` : isSurplus ? `+${item.gap} FTE` : "Balanced"}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {selectedRole && (
            <div className="mt-4 pt-3.5 border-t border-border flex items-center justify-between shrink-0">
              <span className="text-[10px] text-muted-foreground">Drill-down: <strong className="text-foreground">{selectedRole}</strong></span>
              <Button 
                variant="outline" 
                size="xs"
                onClick={() => setSelectedRole(null)}
                className="h-6 text-[9px] rounded text-muted-foreground"
              >
                Clear Drill-down
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 4. Drill-Down Hiring and Redeployment details */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Hiring Pipeline */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <h3 className="font-semibold text-sm">Hiring & Onboarding Channels</h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                {selectedRole ? `Recruitment tracking for ${selectedRole}` : "Global open talent requisitions"}
              </p>
            </div>
            <span className="text-xs font-semibold text-yellow-600 dark:text-yellow-400 bg-yellow-500/10 px-2 py-0.5 rounded border border-yellow-500/10">
              {filteredHiring.length} Open Positions
            </span>
          </div>

          <div className="space-y-3.5">
            {filteredHiring.length > 0 ? (
              filteredHiring.map((hire) => (
                <div 
                  key={hire.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-border/80 bg-muted/10 hover:bg-muted/30 transition-all text-xs"
                >
                  <div className="space-y-0.5">
                    <h4 className="font-semibold text-foreground">{hire.role}</h4>
                    <p className="text-[10px] text-muted-foreground">Department: {hire.department} &bull; Candidates: {hire.count} in flow</p>
                  </div>
                  <div className="text-right space-y-1">
                    <span className="px-2 py-0.5 rounded bg-muted text-[10px] text-muted-foreground font-semibold border border-border/40">
                      {hire.status}
                    </span>
                    <span className="block text-[8px] text-muted-foreground uppercase font-bold tracking-wider">
                      Priority: {hire.priority}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-xs text-muted-foreground border border-dashed border-border rounded-lg">
                No active hiring paths match the selected drill-down.
              </div>
            )}
          </div>
        </div>

        {/* Redeployment Rotations */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <h3 className="font-semibold text-sm">Redeployment & Bench Rotations</h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                {selectedRole ? `Planned roll-offs for ${selectedRole}` : "Planned rotations from finishing contracts"}
              </p>
            </div>
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/10">
              {filteredRedeployment.length} Candidates Scheduled
            </span>
          </div>

          <div className="space-y-3.5">
            {filteredRedeployment.length > 0 ? (
              filteredRedeployment.map((red) => (
                <div 
                  key={red.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-border/80 bg-muted/10 hover:bg-muted/30 transition-all text-xs"
                >
                  <div className="space-y-0.5">
                    <h4 className="font-semibold text-foreground">{red.name}</h4>
                    <p className="text-[10px] text-muted-foreground">{red.role}</p>
                    <p className="text-[9px] text-muted-foreground/80 mt-1">
                      {red.sourceProject} &rarr; {red.targetProject}
                    </p>
                  </div>
                  <div className="text-right space-y-1">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-semibold">
                      {red.status}
                    </span>
                    <span className="block text-[8px] text-muted-foreground uppercase font-bold tracking-wider">
                      Roll-off: {red.rollOffDate}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-xs text-muted-foreground border border-dashed border-border rounded-lg">
                No planned bench rotations match the selected drill-down.
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
