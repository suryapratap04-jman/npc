"use client"

import React, { useState } from "react"
import {
  Settings,
  Database,
  CheckCircle,
  RefreshCw,
  Sliders,
  Bell,
  Cpu,
  BrainCircuit,
  Lock,
  Globe
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { useToastStore } from "@/store/useToastStore"
import { fetchAPI } from "@/services/api"

export default function SettingsPage() {
  const addToast = useToastStore(s => s.addToast)

  // Sliders states
  const [skillWeight, setSkillWeight] = useState(40)
  const [compWeight, setCompWeight] = useState(30)
  const [availWeight, setAvailWeight] = useState(20)
  const [simWeight, setSimWeight] = useState(10)

  // System states
  const [activeModel, setActiveModel] = useState("qwen")
  const [syncStatus, setSyncStatus] = useState<Record<string, string>>({
    relational: "Synced 2 hrs ago",
    vector: "Synced 1 day ago",
    crm: "Synced 1 hr ago"
  })
  const [syncLoading, setSyncLoading] = useState<Record<string, boolean>>({
    relational: false,
    vector: false,
    crm: false
  })

  // Notifications thresholds
  const [minUtil, setMinUtil] = useState(70)
  const [maxDelay, setMaxDelay] = useState(14)

  const handleSaveWeights = () => {
    const total = skillWeight + compWeight + availWeight + simWeight
    if (total !== 100) {
      addToast(`Error: Weights must sum to 100%. Current sum: ${total}%`, "error")
      return
    }
    addToast("Resource Matcher engine weights saved successfully.", "success")
  }

  const handleSync = (key: string, name: string) => {
    setSyncLoading(prev => ({ ...prev, [key]: true }))
    
    // Call live FastAPI sync embeddings generation endpoint
    fetchAPI("/api/embeddings/generate", { method: "POST" })
      .then(() => {
        setSyncLoading(prev => ({ ...prev, [key]: false }))
        setSyncStatus(prev => ({ ...prev, [key]: "Synced just now" }))
        addToast(`Database sync completed: ${name} database is active.`, "success")
      })
      .catch(err => {
        console.error("Sync failed:", err)
        setSyncLoading(prev => ({ ...prev, [key]: false }))
        addToast(`Database sync failed: ${(err as any).detail || err.message}`, "error")
      })
  }

  return (
    <div className="space-y-6 pb-12 font-sans text-foreground max-w-4xl mx-auto">
      
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Platform Settings</h1>
        <p className="text-muted-foreground text-xs md:text-sm">
          Optimize matching weights, run database cluster syncs, and adjust system threshold rules.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        
        {/* Left Column (Main Settings Cards) */}
        <div className="md:col-span-2 space-y-6">
          
          {/* Card 1: Recommendation Engine Weights */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-5">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Sliders className="h-4.5 w-4.5 text-blue-500" />
              <h3 className="font-semibold text-sm">Matching Dimension Weights</h3>
            </div>
            
            <p className="text-xs text-muted-foreground leading-normal">
              Adjust how the Recommendation Engine ranks benched candidates. Weights must equal exactly <strong className="text-foreground">100%</strong>.
            </p>

            <div className="space-y-4">
              {/* Skill Match Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-foreground">Core Skills Compatibility</span>
                  <span className="text-blue-600 dark:text-blue-400">{skillWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={skillWeight}
                  onChange={e => setSkillWeight(parseInt(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer h-1 bg-border rounded-lg"
                />
              </div>

              {/* Competency Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-foreground">Role Competencies Index</span>
                  <span className="text-blue-600 dark:text-blue-400">{compWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={compWeight}
                  onChange={e => setCompWeight(parseInt(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer h-1 bg-border rounded-lg"
                />
              </div>

              {/* Availability Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-foreground">FTE Capacity Availability</span>
                  <span className="text-blue-600 dark:text-blue-400">{availWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={availWeight}
                  onChange={e => setAvailWeight(parseInt(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer h-1 bg-border rounded-lg"
                />
              </div>

              {/* Similarity Slider */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-foreground">Historical Account Similarity</span>
                  <span className="text-blue-600 dark:text-blue-400">{simWeight}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={simWeight}
                  onChange={e => setSimWeight(parseInt(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer h-1 bg-border rounded-lg"
                />
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-border/60 pt-4 shrink-0">
              <span className="text-xs font-semibold text-muted-foreground">
                Sum Total: <span className={skillWeight + compWeight + availWeight + simWeight === 100 ? "text-emerald-500 font-bold" : "text-red-500 font-bold"}>
                  {skillWeight + compWeight + availWeight + simWeight}%
                </span>
              </span>
              <Button
                onClick={handleSaveWeights}
                className="text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded h-8 px-5"
              >
                Save Engine Weights
              </Button>
            </div>
          </div>

          {/* Card 2: Synchronization Pools */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Database className="h-4.5 w-4.5 text-blue-500" />
              <h3 className="font-semibold text-sm">Cluster Integrations Sync</h3>
            </div>
            
            <div className="space-y-3.5">
              {[
                { key: "relational", name: "PostgreSQL Relational DB", desc: "Sync active employee payrolls and project allocations." },
                { key: "vector", name: "Qdrant Semantic Vectors", desc: "Build AI profiles and compile sentence embedding vectors." },
                { key: "crm", name: "Hubspot CRM Deal Flow", desc: "Ingest pipeline logs and anticipated project vacancies." }
              ].map(sync => (
                <div key={sync.key} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-lg border border-border/80 bg-muted/10">
                  <div>
                    <h4 className="font-semibold text-xs text-foreground">{sync.name}</h4>
                    <p className="text-[10px] text-muted-foreground leading-normal mt-0.5">{sync.desc}</p>
                    <span className="text-[9px] font-semibold text-blue-600 dark:text-blue-400 block mt-1">Status: {syncStatus[sync.key]}</span>
                  </div>
                  <Button
                    variant="outline"
                    size="xs"
                    disabled={syncLoading[sync.key]}
                    onClick={() => handleSync(sync.key, sync.name)}
                    className="h-8 text-[11px] font-semibold border-border rounded shrink-0 flex items-center gap-1.5"
                  >
                    <RefreshCw className={`h-3 w-3 text-muted-foreground ${syncLoading[sync.key] ? "animate-spin text-blue-600" : ""}`} />
                    {syncLoading[sync.key] ? "Syncing..." : "Sync Database"}
                  </Button>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Column (Sidebar Settings Cards) */}
        <div className="space-y-6">
          
          {/* Card 3: LLM Model Configurations */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Cpu className="h-4.5 w-4.5 text-blue-500" />
              <h3 className="font-semibold text-sm">AI Orchestration LLM</h3>
            </div>
            
            <div className="space-y-2">
              {[
                { id: "qwen", label: "Qwen 2.5 7B (Instruct)", desc: "Local Ollama engine, high speed, CPU safe." },
                { id: "gemini", label: "Gemini 1.5 Pro API", desc: "Google cloud provider, advanced system logic." },
                { id: "llama", label: "Llama 3 8B (Groq)", desc: "Groq cloud provider, lightning execution speed." }
              ].map(model => (
                <div
                  key={model.id}
                  onClick={() => {
                    setActiveModel(model.id)
                    addToast(`LLM orchestrator model switched to ${model.label.split(" ")[0]}`, "info")
                  }}
                  className={`p-3 rounded-lg border transition-all cursor-pointer flex items-start gap-2.5 ${
                    activeModel === model.id
                      ? "border-blue-600 bg-blue-600/10 text-blue-600 dark:border-blue-400 dark:bg-blue-500/15 dark:text-blue-400 font-semibold"
                      : "border-border hover:bg-muted/30 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <BrainCircuit className="h-4.5 w-4.5 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-xs text-foreground block">{model.label}</span>
                    <span className="text-[10px] text-muted-foreground font-normal leading-normal">{model.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card 4: Notification Rules / Thresholds */}
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <Bell className="h-4.5 w-4.5 text-blue-500" />
              <h3 className="font-semibold text-sm">Alert Rule thresholds</h3>
            </div>

            <div className="space-y-3.5 text-xs font-sans">
              <div className="space-y-1.5">
                <div className="flex justify-between font-semibold">
                  <span className="text-muted-foreground">Min. Utilization Threshold</span>
                  <span className="text-foreground">{minUtil}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="90"
                  step="5"
                  value={minUtil}
                  onChange={e => setMinUtil(parseInt(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer h-1"
                />
                <p className="text-[9px] text-muted-foreground leading-normal">
                  Fires an Amber warning notification if average allocation rates drop below this count.
                </p>
              </div>

              <div className="space-y-1.5 border-t border-border/50 pt-3">
                <div className="flex justify-between font-semibold">
                  <span className="text-muted-foreground">Max. Target Project Delay</span>
                  <span className="text-foreground">{maxDelay} Days</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="30"
                  step="1"
                  value={maxDelay}
                  onChange={e => setMaxDelay(parseInt(e.target.value))}
                  className="w-full accent-blue-600 cursor-pointer h-1"
                />
                <p className="text-[9px] text-muted-foreground leading-normal">
                  Fires a critical Red flag alert if dynamic project timelines delay exceeds this threshold.
                </p>
              </div>
            </div>

            <div className="pt-2 border-t border-border/50">
              <Button
                onClick={() => addToast("Alert thresholds saved successfully.", "success")}
                className="w-full text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded h-8"
              >
                Save Alert Thresholds
              </Button>
            </div>
          </div>

        </div>

      </div>

    </div>
  )
}
