"use client"

import React, { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  FileText,
  FileSpreadsheet,
  Download,
  Search,
  Sparkles,
  Info,
  Calendar,
  CheckCircle,
  FileDown,
  RotateCcw,
  Clock,
  Briefcase,
  ShieldAlert
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { useToastStore } from "@/store/useToastStore"
import { reportService } from "@/services/report.service"
import Loading from "@/app/loading"

interface ReportColumn {
  header: string
  accessor: string
}

interface ReportPreview {
  reportName: string
  category: string
  generatedDate: string
  author: string
  size: string
  rowCount: number
  columns: ReportColumn[]
  rows: any[]
}

export default function ReportsPage() {
  const addToast = useToastStore(s => s.addToast)
  
  // Parameter states
  const [category, setCategory] = useState("health")
  const [format, setFormat] = useState("pdf")
  
  // Data states
  const [filterQuery, setFilterQuery] = useState("")
  
  // Progress states
  const [isCompiling, setIsCompiling] = useState(false)
  const [compileProgress, setCompileProgress] = useState(0)

  // Query report preview data
  const { data: preview, isLoading: loading, error, refetch } = useQuery<ReportPreview>({
    queryKey: ["reportPreview", category],
    queryFn: () => reportService.getReportPreviewData(category)
  })

  const handleGeneratePreview = () => {
    refetch()
  }

  const handleDownload = () => {
    if (!preview) return

    setIsCompiling(true)
    setCompileProgress(0)

    // Simulate compilation progress timer
    const interval = setInterval(() => {
      setCompileProgress(prev => {
        if (prev < 100) {
          return prev + 10
        } else {
          clearInterval(interval)
          setTimeout(() => {
            setIsCompiling(false)
            
            // Trigger a simulated file download of report rows
            const csvContent = "data:text/csv;charset=utf-8," 
              + preview.columns.map(c => c.header).join(",") + "\n"
              + preview.rows.map(r => preview.columns.map(c => r[c.accessor]).join(",")).join("\n")
            
            const encodedUri = encodeURI(csvContent)
            const link = document.createElement("a")
            link.setAttribute("href", encodedUri)
            link.setAttribute("download", `${preview.reportName}.${format}`)
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)

            addToast(`Successfully compiled and downloaded ${preview.reportName}.${format}`, "success")
          }, 300)
          return 100
        }
      })
    }, 150)
  }

  if (error) {
    return (
      <div className="flex h-[70vh] w-full items-center justify-center flex-col gap-4 text-center px-4">
        <div className="h-12 w-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center border border-red-500/20">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-base">Failed to load Report data</h3>
          <p className="text-xs text-muted-foreground font-sans">The API server returned: {(error as any).detail || error.message}</p>
        </div>
        <Button onClick={() => refetch()} size="sm" className="bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold h-8 px-4">
          Retry Preview
        </Button>
      </div>
    )
  }

  // Filter rows based on search query
  const filteredRows = preview
    ? preview.rows.filter(row =>
        preview.columns.some(col => {
          const val = row[col.accessor]
          return val !== undefined && val.toString().toLowerCase().includes(filterQuery.toLowerCase())
        })
      )
    : []

  return (
    <div className="space-y-6 pb-12 font-sans text-foreground max-w-5xl mx-auto relative">
      
      {/* Dynamic Compilation Modal Spinner Overlay */}
      <AnimatePresence>
        {isCompiling && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-background/80 backdrop-blur-md"
            />
            
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative w-full max-w-sm bg-card border border-border rounded-xl shadow-2xl p-6 z-10 space-y-4"
            >
              <div className="flex items-center gap-2 border-b border-border pb-3">
                <FileDown className="h-5 w-5 text-blue-600 dark:text-blue-400 animate-bounce" />
                <h3 className="font-bold text-sm">Compiling Document Format</h3>
              </div>
              <p className="text-xs text-muted-foreground leading-normal">
                Packaging rows into target <span className="font-semibold text-foreground uppercase">{format}</span> format. Running checksum calculations...
              </p>
              
              {/* Progress bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-semibold text-muted-foreground font-sans">
                  <span>Progress</span>
                  <span className="text-foreground">{compileProgress}%</span>
                </div>
                <div className="w-full bg-border rounded-full h-1.5 overflow-hidden">
                  <div 
                    className="h-full rounded-full bg-blue-600 transition-all duration-150"
                    style={{ width: `${compileProgress}%` }}
                  />
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Enterprise Reports Center</h1>
        <p className="text-muted-foreground text-xs md:text-sm">
          Select parameters to compile project delivery health registers, workforce forecast grids, or hiring requisitions.
        </p>
      </div>

      {/* Parameter Selection Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Category card selector */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4 md:col-span-2 flex flex-col justify-between">
          <div className="space-y-3">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block border-b border-border pb-2.5">
              1. Select Report Content Category
            </label>
            <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
              {[
                { id: "health", label: "Project Health" },
                { id: "forecast", label: "Capacity Forecast" },
                { id: "recommendation", label: "Resource Match" },
                { id: "hiring", label: "Hiring Pipeline" }
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setCategory(cat.id)}
                  className={`p-3 rounded-lg border text-center transition-all cursor-pointer flex flex-col items-center gap-2 justify-center text-xs font-semibold ${
                    category === cat.id
                      ? "border-blue-600 bg-blue-600/10 text-blue-600 dark:border-blue-400 dark:bg-blue-500/15 dark:text-blue-400"
                      : "border-border bg-muted/20 text-muted-foreground hover:bg-muted/40"
                  }`}
                >
                  <Briefcase className="h-4.5 w-4.5" />
                  <span>{cat.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="pt-4 flex justify-end shrink-0 border-t border-border/50">
            <Button
              onClick={handleGeneratePreview}
              disabled={loading}
              className="text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded h-8 px-6"
            >
              Generate Preview Grid
            </Button>
          </div>
        </div>

        {/* Format selector card */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm flex flex-col justify-between">
          <div className="space-y-3.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block border-b border-border pb-2.5">
              2. Select Export Format
            </label>
            
            <div className="space-y-2">
              {[
                { id: "pdf", label: "PDF Document (.pdf)", icon: FileText, desc: "Formatted report layout sheets" },
                { id: "csv", label: "CSV Flat File (.csv)", icon: FileSpreadsheet, desc: "Raw comma separated rows" },
                { id: "xlsx", label: "Excel Spreadsheet (.xlsx)", icon: FileSpreadsheet, desc: "Formatted tabular cells" }
              ].map(fmt => (
                <div
                  key={fmt.id}
                  onClick={() => setFormat(fmt.id)}
                  className={`p-3 rounded-lg border transition-all cursor-pointer flex items-start gap-3 ${
                    format === fmt.id
                      ? "border-blue-600 bg-blue-600/10 text-blue-600 dark:border-blue-400 dark:bg-blue-500/15 dark:text-blue-400 font-semibold"
                      : "border-border hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <fmt.icon className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-xs text-foreground block">{fmt.label}</span>
                    <span className="text-[10px] text-muted-foreground font-normal leading-normal">{fmt.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-border/50 shrink-0">
            <Button
              onClick={handleDownload}
              disabled={!preview || loading}
              className="w-full text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded h-8 flex items-center justify-center gap-1.5"
            >
              <Download className="h-4 w-4" /> Download Report
            </Button>
          </div>
        </div>
      </div>

      {/* 3. Modern Spreadsheet Previewer Grid */}
      {preview && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
          
          {/* Metadata banner and row filter search */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border pb-3 gap-3">
            <div className="space-y-1">
              <h3 className="font-semibold text-sm text-foreground flex items-center gap-1.5">
                <Sparkles className="h-4.5 w-4.5 text-indigo-500" />
                Spreadsheet Preview Viewer
              </h3>
              <div className="flex flex-wrap items-center gap-2.5 text-[10px] text-muted-foreground font-sans mt-0.5">
                <span>File Size: <strong className="text-foreground">{preview.size}</strong></span>
                <span>&bull;</span>
                <span>Rows: <strong className="text-foreground">{preview.rowCount} items</strong></span>
                <span>&bull;</span>
                <span>Compiled: <strong className="text-foreground">{preview.generatedDate}</strong></span>
                <span>&bull;</span>
                <span>Author: <strong className="text-foreground">{preview.author}</strong></span>
              </div>
            </div>

            {/* Filter query */}
            <div className="flex items-center gap-2 bg-muted/60 rounded-md border border-border/80 px-2.5 py-1 text-xs self-start shrink-0">
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
              <input
                value={filterQuery}
                onChange={e => setFilterQuery(e.target.value)}
                placeholder="Filter preview rows..."
                className="bg-transparent border-0 outline-none text-xs placeholder:text-muted-foreground text-foreground w-40"
              />
            </div>
          </div>

          {/* Actual spreadsheet grid table */}
          <div className="w-full overflow-x-auto border border-border/80 rounded-lg">
            <table className="w-full text-left border-collapse text-xs font-sans">
              <thead>
                <tr className="bg-muted/50 border-b border-border/80">
                  {preview.columns.map((col, idx) => (
                    <th key={idx} className="p-3 font-semibold text-muted-foreground uppercase tracking-wider select-none">
                      {col.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {filteredRows.length > 0 ? (
                  filteredRows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-muted/10 transition-colors">
                      {preview.columns.map((col, cIdx) => (
                        <td key={cIdx} className="p-3 text-foreground font-medium">
                          {row[col.accessor] !== undefined ? (
                            row[col.accessor].toString().includes("Red") || row[col.accessor].toString().includes("Critical") ? (
                              <span className="px-1.5 py-0.5 rounded bg-red-500/10 text-red-500 font-bold uppercase text-[9px]">
                                {row[col.accessor]}
                              </span>
                            ) : row[col.accessor].toString().includes("Amber") || row[col.accessor].toString().includes("Warning") ? (
                              <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 font-bold uppercase text-[9px]">
                                {row[col.accessor]}
                              </span>
                            ) : row[col.accessor].toString().includes("Green") || row[col.accessor].toString().includes("Stable") ? (
                              <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-bold uppercase text-[9px]">
                                {row[col.accessor]}
                              </span>
                            ) : (
                              row[col.accessor]
                            )
                          ) : (
                            "-"
                          )}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={preview.columns.length} className="p-8 text-center text-muted-foreground">
                      No matching preview rows found for query "{filterQuery}".
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  )
}
