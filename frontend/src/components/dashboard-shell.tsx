"use client"

import React, { useState, useEffect } from "react"
import { usePathname } from "next/navigation"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import {
  LayoutDashboard,
  UserCheck,
  ShieldAlert,
  TrendingUp,
  MessageSquare,
  Search,
  Bell,
  PanelLeftClose,
  PanelLeft,
  ChevronDown,
  Sparkles,
  Menu,
  X,
  Send,
  Settings,
  HelpCircle,
  LogOut,
  BarChart3,
  Info
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { Breadcrumbs } from "@/components/breadcrumbs"
import { CommandPalette } from "@/components/command-palette"
import { useToastStore } from "@/store/useToastStore"

interface DashboardShellProps {
  children: React.ReactNode
}

export function DashboardShell({ children }: DashboardShellProps) {
  const pathname = usePathname()
  const toasts = useToastStore((s) => s.toasts)
  const removeToast = useToastStore((s) => s.removeToast)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  
  // Notification and profile dropdown toggle state
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)

  // Listen for Ctrl+K global keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setIsCommandPaletteOpen((prev) => !prev)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const menuItems = [
    { id: "dashboard", label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { id: "recommendation", label: "Recommendation", path: "/recommendation", icon: UserCheck },
    { id: "project-health", label: "Project Health", path: "/project-health", icon: ShieldAlert },
    { id: "forecast", label: "Forecast", path: "/forecast", icon: TrendingUp },
    { id: "copilot", label: "Copilot", path: "/copilot", icon: MessageSquare },
    { id: "search", label: "Search", path: "/search", icon: Search },
    { id: "reports", label: "Reports", path: "/reports", icon: BarChart3 },
    { id: "settings", label: "Settings", path: "/settings", icon: Settings },
  ]

  const activeItem = menuItems.find(
    (item) => pathname === item.path || (item.path === "/dashboard" && pathname === "/")
  ) || menuItems[0]

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground font-sans">
      
      {/* 1. Desktop Left Sidebar */}
      <motion.aside
        animate={{ width: isSidebarCollapsed ? 64 : 240 }}
        transition={{ duration: 0.2, ease: "easeInOut" }}
        className="hidden md:flex flex-col h-full border-r border-border bg-card/50 backdrop-blur-md z-30 sticky top-0 shrink-0"
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between px-4 border-b border-border h-14">
          {!isSidebarCollapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 font-bold text-base tracking-tight text-foreground"
            >
              <div className="h-6 w-6 rounded bg-blue-600 flex items-center justify-center text-white font-extrabold text-xs shadow-sm">
                A
              </div>
              <span className="font-semibold text-foreground/90">Atlassian Analytics</span>
            </motion.div>
          )}
          {isSidebarCollapsed && (
            <div className="h-6 w-6 rounded bg-blue-600 flex items-center justify-center text-white font-extrabold text-xs mx-auto shadow-sm">
              A
            </div>
          )}
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="h-7 w-7 text-muted-foreground hover:text-foreground hidden md:flex hover:bg-muted/50 rounded"
          >
            {isSidebarCollapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </Button>
        </div>

        {/* Sidebar Middle Navigation */}
        <nav className="flex-1 px-2.5 py-4 space-y-1 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.path || (item.path === "/dashboard" && pathname === "/")
            return (
              <Link
                key={item.id}
                href={item.path}
                className={`w-full flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all duration-200 group relative ${
                  isActive
                    ? "bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 font-semibold"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                }`}
              >
                <Icon className={`h-4.5 w-4.5 shrink-0 transition-colors ${
                  isActive ? "text-blue-600 dark:text-blue-400" : "text-muted-foreground group-hover:text-foreground"
                }`} />
                {!isSidebarCollapsed ? (
                  <motion.span 
                    initial={{ opacity: 0 }} 
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.15 }}
                  >
                    {item.label}
                  </motion.span>
                ) : (
                  <span className="absolute left-full ml-3 px-2 py-1 bg-popover text-popover-foreground text-xs font-normal rounded border border-border shadow-md opacity-0 group-hover:opacity-100 translate-x-1 group-hover:translate-x-0 pointer-events-none transition-all duration-150 whitespace-nowrap z-50">
                    {item.label}
                  </span>
                )}
                {/* Atlassian Analytics styled left indicator */}
                {isActive && (
                  <div className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-blue-600 dark:bg-blue-400 rounded-r" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-2.5 border-t border-border space-y-0.5">
          <Link 
            href="/settings"
            className="w-full flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors group relative"
          >
            <Settings className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-foreground" />
            {!isSidebarCollapsed ? (
              <span>Settings</span>
            ) : (
              <span className="absolute left-full ml-3 px-2 py-1 bg-popover text-popover-foreground text-xs font-normal rounded border border-border shadow-md opacity-0 group-hover:opacity-100 translate-x-1 group-hover:translate-x-0 pointer-events-none transition-all duration-150 whitespace-nowrap z-50">
                Settings
              </span>
            )}
          </Link>
          <a 
            href="https://atlassian.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="w-full flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted/50 hover:text-foreground transition-colors group relative"
          >
            <HelpCircle className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-foreground" />
            {!isSidebarCollapsed ? (
              <span>Help Center</span>
            ) : (
              <span className="absolute left-full ml-3 px-2 py-1 bg-popover text-popover-foreground text-xs font-normal rounded border border-border shadow-md opacity-0 group-hover:opacity-100 translate-x-1 group-hover:translate-x-0 pointer-events-none transition-all duration-150 whitespace-nowrap z-50">
                Help Center
              </span>
            )}
          </a>
        </div>
      </motion.aside>

      {/* 2. Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isMobileSidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
              onClick={() => setIsMobileSidebarOpen(false)}
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 z-50 w-72 border-r border-border bg-card p-4 flex flex-col md:hidden"
            >
              <div className="flex items-center justify-between pb-4 border-b border-border">
                <div className="flex items-center gap-2 font-bold text-base">
                  <div className="h-6 w-6 rounded bg-blue-600 flex items-center justify-center text-white font-extrabold text-xs shadow-sm">
                    A
                  </div>
                  <span className="font-semibold text-foreground/90">Atlassian Analytics</span>
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 rounded" onClick={() => setIsMobileSidebarOpen(false)}>
                  <X className="h-4.5 w-4.5" />
                </Button>
              </div>
              <nav className="flex-1 py-4 space-y-1">
                {menuItems.map((item) => {
                  const Icon = item.icon
                  const isActive = pathname === item.path || (item.path === "/dashboard" && pathname === "/")
                  return (
                    <Link
                      key={item.id}
                      href={item.path}
                      onClick={() => setIsMobileSidebarOpen(false)}
                      className={`w-full flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-blue-600/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400 font-semibold"
                          : "text-muted-foreground hover:bg-muted/50"
                      }`}
                    >
                      <Icon className="h-4.5 w-4.5" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* 3. Main Outer Container */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        
        {/* Sticky Topbar Navbar */}
        <header className="sticky top-0 z-20 flex h-14 w-full items-center justify-between border-b border-border bg-card/60 backdrop-blur-md px-4 md:px-6 shrink-0">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden h-8 w-8 text-muted-foreground hover:text-foreground rounded"
              onClick={() => setIsMobileSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            
            {/* Breadcrumbs */}
            <Breadcrumbs />
          </div>

          {/* Topbar Search and Actions */}
          <div className="flex items-center gap-3.5">
            {/* Search Command Palette Input */}
            <button
              onClick={() => setIsCommandPaletteOpen(true)}
              className="hidden md:flex items-center gap-2 rounded-md border border-border bg-muted/65 px-3 py-1.5 text-xs text-muted-foreground hover:border-muted-foreground/40 hover:bg-muted transition-all w-56 text-left shadow-inner cursor-pointer"
            >
              <Search className="h-3.5 w-3.5" />
              <span>Search platform...</span>
              <kbd className="ml-auto pointer-events-none inline-flex h-4.5 select-none items-center gap-0.5 rounded border bg-background px-1.5 font-mono text-[9px] font-medium text-muted-foreground">
                Ctrl K
              </kbd>
            </button>
            
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden text-muted-foreground hover:text-foreground rounded"
              onClick={() => setIsCommandPaletteOpen(true)}
            >
              <Search className="h-4.5 w-4.5" />
            </Button>

            {/* Notification Dropdown Container */}
            <div className="relative">
              <Button
                variant="ghost"
                size="icon"
                className={`relative h-8 w-8 text-muted-foreground hover:text-foreground rounded-md transition-colors ${
                  showNotifications ? "bg-muted/70 text-foreground" : "hover:bg-muted/50"
                }`}
                onClick={() => {
                  setShowNotifications(!showNotifications)
                  setShowProfile(false)
                }}
              >
                <Bell className="h-4.5 w-4.5" />
                <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-red-500 ring-2 ring-background animate-pulse" />
              </Button>
              
              <AnimatePresence>
                {showNotifications && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 mt-2 w-80 rounded-xl border border-border bg-card shadow-2xl p-4 z-50 animate-in"
                    >
                      <div className="flex items-center justify-between border-b border-border pb-2 mb-2">
                        <span className="font-semibold text-sm text-foreground font-sans">Notifications</span>
                        <Button variant="link" size="sm" className="text-xs p-0 h-auto text-blue-600 dark:text-blue-400 hover:no-underline">Mark all read</Button>
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-start gap-3 p-1.5 rounded-md hover:bg-muted/40 cursor-pointer transition-colors">
                          <div className="h-2 w-2 rounded-full bg-red-500 mt-1.5 shrink-0" />
                          <div>
                            <p className="text-xs font-semibold text-foreground leading-normal">Project CLI-201 Red Flagged</p>
                            <p className="text-[10px] text-muted-foreground mt-0.5 leading-snug">Audit health checks indicate critical schedule delay.</p>
                          </div>
                        </div>
                        <div className="flex items-start gap-3 p-1.5 rounded-md hover:bg-muted/40 cursor-pointer transition-colors">
                          <div className="h-2 w-2 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                          <div>
                            <p className="text-xs font-semibold text-foreground leading-normal">New Forecast Plan Generated</p>
                            <p className="text-[10px] text-muted-foreground mt-0.5 leading-snug">Q3 resource capacity estimates are now available.</p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

            {/* Theme switcher */}
            <ThemeToggle />

            {/* AI Insights Sidebar Toggle */}
            <Button
              variant={isRightPanelOpen ? "secondary" : "ghost"}
              onClick={() => setIsRightPanelOpen(!isRightPanelOpen)}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-md border border-border bg-indigo-500/5 hover:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 shadow-sm"
            >
              <Sparkles className="h-3.5 w-3.5 text-indigo-500 dark:text-indigo-400" />
              <span className="hidden sm:inline">AI Insights</span>
            </Button>

            {/* User Profile avatar dropdown */}
            <div className="relative">
              <button
                className="flex items-center gap-1.5 hover:opacity-85 transition-opacity outline-none"
                onClick={() => {
                  setShowProfile(!showProfile)
                  setShowNotifications(false)
                }}
              >
                <div className="h-7 w-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-sm select-none">
                  SP
                </div>
                <ChevronDown className="h-3 w-3 text-muted-foreground hidden sm:block" />
              </button>

              <AnimatePresence>
                {showProfile && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowProfile(false)} />
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-card shadow-2xl p-2 z-50 text-sm font-sans"
                    >
                      <div className="px-3 py-2 border-b border-border mb-1 text-xs">
                        <p className="font-semibold text-foreground">Surya Pratap Singh</p>
                        <p className="text-muted-foreground text-[10px] truncate mt-0.5">suryapratapsingh@jman.com</p>
                      </div>
                      <Link 
                        href="/settings"
                        onClick={() => setShowProfile(false)}
                        className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-left hover:bg-muted/70 text-foreground transition-all text-xs"
                      >
                        <Settings className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>Account settings</span>
                      </Link>
                      <button className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-left hover:bg-muted/70 text-foreground transition-all border-t border-border mt-1 pt-2 text-red-500 hover:text-red-600 hover:bg-red-500/5 text-xs">
                        <LogOut className="h-3.5 w-3.5" />
                        <span>Sign out</span>
                      </button>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        {/* Outer Workspace containing Main panel + Right AI Panel */}
        <div className="flex-1 flex w-full overflow-hidden relative">
          
          {/* Main Content scroll window */}
          <main className="flex-1 h-full overflow-y-auto p-4 md:p-6 bg-muted/10 relative">
            <div className="max-w-6xl mx-auto space-y-6">
              {children}
            </div>
          </main>

          {/* 4. Right AI Context Panel (Sliding collapsible sidepanel) */}
          <AnimatePresence>
            {isRightPanelOpen && (
              <motion.aside
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 340, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ type: "spring", damping: 30, stiffness: 250 }}
                className="hidden lg:flex flex-col h-full border-l border-border bg-card/30 backdrop-blur-md w-[340px] shrink-0"
              >
                {/* Panel Header */}
                <div className="flex items-center justify-between p-4 border-b border-border h-14 shrink-0">
                  <div className="flex items-center gap-2 font-semibold text-sm">
                    <Sparkles className="h-4 w-4 text-indigo-500 dark:text-indigo-400" />
                    <span>AI Copilot Insights</span>
                  </div>
                  <Button variant="ghost" size="icon" className="h-7 w-7 rounded-full text-muted-foreground hover:bg-muted/50" onClick={() => setIsRightPanelOpen(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Panel Chat conversation placeholder list */}
                <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs font-sans">
                  <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-lg p-3.5 text-muted-foreground space-y-2.5">
                    <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 font-semibold">
                      <Info className="h-3.5 w-3.5 shrink-0" />
                      <span>Active Page Context</span>
                    </div>
                    <p className="leading-relaxed">
                      You are currently viewing the <strong className="text-foreground">{activeItem.label}</strong> page.
                    </p>
                    <p className="leading-relaxed">
                      Ask questions below to get contextual resource summaries, budget risk alerts, and pipeline diagnostic estimations.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex flex-col gap-1.5 max-w-[85%] rounded-2xl bg-muted/60 p-3 ml-auto text-foreground self-end font-medium">
                      <p className="leading-relaxed">Which active projects are currently at risk?</p>
                    </div>

                    <div className="flex flex-col gap-2 max-w-[90%] rounded-2xl bg-card border border-border p-3.5 mr-auto self-start shadow-sm ring-1 ring-black/5 dark:ring-white/5">
                      <div className="flex items-center gap-1.5 font-semibold text-indigo-600 dark:text-indigo-400">
                        <Sparkles className="h-3.5 w-3.5" />
                        <span>Copilot Assistant</span>
                      </div>
                      <p className="leading-relaxed text-muted-foreground">
                        I identified <strong className="text-foreground font-semibold">1 critical project</strong> flagged as Red (High Risk) due to allocation bottlenecks:
                      </p>
                      <div className="mt-1.5 p-2 rounded-md bg-muted/30 border border-border">
                        <span className="font-semibold text-foreground">Project CLI-201</span>
                        <span className="ml-2 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider bg-red-500/10 text-red-500 rounded">Critical Delay</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Panel Quick chat textbox input */}
                <div className="p-3 border-t border-border bg-card/20 shrink-0">
                  <div className="flex items-center gap-2 bg-muted/60 rounded-full border border-border px-3 py-1 shadow-inner hover:border-muted-foreground/35 transition-all">
                    <input
                      placeholder="Ask the copilot..."
                      className="flex-1 bg-transparent border-0 outline-none text-xs placeholder:text-muted-foreground text-foreground h-7"
                    />
                    <Button size="icon" className="h-7 w-7 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-sm shrink-0">
                      <Send className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </motion.aside>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* 5. Command Palette */}
      <CommandPalette isOpen={isCommandPaletteOpen} onClose={() => setIsCommandPaletteOpen(false)} />

      {/* Global Toasts List Overlay */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 15, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 15, scale: 0.95 }}
              className={`pointer-events-auto flex items-center justify-between gap-3 rounded-lg border p-3 shadow-lg text-xs font-semibold ${
                toast.type === "success"
                  ? "bg-emerald-600 border-emerald-500 text-white"
                  : toast.type === "error"
                  ? "bg-red-600 border-red-500 text-white"
                  : toast.type === "warning"
                  ? "bg-amber-500 border-amber-400 text-white"
                  : "bg-blue-600 border-blue-500 text-white"
              }`}
            >
              <span>{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-white/80 hover:text-white shrink-0 outline-none cursor-pointer"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
