import { fetchAPI } from "./api"

export interface CapacityProjections {
  available_now: number
  available_30_days: number
  available_60_days: number
  available_90_days: number
}

export interface MonthlyProjection {
  month: string // YYYY-MM
  expected_project_volume: number
  headcount_demand: number
  skill_demand: Record<string, number>
  utilization_percentage: number
  capacity_surplus: number
  capacity_deficit: number
}

export interface SixMonthForecastResponse {
  monthly_projections: MonthlyProjection[]
  average_projected_utilization: number
  total_capacity_surplus: number
  total_capacity_deficit: number
  confidence_score: string
}

export interface CapacityStatusResponse {
  capacity_projections: CapacityProjections
  available_employees_by_role: Record<string, string[]>
  details: Record<string, any>
}

export interface HiringNeed {
  role: string
  count_needed: number
  priority: string
  reason: string
}

export interface HiringResponse {
  hiring_needs: HiringNeed[]
  summary: string
}

export interface RedeploymentOption {
  employee_id: string
  name?: string
  role: string
  current_project_id?: string
  project_end_date?: string
  available_from: string
  match_score: number
}

export interface RedeploymentResponse {
  redeployment_options: RedeploymentOption[]
  summary: string
}

export interface NewProjectDemandRequest {
  project_type: string
  expected_duration_months: number
  required_skills: string[]
  expected_start_date: string
  expected_team_size?: number
}

export interface NewProjectForecastResponse {
  project_type: string
  team_recommendation: Record<string, number>
  estimated_fte: number
  estimated_cost: number
  expected_duration: number
  capacity: CapacityProjections
  recommendation: {
    redeploy: string[]
    hire: string[]
  }
  confidence: string
  explanation?: string
}

export interface ComposedForecastData {
  summary: {
    totalDemand: number
    totalCapacity: number
    openHiring: number
    redeploymentReady: number
  }
  baselineForecast: Array<{
    month: string
    Capacity: number
    Demand: number
    Gap: number
  }>
  baselineGaps: Array<{
    role: string
    demand: number
    supply: number
    gap: number
    hiringNeeded: number
    redeploymentCandidates: number
  }>
  hiringStats: Array<{
    id: string
    role: string
    department: string
    status: string
    count: number
    priority: "High" | "Medium" | "Low"
  }>
  redeploymentStats: Array<{
    id: string
    name: string
    role: string
    rollOffDate: string
    sourceProject: string
    targetProject: string
    status: string
  }>
}

export const forecastService = {
  async getForecastOutlook(): Promise<ComposedForecastData> {
    const [sixMonth, capacity, hiring, redeployment] = await Promise.all([
      fetchAPI<SixMonthForecastResponse>("/api/forecast/six-month"),
      fetchAPI<CapacityStatusResponse>("/api/forecast/capacity"),
      fetchAPI<HiringResponse>("/api/forecast/hiring?project_type=AI&required_skills=React&required_skills=Python"),
      fetchAPI<RedeploymentResponse>("/api/forecast/redeployment?project_type=AI&required_skills=React&required_skills=Python")
    ])

    // Convert short month labels
    const baselineForecast = (sixMonth.monthly_projections || []).map(m => {
      const parts = m.month.split("-")
      const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
      const monthIdx = parts[1] ? parseInt(parts[1], 10) - 1 : 0
      const label = monthNames[monthIdx] || m.month
      
      return {
        month: label,
        Capacity: Math.round(m.headcount_demand + m.capacity_surplus),
        Demand: Math.round(m.headcount_demand),
        Gap: Math.round(m.capacity_deficit)
      }
    })

    // Compute gaps aggregated by role
    const baselineGaps = Object.entries(capacity.available_employees_by_role || {}).map(([role, list]) => {
      const neededCount = hiring.hiring_needs.find(n => n.role === role)?.count_needed || 0
      return {
        role,
        demand: list.length + neededCount,
        supply: list.length,
        gap: -neededCount,
        hiringNeeded: neededCount,
        redeploymentCandidates: redeployment.redeployment_options.filter(o => o.role === role).length
      }
    })

    const hiringStats = hiring.hiring_needs.map((h, idx) => ({
      id: `HIR-${idx + 1}`,
      role: h.role,
      department: "Engineering",
      status: h.priority === "High" ? "Sourcing" : "Sourcing",
      count: h.count_needed,
      priority: h.priority as "High" | "Medium" | "Low"
    }))

    const redeploymentStats = redeployment.redeployment_options.map((r, idx) => ({
      id: r.employee_id,
      name: r.name || `Resource ${r.employee_id}`,
      role: r.role,
      rollOffDate: r.project_end_date || "Jul 15, 2026",
      sourceProject: r.current_project_id || "CLI-115",
      targetProject: "CLI-201",
      status: "Match Score " + Math.round(r.match_score * 100) + "%"
    }))

    return {
      summary: {
        totalDemand: baselineForecast.reduce((acc, f) => acc + f.Demand, 0) / (baselineForecast.length || 1),
        totalCapacity: baselineForecast.reduce((acc, f) => acc + f.Capacity, 0) / (baselineForecast.length || 1),
        openHiring: hiring.hiring_needs.reduce((acc, h) => acc + h.count_needed, 0),
        redeploymentReady: redeployment.redeployment_options.length
      },
      baselineForecast,
      baselineGaps,
      hiringStats,
      redeploymentStats
    }
  },

  async runScenarioSimulation(req: NewProjectDemandRequest): Promise<NewProjectForecastResponse> {
    return fetchAPI<NewProjectForecastResponse>("/api/forecast/new-project", {
      method: "POST",
      body: JSON.stringify(req)
    })
  }
}
