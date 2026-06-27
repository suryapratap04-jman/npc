"use client"

import React, { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import {
  Search,
  Users,
  Briefcase,
  Layers,
  Sparkles,
  X,
  ChevronRight,
  ArrowUpRight,
  Award,
  CircleDollarSign,
  Workflow,
  Clock,
  History,
  Compass
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { searchService } from "@/services/search.service"

interface SearchItem {
  id: string
  name: string
  title: string
  type: "Employee" | "Project" | "Skill" | "Pipeline"
  subtitle: string
  details: string
  similarity: number
  profile: any
}

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [activeCategory, setActiveCategory] = useState("all")
  const [debouncedQuery, setDebouncedQuery] = useState(query)
  
  // Drawer state
  const [selectedItem, setSelectedItem] = useState<SearchItem | null>(null)

  // Popular search suggestions
  const suggestions = [
    { text: "Lead React Architect", category: "all" },
    { text: "Delta Retail", category: "project" },
    { text: "PostgreSQL DBA", category: "skill" },
    { text: "AWS Cloud Specialist", category: "employee" }
  ]

  // Recent searches state
  const [recentSearches, setRecentSearches] = useState<string[]>([
    "React Developer",
    "Apex Database lag",
    "Sarah Jenkins"
  ])

  // Debounce search query changes
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query)
    }, 250)
    return () => clearTimeout(handler)
  }, [query])

  // Run vector search queries using TanStack Query
  const { data: results = [], isLoading: loading } = useQuery<SearchItem[]>({
    queryKey: ["search", debouncedQuery, activeCategory],
    queryFn: () => searchService.searchAll(debouncedQuery, activeCategory),
    enabled: debouncedQuery.trim().length > 0
  })

  const handleSuggestionClick = (text: string, cat: string) => {
    setQuery(text)
    setActiveCategory(cat)
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim() && !recentSearches.includes(query.trim())) {
      setRecentSearches(prev => [query.trim(), ...prev.slice(0, 4)])
    }
    setDebouncedQuery(query)
  }

  const handleClearSearch = () => {
    setQuery("")
    setDebouncedQuery("")
  }

  return (
    <div className="space-y-6 pb-12 font-sans text-foreground max-w-4xl mx-auto">
      
      {/* 1. Spotlight Search Header */}
      <div className="text-center py-4 space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">Semantic Workspace Search</h1>
        <p className="text-muted-foreground text-xs md:text-sm max-w-md mx-auto">
          Query benched developers, client projects, technical skills, and sales deals using vector similarity matches.
        </p>
      </div>

      {/* 2. Central Spotlight Input Block */}
      <div className="rounded-2xl border border-border bg-card shadow-2xl p-5 relative overflow-hidden ring-1 ring-black/5 dark:ring-white/5">
        <form onSubmit={handleSearchSubmit} className="relative flex items-center gap-3 bg-muted/60 rounded-xl px-4 py-3 border border-border/80 focus-within:border-blue-500/60 focus-within:ring-1 focus-within:ring-blue-600/30 transition-all">
          <Search className="h-5 w-5 text-muted-foreground shrink-0" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Type to search employee records, project names, code competencies, CRM deals..."
            className="flex-1 bg-transparent border-0 outline-none text-sm placeholder:text-muted-foreground text-foreground"
            autoFocus
          />
          {query && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-6 w-6 rounded-full hover:bg-muted/80 text-muted-foreground"
              onClick={handleClearSearch}
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          )}
        </form>

        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-2 mt-4 text-xs font-semibold">
          <span className="text-muted-foreground font-medium mr-1.5">Search scope:</span>
          {[
            { id: "all", label: "All Assets" },
            { id: "employee", label: "Employees" },
            { id: "project", label: "Projects" },
            { id: "skill", label: "Skills" },
            { id: "pipeline", label: "Pipelines" }
          ].map(cat => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setActiveCategory(cat.id)}
              className={`px-3 py-1 rounded-full border transition-all ${
                activeCategory === cat.id
                  ? "bg-blue-600 border-blue-600 text-white font-semibold shadow-sm"
                  : "border-border bg-muted/20 text-muted-foreground hover:bg-muted/60"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Search Suggestions & Recents (Show when query is empty) */}
      {!query && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Suggestions */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Compass className="h-4 w-4 text-blue-500" />
              Popular Suggestions
            </h4>
            <div className="flex flex-wrap gap-2 text-xs">
              {suggestions.map((sug, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestionClick(sug.text, sug.category)}
                  className="px-2.5 py-1.5 rounded-lg border border-border/80 bg-muted/10 hover:bg-muted/40 transition-colors font-medium text-foreground/90 cursor-pointer"
                >
                  {sug.text}
                </button>
              ))}
            </div>
          </div>

          {/* Recent Searches */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <History className="h-4 w-4 text-blue-500" />
              Recent Searches
            </h4>
            <div className="space-y-1.5 text-xs">
              {recentSearches.map((rec, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(rec)}
                  className="w-full flex items-center justify-between text-muted-foreground hover:text-foreground font-sans p-1.5 rounded hover:bg-muted/30 transition-colors text-left"
                >
                  <span className="flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-muted-foreground/60" />
                    {rec}
                  </span>
                  <ChevronRight className="h-3 w-3 text-muted-foreground/60" />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 4. Results List */}
      {query && (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-semibold text-muted-foreground">
              {loading ? "Calculating matches..." : `Matching similarity hits (${results.length})`}
            </span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 flex-col gap-2">
              <div className="h-6 w-6 rounded-full border-2 border-blue-600/20 border-t-blue-600 animate-spin" />
              <span className="text-xs text-muted-foreground">Retrieving vector indices...</span>
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-2.5">
              {results.map(item => {
                const isEmp = item.type === "Employee"
                const isProj = item.type === "Project"
                const isSkill = item.type === "Skill"
                return (
                  <motion.div
                    key={item.id}
                    layoutId={item.id}
                    onClick={() => setSelectedItem(item)}
                    className="rounded-xl border border-border bg-card p-4 hover:border-blue-500/40 hover:bg-muted/10 transition-all duration-150 cursor-pointer flex items-center justify-between gap-4 group"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 shadow-inner ${
                        isEmp 
                          ? "bg-blue-600/10 text-blue-600 dark:bg-blue-500/15" 
                          : isProj 
                          ? "bg-red-500/10 text-red-500 dark:bg-red-500/15" 
                          : isSkill 
                          ? "bg-indigo-500/10 text-indigo-600 dark:bg-indigo-500/15" 
                          : "bg-yellow-500/10 text-yellow-600 dark:bg-yellow-500/15"
                      }`}>
                        {isEmp && <Users className="h-4 w-4" />}
                        {isProj && <Briefcase className="h-4 w-4" />}
                        {isSkill && <Award className="h-4 w-4" />}
                        {item.type === "Pipeline" && <CircleDollarSign className="h-4 w-4" />}
                      </div>
                      <div>
                        <h4 className="font-semibold text-xs text-foreground group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors flex items-center gap-1.5">
                          {item.name}
                          <span className="text-[9px] text-muted-foreground font-normal">({item.type})</span>
                        </h4>
                        <p className="text-[10px] text-muted-foreground leading-snug mt-0.5">{item.subtitle}</p>
                        <p className="text-[9px] text-muted-foreground/80 mt-1">{item.details}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400">
                        Match {Math.round(item.similarity * 100)}%
                      </span>
                      <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </motion.div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-16 border border-dashed border-border rounded-xl bg-card">
              <p className="text-xs text-muted-foreground font-sans">No matches found for query "{query}".</p>
            </div>
          )}
        </div>
      )}

      {/* DETAIL WORKBENCH DRAWER */}
      <AnimatePresence>
        {selectedItem && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-background/60 backdrop-blur-sm"
              onClick={() => setSelectedItem(null)}
            />

            <div className="absolute inset-y-0 right-0 flex max-w-full">
              <motion.div
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 26, stiffness: 220 }}
                className="w-screen max-w-md bg-card border-l border-border shadow-2xl p-6 flex flex-col justify-between h-full overflow-y-auto"
              >
                
                {/* Header */}
                <div className="flex items-center justify-between border-b border-border pb-3.5 mb-5 shrink-0">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />
                    <h3 className="font-bold text-base">Metadata Asset Sheet</h3>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full hover:bg-muted/50" onClick={() => setSelectedItem(null)}>
                    <X className="h-4.5 w-4.5" />
                  </Button>
                </div>

                <div className="flex-1 space-y-6 text-xs font-sans">
                  
                  {/* Title Banner */}
                  <div className="bg-muted/20 p-3.5 rounded-lg border border-border/40 flex items-center justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-foreground">{selectedItem.title}</h4>
                      <p className="text-[11px] text-muted-foreground mt-0.5">{selectedItem.subtitle}</p>
                    </div>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400">
                      Match {Math.round(selectedItem.similarity * 100)}%
                    </span>
                  </div>

                  {/* 1. Category Render Sheet: Employee */}
                  {selectedItem.type === "Employee" && (
                    <div className="space-y-4">
                      <div className="space-y-1">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Operational Summary</span>
                        <p className="text-muted-foreground leading-normal">
                          Assigned to department <strong className="text-foreground">{selectedItem.profile.department}</strong>.
                          Current project allocation: <strong className="text-foreground">{selectedItem.profile.currentProject}</strong>.
                        </p>
                      </div>

                      <div className="space-y-2 border-t border-border/60 pt-4">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Platform Credentials</span>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Experience:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.experience} years</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Free Capacity:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.availability}% free</span>
                        </div>
                      </div>

                      <div className="space-y-2 border-t border-border/60 pt-4">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Validated Skillsets</span>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedItem.profile.skills.map((s: string, i: number) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-muted text-[10px] text-foreground font-semibold border border-border/40">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-2 border-t border-border/60 pt-4">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Core Competencies</span>
                        <ul className="space-y-1.5 text-muted-foreground">
                          {selectedItem.profile.competencies.map((c: string, i: number) => (
                            <li key={i} className="flex items-center gap-2">
                              <span className="h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
                              {c}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* 2. Category Render Sheet: Project */}
                  {selectedItem.type === "Project" && (
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Timeline Audits</span>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Milestone Progress:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.progress}%</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">RAG Status:</span>
                          <span className={`font-bold uppercase text-[9px] px-1.5 py-0.2 rounded ${
                            selectedItem.profile.status === "Red" 
                              ? "bg-red-500/10 text-red-500" 
                              : selectedItem.profile.status === "Amber" 
                              ? "bg-amber-500/10 text-amber-500" 
                              : "bg-emerald-500/10 text-emerald-500"
                          }`}>{selectedItem.profile.status}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Staffing Level:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.staffCount} FTEs</span>
                        </div>
                      </div>

                      <div className="space-y-1.5 border-t border-border/60 pt-4">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">AI Risk Diagnostics</span>
                        <p className="text-muted-foreground leading-normal italic bg-muted/20 p-2.5 rounded border border-border/50">
                          "{selectedItem.profile.riskFactor}"
                        </p>
                      </div>
                    </div>
                  )}

                  {/* 3. Category Render Sheet: Skill */}
                  {selectedItem.type === "Skill" && (
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Code Standardization</span>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Focus Category:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.category}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Certified Standards:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.standardLibrary}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Platform Accreditations:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.certificationsAvailable}</span>
                        </div>
                      </div>

                      <div className="space-y-2 border-t border-border/60 pt-4">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Active Accounts</span>
                        <div className="flex flex-wrap gap-2 text-[10px]">
                          {selectedItem.profile.associatedProjects.map((proj: string, i: number) => (
                            <span key={i} className="px-2 py-1 rounded bg-blue-600/10 text-blue-600 dark:text-blue-400 font-semibold border border-blue-600/5">
                              {proj}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 4. Category Render Sheet: Pipeline */}
                  {selectedItem.type === "Pipeline" && (
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">CRM Lead Profiling</span>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Sales Value:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.estimatedValue}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Deal Probability:</span>
                          <span className="font-bold text-emerald-500">{selectedItem.profile.probability}</span>
                        </div>
                        <div className="flex justify-between py-1.5 border-b border-border/40">
                          <span className="text-muted-foreground">Anticipated Kickoff:</span>
                          <span className="font-semibold text-foreground">{selectedItem.profile.expectedStart}</span>
                        </div>
                      </div>

                      <div className="space-y-2 border-t border-border/60 pt-4">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Vacancies Needed</span>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedItem.profile.rolesNeeded.map((role: string, i: number) => (
                            <span key={i} className="px-2 py-0.5 rounded bg-muted text-[10px] text-muted-foreground font-medium border border-border/40">
                              {role}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-1.5 border-t border-border/60 pt-4 text-muted-foreground">
                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Deal Notes</span>
                        <p className="leading-relaxed">{selectedItem.profile.notes}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer Controls */}
                <div className="pt-4 border-t border-border shrink-0 flex gap-3">
                  <Button
                    variant="outline"
                    className="flex-1 h-9 text-xs font-semibold text-muted-foreground hover:text-foreground"
                    onClick={() => setSelectedItem(null)}
                  >
                    Close Sheet
                  </Button>
                  
                  {selectedItem.type === "Employee" && (
                    <Link href={`/recommendation`} className="flex-1">
                      <Button
                        className="w-full h-9 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded"
                        onClick={() => setSelectedItem(null)}
                      >
                        Allocate Employee
                      </Button>
                    </Link>
                  )}
                  {selectedItem.type === "Project" && (
                    <Link href={`/recommendation?project=${selectedItem.id}`} className="flex-1">
                      <Button
                        className="w-full h-9 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded"
                        onClick={() => setSelectedItem(null)}
                      >
                        Match Staffing
                      </Button>
                    </Link>
                  )}
                </div>
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>

    </div>
  )
}
