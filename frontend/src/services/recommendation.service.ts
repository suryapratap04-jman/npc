import { fetchAPI } from "./api"
import { getEmployeeName } from "./dashboard.service"

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
  skillset?: string
}

export const recommendationService = {
  async getProjects(): Promise<ProjectSummary[]> {
    const rawPipeline = await fetchAPI<any[]>("/api/pipeline?limit=100")
    // Filter to only include pipeline deals that have a non-empty skillset
    const filteredPipeline = rawPipeline.filter(p => p.skillset && p.skillset.trim().length > 0)
    
    return filteredPipeline.map(p => ({
      id: String(p.id),
      name: `${p.client || "N/A"} - ${p.solution || "N/A"} (Priority: ${p.priority || "N/A"})`,
      client: p.client || "N/A",
      project_status: p.status || "N/A",
      project_manager: p.em || "N/A",
      start_date: p.likely_start_date || "N/A",
      end_date: "N/A",
      skillset: p.skillset
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
        name: getEmployeeName(candidate.employee_id),
        skills: empMatch && empMatch.skills && empMatch.skills.length > 0 ? empMatch.skills : candidate.matching_skills,
        competencies: empMatch && empMatch.competencies ? empMatch.competencies : [],
        experience_years: empMatch && empMatch.experience_years ? empMatch.experience_years : 4,
        email: empMatch && empMatch.email ? empMatch.email : `${candidate.employee_id}@company.com`
      }
    })

    return {
      ...response,
      recommendations: enrichedRecommendations
    }
  }
}
