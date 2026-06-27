import { fetchAPI } from "./api"

export interface RecommendationRequest {
  project_id?: string
  required_skills: string[]
  project_type?: string
  required_competencies?: string[]
  project_start_date?: string
  top_n: number
  strategy?: string
}

export interface CandidateRecommendation {
  employee_id: string
  job_name: string
  department_name: string
  final_score: float
  rank: int
  category_scores: Record<string, number>
  strategy_scores?: Record<string, number>
  confidence?: string
  availability_date: string
  utilization_percentage: number
  matching_skills: string[]
  // Extracted details
  name?: string
  skills?: string[]
  competencies?: string[]
  experience_years?: number
  email?: string
}

type float = number
type int = number

export interface RecommendationResponse {
  recommendations: CandidateRecommendation[]
  explanation: string
  processing_time_ms: number
  model_version: string
}

export interface ProjectSummary {
  id: string
  name: string
  client: string
  project_status: string
  project_manager: string
  start_date: string
  end_date: string
}

export const recommendationService = {
  async getProjects(): Promise<ProjectSummary[]> {
    const rawProjects = await fetchAPI<any[]>("/api/projects?limit=50")
    return rawProjects.map(p => ({
      id: p.project_id,
      name: p.project_key || `Project ${p.project_id}`,
      client: p.client_id || "Client Account",
      project_status: p.project_status || "Active",
      project_manager: p.reporter_id || "Sarah Jenkins",
      start_date: p.project_start_date || "2026-08-01",
      end_date: p.project_end_date || "2027-02-01"
    }))
  },

  async getRecommendations(req: RecommendationRequest): Promise<RecommendationResponse> {
    // 1. Fetch recommendations list
    const response = await fetchAPI<RecommendationResponse>("/api/recommend/resources", {
      method: "POST",
      body: JSON.stringify(req)
    })

    // 2. Fetch employee records to fill missing detail fields (like names, skills, etc.)
    const employees = await fetchAPI<any[]>("/api/employees?limit=100")

    // Map candidate names from the relational DB
    const enrichedRecommendations = response.recommendations.map(candidate => {
      const empMatch = employees.find(e => e.employee_id === candidate.employee_id)
      return {
        ...candidate,
        name: empMatch ? empMatch.name : `Resource ${candidate.employee_id}`,
        skills: empMatch ? empMatch.skills : candidate.matching_skills,
        competencies: empMatch ? empMatch.competencies : [],
        experience_years: empMatch ? empMatch.experience_years : 4,
        email: empMatch ? empMatch.email : `${candidate.employee_id}@company.com`
      }
    })

    return {
      ...response,
      recommendations: enrichedRecommendations
    }
  }
}
