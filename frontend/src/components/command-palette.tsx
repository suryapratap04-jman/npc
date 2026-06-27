"use client"

import React, { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { Search, X, LayoutDashboard, UserCheck, ShieldAlert, TrendingUp, MessageSquare, SearchCode, BarChart3, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [selectedIndex, setSelectedIndex] = useState(0)
  const listRef = useRef<HTMLDivElement>(null)

  const items = [
    { icon: LayoutDashboard, label: "Go to Executive Dashboard", path: "/dashboard", shortcut: "G D" },
    { icon: UserCheck, label: "Go to Resource Matcher", path: "/recommendation", shortcut: "G R" },
    { icon: ShieldAlert, label: "Go to Project Health Status", path: "/project-health", shortcut: "G H" },
    { icon: TrendingUp, label: "Go to Forecast & Planning", path: "/forecast", shortcut: "G F" },
    { icon: MessageSquare, label: "Go to AI Copilot Center", path: "/copilot", shortcut: "G C" },
    { icon: SearchCode, label: "Go to Advanced Search", path: "/search", shortcut: "G S" },
    { icon: BarChart3, label: "Go to Operational Reports", path: "/reports", shortcut: "G R" },
    { icon: Settings, label: "Go to Platform Settings", path: "/settings", shortcut: "G P" }
  ]

  const filteredItems = items.filter(item =>
    item.label.toLowerCase().includes(query.toLowerCase())
  )

  useEffect(() => {
    if (isOpen) {
      setQuery("")
      setSelectedIndex(0)
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = "unset"
    }
    return () => {
      document.body.style.overflow = "unset"
    }
  }, [isOpen])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      if (e.key === "Escape") {
        e.preventDefault()
        onClose()
      } else if (e.key === "ArrowDown") {
        e.preventDefault()
        setSelectedIndex(prev => (prev + 1) % filteredItems.length)
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setSelectedIndex(prev => (prev - 1 + filteredItems.length) % filteredItems.length)
      } else if (e.key === "Enter") {
        e.preventDefault()
        if (filteredItems[selectedIndex]) {
          handleSelect(filteredItems[selectedIndex].path)
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, selectedIndex, filteredItems, onClose])

  const handleSelect = (path: string) => {
    router.push(path)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-background/60 backdrop-blur-md transition-opacity duration-300 animate-in fade-in" onClick={onClose} />
      
      {/* Container */}
      <div className="relative w-full max-w-lg rounded-xl border border-border bg-card shadow-2xl p-4 animate-in fade-in-50 zoom-in-95 duration-200 ring-1 ring-black/5 dark:ring-white/10">
        <div className="flex items-center gap-3 border-b border-border pb-3">
          <Search className="h-5 w-5 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSelectedIndex(0)
            }}
            placeholder="Type to search pages and options..."
            className="flex-1 bg-transparent border-0 outline-none text-foreground placeholder:text-muted-foreground text-sm font-sans"
            autoFocus
          />
          <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            ESC
          </kbd>
          <Button variant="ghost" size="icon" className="h-6 w-6 rounded-full" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Suggestion list */}
        <div ref={listRef} className="mt-4 max-h-[300px] overflow-y-auto space-y-1 pr-1">
          <h4 className="text-xs font-semibold text-muted-foreground px-2 py-1.5 font-sans tracking-wider uppercase">
            Pages & Actions
          </h4>
          {filteredItems.length > 0 ? (
            filteredItems.map((item, idx) => {
              const Icon = item.icon
              const isSelected = idx === selectedIndex
              return (
                <button
                  key={item.path}
                  className={`w-full flex items-center justify-between rounded-lg p-2.5 text-sm text-foreground transition-all duration-150 group font-sans text-left ${
                    isSelected 
                      ? "bg-secondary text-secondary-foreground shadow-sm ring-1 ring-border" 
                      : "hover:bg-muted/50"
                  }`}
                  onClick={() => handleSelect(item.path)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4.5 w-4.5 transition-colors ${
                      isSelected ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                    }`} />
                    <span className={isSelected ? "font-semibold" : "font-medium"}>{item.label}</span>
                  </div>
                  <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-0.5 rounded bg-muted/60 border border-border/40 px-1.5 font-mono text-[9px] font-medium text-muted-foreground">
                    {item.shortcut}
                  </kbd>
                </button>
              )
            })
          ) : (
            <div className="text-center py-6 text-sm text-muted-foreground font-sans">
              No matching pages or tools found
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
