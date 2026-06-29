import { fetchAPI } from "./api"

export interface ProjectHealthSummary {
  project_id: string
  project_key?: string
  overall_health: string // Red, Amber, Green
  risk_score: number
  risk_level: string // Low, Medium, High, Critical
  // Enriched
  name?: string
  client?: string
  PM?: string
  staffCount?: number
  billability?: number
  utilization?: number
}

export interface ScheduleHealth {
  status: string
  delay_days: number
  days_remaining: number
  planned_duration: number
  actual_duration: number
  extension_count: number
}

export interface UtilizationHealth {
  average: number
  peak: number
  overallocated_count: number
  underutilized_count: number
  idle_capacity_percentage: number
  releasable_capacity_percentage: number
}

export interface BillabilityHealth {
  percentage: number
  billable_hours: number
  non_billable_hours: number
  shadow_resources_count: number
  billability_trend: string
  cost_recovery_status: string
}

export interface ProjectHealthDetail {
  project_id: string
  overall_health: string
  risk_score: number
  risk_level: string
  schedule: ScheduleHealth
  utilization: UtilizationHealth
  billability: BillabilityHealth
  recommended_actions: string[]
  explanation?: string
  // Enriched
  name?: string
  client?: string
  PM?: string
}

export const healthService = {
  async getProjectsHealth(): Promise<ProjectHealthSummary[]> {
    const [summaries, projects, utilizationStats, billabilityStats] = await Promise.all([
      fetchAPI<any[]>("/api/health/projects"),
      fetchAPI<any[]>("/api/projects?limit=100"),
      fetchAPI<any[]>("/api/health/utilization"),
      fetchAPI<any[]>("/api/health/billability")
    ])

    return summaries.map(s => {
      const matchProj = projects.find(p => p.project_id === s.project_id)
      const matchUtil = utilizationStats.find(u => u.project_id === s.project_id)
      const matchBill = billabilityStats.find(b => b.project_id === s.project_id)
      
      return {
        ...s,
        name: matchProj ? (matchProj.project_key || `Project ${matchProj.project_id}`) : "Active Delivery Contract",
        client: matchProj ? (matchProj.client_id || "Client Account") : "N/A",
        PM: matchProj ? (matchProj.reporter_id || "N/A") : "N/A",
        staffCount: matchUtil ? matchUtil.overallocated_count : 0,
        billability: matchBill ? Math.round(matchBill.billability_percentage) : 0,
        utilization: matchUtil ? Math.round(matchUtil.average_utilization) : 0
      }
    })
  },

  async getProjectHealthDetail(id: string): Promise<ProjectHealthDetail> {
    const [detail, projects] = await Promise.all([
      fetchAPI<ProjectHealthDetail>(`/api/health/projects/${id}`),
      fetchAPI<any[]>("/api/projects?limit=100")
    ])

    const matchProj = projects.find(p => p.project_id === id)
    return {
      ...detail,
      name: matchProj ? (matchProj.project_key || `Project ${matchProj.project_id}`) : "Active Delivery Contract",
      client: matchProj ? (matchProj.client_id || "Client Account") : "N/A",
      PM: matchProj ? (matchProj.reporter_id || "N/A") : "N/A"
    }
  },

  async syncAIProfiles(): Promise<any> {
    return fetchAPI<any>("/api/embeddings/generate", {
      method: "POST"
    })
  }
}
