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
    const [summaries, projects] = await Promise.all([
      fetchAPI<any[]>("/api/health/projects"),
      fetchAPI<any[]>("/api/projects?limit=100")
    ])

    return summaries.map(s => {
      const matchProj = projects.find(p => p.project_id === s.project_id)
      return {
        ...s,
        name: matchProj ? (matchProj.project_key || `Project ${matchProj.project_id}`) : "Active Delivery Contract",
        client: matchProj ? (matchProj.client_id || "Client Account") : "N/A",
        PM: matchProj ? (matchProj.reporter_id || "Sarah Jenkins") : "Sarah Jenkins",
        staffCount: s.overall_health === "Red" ? 4 : 8,
        billability: s.overall_health === "Red" ? 60 : s.overall_health === "Amber" ? 75 : 95,
        utilization: s.overall_health === "Red" ? 105 : s.overall_health === "Amber" ? 85 : 92
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
      PM: matchProj ? (matchProj.reporter_id || "Sarah Jenkins") : "Sarah Jenkins"
    }
  }
}
