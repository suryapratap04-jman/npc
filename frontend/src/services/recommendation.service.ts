import { fetchAPI } from "./api"

export interface RecommendationRequest {
  project_id?: string
  required_skills: string[]
  project_type?: string
  required_competencies?: string[]
  project_start_date?: string
  top_n: number
  strategy?: string
  
  // Redesigned and Connected Filters
  department?: string
  experience_range?: string
  availability_window?: string
  location?: string
  technology?: string
  domain?: string
}

export interface CandidateRecommendation {
  employee_id: string
  name: string
  email: string
  job_name: string
  department_name: string
  location: string
  experience_years: number
  skills: string[]
  competencies: string[]
  current_allocation: number
  availability_date: string
  current_project: string
  final_score: number
  rank: number
  confidence?: string
  why_recommended: string
  strengths: string[]
  potential_risks: string[]
  
  // Detailed scoring breakdown
  skill_match: number
  competency_match: number
  experience_score: number
  availability_score: number
  historical_score: number
  semantic_score: number
  
  category_scores?: Record<string, number>
  strategy_scores?: Record<string, number>
}

export interface ProjectDetail {
  project_id: string
  name: string
  client: string
  technology?: string
  domain?: string
  required_skills: string[]
  project_type: string
  expected_start_date: string
  demand: string
}

export interface RecommendationResponse {
  project?: ProjectDetail
  summary?: string
  candidates: CandidateRecommendation[]
  recommendations: CandidateRecommendation[] // Backwards compatibility
  explanation: string
  confidence?: string
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
  
  // Enriched pipeline details
  technology?: string
  domain?: string
  project_type?: string
  demand?: string
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
      skillset: p.skillset,
      
      // Map new project demand properties
      technology: p.solution || "N/A",
      domain: p.cluster || "N/A",
      project_type: p.request_type || "N/A",
      demand: p.resources_requested || "N/A"
    }))
  },

  async getRecommendations(req: RecommendationRequest): Promise<RecommendationResponse> {
    // Return fully enriched recommendation list from backend directement
    return await fetchAPI<RecommendationResponse>("/api/recommend/resources", {
      method: "POST",
      body: JSON.stringify(req)
    })
  }
}
