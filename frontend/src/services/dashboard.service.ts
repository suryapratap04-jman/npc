import { fetchAPI } from "./api"

export function getEmployeeName(id: string): string {
  return id
}

// TypeScript interfaces matching backend models
export interface EmployeeModel {
  employee_id: string
  name: string
  location: string
  job_name: string
  department_name: string
  current_project_id: string | null
  allocation_percentage: number
  skills: string[]
  competencies: string[]
  experience_years: number
}

export interface ProjectModel {
  id: string
  name: string
  client: string
  project_status: string
  project_manager: string
  start_date: string
  end_date: string
}

export interface PipelineModel {
  deal_id: string
  client: string
  project_name: string
  estimated_value: number
  probability: number
  expected_start_date: string
  roles_needed: string[]
  notes?: string
}

export interface ComposedDashboardData {
  aiSummary: string
  kpiCards: Array<{
    id: string
    title: string
    value: string
    change: string
    status: "good" | "bad" | "neutral" | "warning"
    detail: string
    color: string
  }>
  capacityChart: Array<{
    month: string
    Supply: number
    Demand: number
    Pipeline: number
  }>
  projectHealth: Array<{
    id: string
    name: string
    client: string
    status: string
    progress: number
    PM: string
    staffCount: number
    riskDetail: string
  }>
  availabilityTimeline: Array<{
    id: string
    name: string
    skill: string
    project: string
    date: string
    daysRemaining: number
  }>
  pipelineDeals: Array<{
    id: string
    client: string
    project: string
    start: string
    probability: string
    size: string
    roles: string[]
  }>
  recentActivity: Array<{
    id: string
    time: string
    category: string
    text: string
  }>
  aiActions: Array<{
    id: string
    title: string
    description: string
    type: string
    path: string
  }>
}

export const dashboardService = {
  async getDashboardData(): Promise<ComposedDashboardData> {
    return fetchAPI<ComposedDashboardData>("/api/dashboard/overview")
  }
}
