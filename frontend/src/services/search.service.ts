import { fetchAPI } from "./api"
import { getEmployeeName } from "./dashboard.service"

export interface SearchResultItem {
  id: string
  name: string
  title: string
  type: "Employee" | "Project" | "Skill" | "Pipeline"
  subtitle: string
  details: string
  similarity: number
  profile: any
}

export interface SearchRequest {
  query: string
  limit?: number
}

interface VectorSearchHit {
  id: string | number
  score: number
  payload: Record<string, any>
}

export const searchService = {
  async searchAll(query: string, category: string = "all"): Promise<SearchResultItem[]> {
    if (!query.trim()) return []

    const limit = 10
    const promises: Promise<any[]>[] = []

    const includeEmployees = category === "all" || category === "employee"
    const includeProjects = category === "all" || category === "project"

    if (includeEmployees) {
      promises.push(
        fetchAPI<VectorSearchHit[]>("/api/search/employees", {
          method: "POST",
          body: JSON.stringify({ query, limit })
        })
      )
    } else {
      promises.push(Promise.resolve([]))
    }

    if (includeProjects) {
      promises.push(
        fetchAPI<VectorSearchHit[]>("/api/search/projects", {
          method: "POST",
          body: JSON.stringify({ query, limit })
        })
      )
    } else {
      promises.push(Promise.resolve([]))
    }

    // Parallel fetch employees list & projects list from relational DB for enrichment
    const [empHits, projHits, rawEmployees, rawProjects] = await Promise.all([
      promises[0],
      promises[1],
      fetchAPI<any[]>("/api/employees?limit=100"),
      fetchAPI<any[]>("/api/projects?limit=100")
    ])

    const mappedResults: SearchResultItem[] = []

    // Map Employees Qdrant payloads to UI Schema
    empHits.forEach((hit: VectorSearchHit) => {
      const p = hit.payload || {}
      const empId = String(hit.id || p.employee_id)
      const empMatch = rawEmployees.find(e => e.employee_id === empId)
      
      mappedResults.push({
        id: empId,
        name: getEmployeeName(empId),
        title: p.job_name || empMatch?.job_name || "N/A",
        type: "Employee",
        subtitle: `${p.department_name || empMatch?.department_name || "N/A"} CoE &bull; Location: ${p.location || empMatch?.location || "N/A"}`,
        details: `Skills matched: ${(p.skills || empMatch?.skills || []).slice(0, 4).join(", ")}. Experience: ${empMatch?.experience_years || 0} years.`,
        similarity: hit.score,
        profile: {
          department: p.department_name || empMatch?.department_name || "N/A",
          currentProject: empMatch?.current_project_id ? (rawProjects.find(pr => pr.project_id === empMatch.current_project_id)?.project_key || empMatch.current_project_id) : "Bench / Unallocated",
          experience: empMatch?.experience_years || 0,
          availability: empMatch?.allocation_percentage ? (100 - empMatch.allocation_percentage) : 100,
          skills: p.skills || empMatch?.skills || [],
          competencies: empMatch?.competencies || []
        }
      })
    })

    // Map Projects Qdrant payloads to UI Schema
    projHits.forEach((hit: VectorSearchHit) => {
      const p = hit.payload || {}
      const projId = String(hit.id || p.id)
      const projMatch = rawProjects.find(pr => pr.project_id === projId)
      const allocatedEmployeesCount = rawEmployees.filter(e => e.current_project_id === projId).length
      
      mappedResults.push({
        id: projId,
        name: p.name || projMatch?.project_key || `Project ${projId}`,
        title: p.client || projMatch?.client_id || "N/A",
        type: "Project",
        subtitle: `Project Manager: ${p.project_manager || projMatch?.reporter_id || "N/A"} &bull; Client: ${p.client || projMatch?.client_id || "N/A"}`,
        details: `Duration: ${p.start_date || projMatch?.project_start_date || "N/A"} to ${p.end_date || projMatch?.project_end_date || "N/A"}. Status: ${p.project_status || projMatch?.project_status || "N/A"}.`,
        similarity: hit.score,
        profile: {
          progress: 100,
          status: "Green",
          staffCount: allocatedEmployeesCount,
          riskFactor: "On schedule"
        }
      })
    })

    // Sort by similarity score descending
    return mappedResults.sort((a, b) => b.similarity - a.similarity)
  }
}
