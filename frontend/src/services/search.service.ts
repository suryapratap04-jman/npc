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
        }).catch(err => {
          console.error("Employee search failed:", err)
          return []
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
        }).catch(err => {
          console.error("Project search failed:", err)
          return []
        })
      )
    } else {
      promises.push(Promise.resolve([]))
    }

    // Parallel fetch employees list & projects list from relational DB for enrichment
    const [empHits, projHits, rawEmployees, rawProjects] = await Promise.all([
      promises[0],
      promises[1],
      fetchAPI<any[]>("/api/employees?limit=100").catch(() => []),
      fetchAPI<any[]>("/api/projects?limit=100").catch(() => [])
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
        title: p.job_name || empMatch?.job_name || "Engineer",
        type: "Employee",
        subtitle: `${p.department_name || empMatch?.department_name || "Engineering"} CoE &bull; Location: ${p.location || empMatch?.location || "Remote"}`,
        details: `Skills matched: ${(p.skills || empMatch?.skills || []).slice(0, 4).join(", ")}. Experience: ${empMatch?.experience_years || 4} years.`,
        similarity: hit.score,
        profile: {
          department: p.department_name || empMatch?.department_name || "Engineering",
          currentProject: empMatch?.current_project_id ? (rawProjects.find(pr => pr.project_id === empMatch.current_project_id)?.project_key || empMatch.current_project_id) : "Bench / Unallocated",
          experience: empMatch?.experience_years || 4,
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
      
      mappedResults.push({
        id: projId,
        name: p.name || projMatch?.project_key || `Project ${projId}`,
        title: p.client || projMatch?.client_id || "Client Project",
        type: "Project",
        subtitle: `Project Manager: ${p.project_manager || projMatch?.reporter_id || "Sarah Jenkins"} &bull; Client: ${p.client || projMatch?.client_id || "Delta"}`,
        details: `Duration: ${p.start_date || projMatch?.project_start_date || "2026-08"} to ${p.end_date || projMatch?.project_end_date || "2027-02"}. Status: ${p.project_status || projMatch?.project_status || "Active"}.`,
        similarity: hit.score,
        profile: {
          progress: (p.project_status || projMatch?.project_status) === "Active" ? 75 : 100,
          status: (p.project_status || projMatch?.project_status) === "Active" ? "Amber" : "Green",
          staffCount: 6,
          riskFactor: (p.project_status || projMatch?.project_status) === "Active" ? "Staff vacancy for critical role" : "On schedule"
        }
      })
    })

    // Sort by similarity score descending
    return mappedResults.sort((a, b) => b.similarity - a.similarity)
  }
}
