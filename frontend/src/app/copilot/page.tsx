"use client"

import React, { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { copilotService } from "@/services/copilot.service"
import { fetchAPI } from "@/services/api"
import { getEmployeeName } from "@/services/dashboard.service"
import {
  Sparkles,
  Send,
  BrainCircuit,
  MessageSquare,
  TrendingUp,
  UserCheck,
  ShieldAlert,
  HelpCircle,
  ChevronDown,
  ChevronRight,
  Info,
  Clock,
  ArrowRight,
  UserPlus,
  Play,
  RotateCcw,
  CheckCircle,
  Plus
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend
} from "recharts"

interface ChatMessage {
  id: string
  role: "user" | "assistant"
  text: string
  confidence?: number
  reasoningSteps?: string[]
  chartData?: any[]
  tableData?: any[]
  cardData?: any[]
}

interface SuggestedPrompt {
  label: string
  query: string
}

export default function CopilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      text: "Hello! I am your AI Decision Intelligence Copilot. I run semantic algorithms across your PostgreSQL databases, Qdrant vectors, and HubSpot deals to resolve staffing gaps, audit delivery health, and simulate pipeline capacity.\n\nAsk me anything, or tap one of the suggested requests below.",
      confidence: 100
    }
  ])
  const [inputValue, setInputValue] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [activeReasoningStep, setActiveReasoningStep] = useState(0)
  

  
  // Custom states
  const [mounted, setMounted] = useState(false)
  const [historyQueries, setHistoryQueries] = useState<string[]>([
    "Sarah Jenkins backup resource",
    "Q3 Capacity forecasts",
    "CLI-201 delivery blocker logs"
  ])

  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isGenerating])

  const suggestedPrompts: SuggestedPrompt[] = [
    { label: "Check Critical Project Gaps", query: "Which projects have critical health risks today?" },
    { label: "Find CLI-201 Candidates", query: "Who is recommended for CLI-201 E-Commerce Migration?" },
    { label: "Analyze Q3 Capacity Forecast", query: "Draft a Q3 capacity forecast summary" }
  ]

  // Prebaked replies mapping for rich visual streaming responses
  const getPrebakedReply = (query: string): Partial<ChatMessage> => {
    const cleanQuery = query.toLowerCase()

    if (cleanQuery.includes("project") || cleanQuery.includes("risk") || cleanQuery.includes("health")) {
      return {
        text: "I scanned PostgreSQL and flagged **2 critical Red risks** and **1 Amber warnings**. Both Red status projects suffer from developers rolling off their contracts this week, creating immediate capacity gaps:",
        confidence: 95,
        reasoningSteps: [
          "Initiating Health Engine diagnostic audit...",
          "Scanning database client metrics & active contracts...",
          "Checking Postgres logs for task latency deviations...",
          "Compiling RAG status reports..."
        ],
        cardData: [
          { id: "CLI-201", name: "E-Commerce Migration", client: "Delta Retail", status: "Red", PM: "Sarah Jenkins", gap: "Needs Lead React Architect", progress: 68 },
          { id: "CLI-108", name: "Legacy Database Sync", client: "Apex Logistics", status: "Red", PM: "Tom Harris", gap: "Postgres Indexing Sync lag", progress: 42 }
        ]
      }
    }

    if (cleanQuery.includes("cli-201") || cleanQuery.includes("recommend") || cleanQuery.includes("replace") || cleanQuery.includes("match")) {
      return {
        text: "I scanned the Qdrant vector database and matched benched engineers against the **E-Commerce Migration (CLI-201)** vacancy (Lead React Architect). The match score ranks candidates by skills, availability timeline, and previous experience:",
        confidence: 98,
        reasoningSteps: [
          "Scanning Qdrant database vector index for 'Lead React Architect'...",
          "Querying Recommendation Engine (FTE availabilities & skills models)...",
          "Scoring candidates across 5 matching dimensions...",
          "Generating LLM staffing rationale justifications..."
        ],
        tableData: [
          { id: "EMP102", name: "Alex Mercer", role: "Lead React Architect", score: 96, avail: "90% ready in 8 days", skills: "React, Next, TS" },
          { id: "EMP108", name: "David Chen", role: "Senior Python DBA", score: 88, avail: "100% available", skills: "Python, Postgres, React" },
          { id: "EMP119", name: "Elena Petrova", role: "Next.js Engineer", score: 81, avail: "70% available", skills: "React, Next, Tailwind" }
        ]
      }
    }

    if (cleanQuery.includes("forecast") || cleanQuery.includes("capacity") || cleanQuery.includes("summary") || cleanQuery.includes("q3")) {
      return {
        text: "Here is the projected workforce capacity and demand forecast for Q3 2026. The baseline calculations indicate a **6 FTE deficit** in engineering roles (specifically React Architects and Backend Engineers) starting in June due to pipeline contract wins:",
        confidence: 96,
        reasoningSteps: [
          "Calling Capacity Forecast Engine...",
          "Retrieving active allocations and HubSpot sales deal coefficients...",
          "Aggregating monthly Supply vs. Demand curves...",
          "Simulating resource gap timelines..."
        ],
        chartData: [
          { month: "Jan", Capacity: 120, Demand: 98, Gap: 22 },
          { month: "Feb", Capacity: 120, Demand: 104, Gap: 16 },
          { month: "Mar", Capacity: 125, Demand: 110, Gap: 15 },
          { month: "Apr", Capacity: 125, Demand: 112, Gap: 13 },
          { month: "May", Capacity: 130, Demand: 118, Gap: 12 },
          { month: "Jun", Capacity: 130, Demand: 124, Gap: 6 }
        ]
      }
    }

    return {
      text: "I analyzed the platform logs. I am actively connected to the **Recommendation Engine**, **Forecast Engine**, and **Project Health Engine**. I can query employee records, run what-if capacity simulations, and audit project timelines.\n\nTry checking critical project health risks or matching candidates for project CLI-201.",
      confidence: 90,
      reasoningSteps: [
        "Querying semantic database indexes...",
        "Calling LLM provider fallback logic..."
      ]
    }
  }

  const handleSend = (text: string) => {
    if (!text.trim()) return

    // 1. Add user message
    const userMsgId = Date.now().toString()
    setMessages(prev => [...prev, { id: userMsgId, role: "user", text }])
    setInputValue("")
    setIsGenerating(true)
    setActiveReasoningStep(0)

    // Save to history logs
    if (!historyQueries.includes(text.trim())) {
      setHistoryQueries(prev => [text.trim(), ...prev.slice(0, 4)])
    }

    // Call live FastAPI Copilot chat endpoint
    copilotService.chat({ message: text, session_id: "default" })
      .then(async (res) => {
        let chartData: any[] | undefined = undefined
        let tableData: any[] | undefined = undefined
        let cardData: any[] | undefined = undefined

        const lowerText = text.toLowerCase()
        const intent = res.detected_intent.toLowerCase()

        if (intent === "forecast" || lowerText.includes("forecast") || lowerText.includes("capacity")) {
          // Fetch live forecast curves
          const forecast = await fetchAPI<any>("/api/forecast/six-month").catch(() => null)
          if (forecast) {
            chartData = (forecast.monthly_projections || []).map((m: any) => ({
              month: m.month.split("-")[1] || m.month,
              Capacity: Math.round(m.headcount_demand + m.capacity_surplus),
              Demand: Math.round(m.headcount_demand),
              Gap: Math.round(m.capacity_deficit)
            }))
          }
        } else if (intent === "recommendation" || lowerText.includes("recommend") || lowerText.includes("candidate") || lowerText.includes("replace")) {
          // Fetch live recommendations
          const recs = await fetchAPI<any>("/api/recommend/resources", {
            method: "POST",
            body: JSON.stringify({ required_skills: ["React", "Python"], top_n: 3 })
          }).catch(() => null)
          if (recs) {
            tableData = recs.recommendations.map((c: any) => ({
              id: c.employee_id,
              name: getEmployeeName(c.employee_id),
              role: c.job_name,
              score: Math.round(c.final_score <= 1 ? c.final_score * 100 : c.final_score),
              avail: c.availability_date,
              skills: c.matching_skills.join(", ")
            }))
          }
        } else if (intent === "health" || lowerText.includes("health") || lowerText.includes("risk") || lowerText.includes("critical")) {
          // Fetch live health project summaries
          const health = await fetchAPI<any[]>("/api/health/projects").catch(() => null)
          if (health) {
            cardData = health.filter(h => h.overall_health === "Red").map((h: any) => ({
              id: h.project_id,
              name: "Client Project",
              client: "Client Account",
              status: h.overall_health,
              PM: "Sarah Jenkins",
              gap: "Critical Staff Gap",
              progress: 65
            }))
          }
        }

        const replyMeta: Partial<ChatMessage> = {
          text: res.response,
          confidence: Math.round(res.intent_confidence <= 1 ? res.intent_confidence * 100 : res.intent_confidence),
          reasoningSteps: res.executed_tools.length > 0 
            ? res.executed_tools 
            : ["Parsing request semantics...", "Routing query target...", "Analyzing context maps...", "Generating LLM response..."],
          chartData,
          tableData,
          cardData
        }

        // 3. Simulate reasoning steps ticking
        const stepsCount = replyMeta.reasoningSteps?.length || 4
        let stepIndex = 0
        const interval = setInterval(() => {
          if (stepIndex < stepsCount - 1) {
            stepIndex++
            setActiveReasoningStep(stepIndex)
          } else {
            clearInterval(interval)
            // Start streaming text
            streamResponse(replyMeta)
          }
        }, 400)
      })
      .catch(err => {
        console.error("Copilot chat failed:", err)
        setIsGenerating(false)
      })
  }

  const streamResponse = (replyMeta: Partial<ChatMessage>) => {
    const fullText = replyMeta.text || ""
    const words = fullText.split(" ")
    let currentText = ""
    let wordIdx = 0

    const botMsgId = (Date.now() + 1).toString()
    
    // Add empty bot bubble with metadata
    setMessages(prev => [
      ...prev,
      {
        id: botMsgId,
        role: "assistant",
        text: "",
        confidence: replyMeta.confidence,
        reasoningSteps: replyMeta.reasoningSteps
      }
    ])

    const streamInterval = setInterval(() => {
      if (wordIdx < words.length) {
        currentText += (wordIdx === 0 ? "" : " ") + words[wordIdx]
        setMessages(prev => 
          prev.map(m => m.id === botMsgId ? { ...m, text: currentText } : m)
        )
        wordIdx++
      } else {
        clearInterval(streamInterval)
        // Inject final rich media data (charts, tables, cards) once text stream finishes
        setMessages(prev => 
          prev.map(m => m.id === botMsgId ? { 
            ...m, 
            chartData: replyMeta.chartData,
            tableData: replyMeta.tableData,
            cardData: replyMeta.cardData
          } : m)
        )
        setIsGenerating(false)
      }
    }, 45) // Typist animation speed
  }

  return (
    <div className="flex h-[82vh] w-full gap-4 overflow-hidden text-sm font-sans text-foreground">
      
      {/* 1. History Sidebar (Hidden on small screens) */}
      <div className="hidden lg:flex w-64 bg-card/40 border border-border rounded-xl p-4 flex-col justify-between shrink-0">
        <div className="space-y-4">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <Clock className="h-4 w-4 text-blue-500" />
            <h3 className="font-semibold text-xs uppercase tracking-wider text-muted-foreground">Chat History</h3>
          </div>
          <div className="space-y-1.5">
            {historyQueries.map((hist, i) => (
              <button
                key={i}
                onClick={() => handleSend(hist)}
                className="w-full text-left truncate px-2.5 py-2 text-xs rounded hover:bg-muted/50 transition-colors text-muted-foreground hover:text-foreground font-medium cursor-pointer"
              >
                {hist}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-lg p-3 space-y-1 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-1 font-bold text-indigo-600 dark:text-indigo-400">
            <BrainCircuit className="h-3.5 w-3.5" />
            <span>Engines Online</span>
          </div>
          <p className="leading-relaxed">Connected to active PostgreSQL and Qdrant clusters.</p>
        </div>
      </div>

      {/* 2. Chat Workspace */}
      <div className="flex-1 bg-card border border-border rounded-xl flex flex-col justify-between overflow-hidden relative">
        
        {/* Chat Feed */}
        <div className="flex-1 p-4 md:p-6 overflow-y-auto space-y-5">
          {messages.map((msg) => {
            const isBot = msg.role === "assistant"
            return (
              <div 
                key={msg.id}
                className={`flex gap-3 max-w-[85%] ${isBot ? "mr-auto text-left" : "ml-auto text-right flex-row-reverse"}`}
              >
                {/* Avatar */}
                <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold shadow-sm ${
                  isBot 
                    ? "bg-indigo-500 text-white" 
                    : "bg-blue-600 text-white"
                }`}>
                  {isBot ? "AI" : "SP"}
                </div>

                <div className="space-y-3">
                  {/* Chat message bubble */}
                  <div className={`rounded-2xl p-4 shadow-sm text-xs leading-relaxed font-sans ${
                    isBot 
                      ? "bg-card border border-border/80 text-foreground/90" 
                      : "bg-blue-600 text-white text-left font-medium"
                  }`}>
                    {/* Rendered Text */}
                    <div className="whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                      {/* Flashing cursor stream indicator */}
                      {isGenerating && isBot && msg.text && msg.text.split(" ").length < (getPrebakedReply(inputValue).text?.split(" ").length || 1) && (
                        <span className="inline-block h-3.5 w-1 bg-blue-600 dark:bg-blue-400 ml-0.5 animate-pulse" />
                      )}
                    </div>

                    {/* Confidence Pill */}
                    {isBot && msg.confidence && msg.confidence < 100 && (
                      <div className="mt-3.5 flex items-center gap-1.5 text-[9px] font-bold text-indigo-500 uppercase tracking-wider border-t border-border/40 pt-2">
                        <CheckCircle className="h-3 w-3 text-indigo-500" />
                        <span>AI Confidence: {msg.confidence}%</span>
                      </div>
                    )}
                  </div>

                  {/* Reasoning Timeline Accordion (Only show during generation for active bot bubble) */}
                  {isBot && isGenerating && msg.reasoningSteps && (
                    <div className="bg-muted/30 border border-border rounded-xl p-3.5 space-y-2 max-w-[320px] transition-all">
                      <span className="text-[9px] text-muted-foreground uppercase font-bold tracking-wider block">
                        Engine Reasoning Timeline
                      </span>
                      <div className="space-y-1.5 text-[10px] font-sans">
                        {msg.reasoningSteps.map((step, sIdx) => {
                          const isPast = sIdx < activeReasoningStep
                          const isActive = sIdx === activeReasoningStep
                          return (
                            <div key={sIdx} className="flex items-center gap-2">
                              {isPast ? (
                                <CheckCircle className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                              ) : isActive ? (
                                <div className="h-3 w-3 rounded-full border border-indigo-500 border-t-transparent animate-spin shrink-0" />
                              ) : (
                                <div className="h-2 w-2 rounded-full bg-muted-foreground/30 shrink-0 ml-0.5" />
                              )}
                              <span className={`${isPast ? "text-muted-foreground" : isActive ? "text-foreground font-semibold" : "text-muted-foreground/60"}`}>
                                {step}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  {/* Rich Component: Recharts Chart */}
                  {isBot && msg.chartData && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="rounded-xl border border-border bg-card p-4 shadow-md w-full max-w-[480px]"
                    >
                      <span className="text-[9px] text-indigo-600 dark:text-indigo-400 font-bold uppercase tracking-wider block mb-3">
                        Capacity Graph Output
                      </span>
                      <div className="h-[180px] w-full">
                        {mounted ? (
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={msg.chartData} margin={{ top: 5, right: 0, left: -25, bottom: 0 }}>
                              <defs>
                                <linearGradient id="copilotCap" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.1}/>
                                  <stop offset="95%" stopColor="#4f46e5" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                              <XAxis dataKey="month" style={{ fontSize: "9px", fill: "var(--muted-foreground)" }} />
                              <YAxis style={{ fontSize: "9px", fill: "var(--muted-foreground)" }} />
                              <RechartsTooltip contentStyle={{ fontSize: "10px" }} />
                              <Area type="monotone" dataKey="Capacity" stroke="#4f46e5" fillOpacity={1} fill="url(#copilotCap)" />
                              <Area type="monotone" dataKey="Demand" stroke="#ef4444" fillOpacity={0} />
                            </AreaChart>
                          </ResponsiveContainer>
                        ) : (
                          <div className="text-xs text-muted-foreground">Loading chart...</div>
                        )}
                      </div>
                    </motion.div>
                  )}

                  {/* Rich Component: Allocation Table */}
                  {isBot && msg.tableData && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="rounded-xl border border-border bg-card overflow-hidden shadow-md w-full max-w-[480px] text-[11px] font-sans"
                    >
                      <div className="px-3.5 py-2 border-b border-border bg-muted/30">
                        <span className="text-[9px] text-indigo-600 dark:text-indigo-400 font-bold uppercase tracking-wider">
                          Resource Match Recommendations
                        </span>
                      </div>
                      <div className="divide-y divide-border/60">
                        {msg.tableData.map((row, rIdx) => (
                          <div key={rIdx} className="flex items-center justify-between p-3 hover:bg-muted/10">
                            <div>
                              <p className="font-semibold text-foreground">{row.name}</p>
                              <p className="text-[10px] text-muted-foreground">{row.role} &bull; {row.skills}</p>
                            </div>
                            <div className="text-right space-y-1">
                              <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 font-bold">
                                {row.score}% match
                              </span>
                              <span className="block text-[8px] text-muted-foreground">
                                {row.avail}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="p-2 bg-card border-t border-border flex justify-end shrink-0">
                        <Link href="/recommendation">
                          <Button size="xs" className="h-6 text-[10px] bg-blue-600 hover:bg-blue-700 text-white rounded">
                            Open Allocation Board <ArrowRight className="h-3 w-3" />
                          </Button>
                        </Link>
                      </div>
                    </motion.div>
                  )}

                  {/* Rich Component: Health Risk Cards */}
                  {isBot && msg.cardData && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="grid gap-3 sm:grid-cols-2 max-w-[480px] w-full text-[11px] font-sans"
                    >
                      {msg.cardData.map((proj) => (
                        <div key={proj.id} className="rounded-xl border border-border bg-card p-3 shadow-md flex flex-col justify-between gap-3">
                          <div>
                            <div className="flex items-start justify-between">
                              <h4 className="font-semibold text-foreground">{proj.name}</h4>
                              <span className="px-1 py-0.2 rounded text-[8px] font-bold bg-red-500/10 text-red-500">
                                {proj.status}
                              </span>
                            </div>
                            <p className="text-[9px] text-muted-foreground mt-0.5">PM: {proj.PM} &bull; Client: {proj.client}</p>
                            <p className="text-[10px] text-red-500 font-semibold mt-2">
                              {proj.gap}
                            </p>
                          </div>
                          
                          <Link href={`/recommendation?project=${proj.id}`}>
                            <Button size="xs" variant="outline" className="w-full h-6 text-[9px] border-red-500/20 text-red-500 hover:bg-red-500/5">
                              Resolve Allocation Gap
                            </Button>
                          </Link>
                        </div>
                      ))}
                    </motion.div>
                  )}

                </div>
              </div>
            )
          })}
          
          {/* Scroll target anchor */}
          <div ref={chatEndRef} />
        </div>

        {/* Suggested Queries Tray (Only show when not generating) */}
        {!isGenerating && (
          <div className="px-4 py-2 border-t border-border bg-card/60 flex flex-wrap gap-2 text-xs">
            {suggestedPrompts.map((prom, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prom.query)}
                className="px-2.5 py-1.5 rounded-lg border border-border/80 bg-muted/10 hover:bg-muted/40 transition-colors text-muted-foreground hover:text-foreground font-medium cursor-pointer"
              >
                {prom.label}
              </button>
            ))}
          </div>
        )}

        {/* Input Bar */}
        <div className="p-4 border-t border-border bg-card/40 flex items-center gap-2">
          <div className="flex-1 flex items-center gap-2 bg-muted/60 rounded-full border border-border px-4 py-2 shadow-inner focus-within:border-blue-500/60 focus-within:ring-1 focus-within:ring-blue-600/30 transition-all">
            <input
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !isGenerating) {
                  handleSend(inputValue)
                }
              }}
              placeholder={isGenerating ? "AI is typing..." : "Ask your copilot to forecast gaps, matching resources, audit projects..."}
              className="flex-1 bg-transparent border-0 outline-none text-xs placeholder:text-muted-foreground text-foreground"
              disabled={isGenerating}
            />
            <Button
              size="icon"
              disabled={isGenerating || !inputValue.trim()}
              onClick={() => handleSend(inputValue)}
              className="h-7 w-7 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-sm shrink-0"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

      </div>
    </div>
  )
}
