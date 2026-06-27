import { fetchAPI } from "./api"
import { EmployeeModel, ProjectModel, PipelineModel } from "./dashboard.service"

export interface ReportColumn {
  header: string
  accessor: string
}

export interface ReportPreviewData {
  reportName: string
  category: string
  generatedDate: string
  author: string
  size: string
  rowCount: number
  columns: ReportColumn[]
  rows: any[]
}

export const reportsService = {
  async getReportPreviewData(category: string): Promise<ReportPreviewData> {
    let columns: ReportColumn[] = []
    let rows: any[] = []
    let size = "0 KB"
    let rowCount = 0

    if (category === "health") {
      columns = [
        { header: "Project ID", accessor: "id" },
        { header: "Project Name", accessor: "name" },
        { header: "Client Account", accessor: "client" },
        { header: "Lead Manager (PM)", accessor: "PM" },
        { header: "RAG Status", accessor: "status" }
      ]
      // Fetch live project status summaries
      const [projects, healthSummaries] = await Promise.all([
        fetchAPI<ProjectModel[]>("/api/projects?limit=50"),
        fetchAPI<any[]>("/api/health/projects")
      ])
      rows = healthSummaries.map((h: any) => {
        const match = projects.find(p => p.id === h.project_id)
        return {
          id: h.project_id,
          name: match ? match.name : "Active Delivery Contract",
          client: match ? match.client : "N/A",
          PM: match ? match.project_manager : "Sarah Jenkins",
          status: h.overall_health
        }
      })
      rowCount = rows.length
      size = `${(rowCount * 1.5).toFixed(1)} KB`
    } else if (category === "forecast") {
      columns = [
        { header: "Target Month", accessor: "month" },
        { header: "Headcount Supply (FTE)", accessor: "Capacity" },
        { header: "Pipeline Demand (FTE)", accessor: "Demand" },
        { header: "Calculated Gap (FTE)", accessor: "Gap" }
      ]
      // Fetch six-month forecasts
      const forecast = await fetchAPI<any>("/api/forecast/six-month")
      rows = (forecast.monthly_projections || []).map((m: any) => {
        return {
          month: m.month,
          Capacity: Math.round(m.headcount_demand + m.capacity_surplus),
          Demand: Math.round(m.headcount_demand),
          Gap: Math.round(m.capacity_deficit)
        }
      })
      rowCount = rows.length
      size = `${(rowCount * 1.2).toFixed(1)} KB`
    } else if (category === "recommendation") {
      columns = [
        { header: "Employee ID", accessor: "id" },
        { header: "Resource Name", accessor: "name" },
        { header: "Primary Competency Role", accessor: "role" },
        { header: "Department", accessor: "department" },
        { header: "Free Capacity (%)", accessor: "availability" }
      ]
      // Fetch employees list
      const employees = await fetchAPI<EmployeeModel[]>("/api/employees?limit=50")
      rows = employees.map(e => ({
        id: e.employee_id,
        name: e.name,
        role: e.job_name || "Engineer",
        department: e.department_name || "Engineering",
        availability: e.allocation_percentage ? (100 - e.allocation_percentage) : 100
      }))
      rowCount = rows.length
      size = `${(rowCount * 1.6).toFixed(1)} KB`
    } else {
      // hiring
      columns = [
        { header: "Deal ID", accessor: "id" },
        { header: "Client Account", accessor: "client" },
        { header: "Anticipated Project", accessor: "project" },
        { header: "Expected Size", accessor: "size" },
        { header: "Probability (%)", accessor: "probability" }
      ]
      // Fetch CRM pipelines deals
      const deals = await fetchAPI<PipelineModel[]>("/api/pipeline?limit=50")
      rows = deals.map(d => ({
        id: d.deal_id,
        client: d.client,
        project: d.project_name,
        size: `$${(d.estimated_value / 1000).toFixed(0)}K`,
        probability: `${Math.round(d.probability * 100)}%`
      }))
      rowCount = rows.length
      size = `${(rowCount * 1.1).toFixed(1)} KB`
    }

    const generatedDate = new Date().toLocaleString()

    return {
      reportName: `${category.toUpperCase()}_Status_Report_${Date.now().toString().slice(-4)}`,
      category,
      generatedDate,
      author: "Surya Pratap Singh",
      size,
      rowCount,
      columns,
      rows
    }
  }
}
