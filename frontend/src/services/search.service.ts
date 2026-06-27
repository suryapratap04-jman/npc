import { fetchAPI } from "./api"

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

    // Decouple checks based on active scopes
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

    const [empHits, projHits] = await Promise.all(promises)

    const mappedResults: SearchResultItem[] = []

    // Map Employees Qdrant payloads to UI Schema
    empHits.forEach((hit: VectorSearchHit) => {
      const p = hit.payload || {}
      mappedResults.push({
        id: String(hit.id || p.employee_id),
        name: p.name || `Employee ${hit.id}`,
        title: p.job_name || "Engineer",
        type: "Employee",
        subtitle: `${p.department_name || "Engineering"} CoE &bull; Location: ${p.location || "Remote"}`,
        details: `Skills matched: ${(p.skills || []).slice(0, 4).join(", ")}. Experience: ${p.experience_years || 4} years.`,
        similarity: hit.score,
        profile: {
          department: p.department_name || "Engineering",
          currentProject: p.current_project_id || "Bench / Unallocated",
          experience: p.experience_years || 4,
          availability: p.allocation_percentage ? (100 - p.allocation_percentage) : 100,
          skills: p.skills || [],
          competencies: p.competencies || []
        }
      })
    })

    // Map Projects Qdrant payloads to UI Schema
    projHits.forEach((hit: VectorSearchHit) => {
      const p = hit.payload || {}
      mappedResults.push({
        id: String(hit.id || p.id),
        name: p.name || `Project ${hit.id}`,
        title: p.client || "Client Project",
        type: "Project",
        subtitle: `Project Manager: ${p.project_manager || "Sarah Jenkins"} &bull; Client: ${p.client || "Delta"}`,
        details: `Duration: ${p.start_date || "2026-08"} to ${p.end_date || "2027-02"}. Status: ${p.project_status || "Active"}.`,
        similarity: hit.score,
        profile: {
          progress: p.project_status === "Active" ? 75 : 100,
          status: p.project_status === "Active" ? "Amber" : "Green",
          staffCount: 6,
          riskFactor: p.project_status === "Active" ? "Staff vacancy for critical role" : "On schedule"
        }
      })
    })

    // Sort by similarity score descending
    return mappedResults.sort((a, b) => b.similarity - a.similarity)
  }
}
