"use client"

import React, { useEffect, useState } from "react"
import { ShieldAlert, RotateCcw, HelpCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function ErrorBoundary({ error, reset }: ErrorProps) {
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    // Log error to monitoring logs
    console.error("ErrorBoundary caught error:", error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center font-sans space-y-6 max-w-lg mx-auto px-4 text-foreground">
      <div className="h-16 w-16 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center shrink-0 border border-red-500/20 shadow-inner">
        <ShieldAlert className="h-8 w-8" />
      </div>

      <div className="space-y-2">
        <h2 className="text-3xl font-extrabold tracking-tight">System Deficit (500 Error)</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          An unexpected error occurred during execution. The platform engines encountered a rendering exception.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 w-full justify-center pt-2">
        <Button 
          onClick={() => reset()}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-md h-9 text-xs font-semibold flex items-center justify-center gap-1.5 shadow-sm px-6"
        >
          <RotateCcw className="h-4 w-4" /> Try Resetting Page
        </Button>
        <Button 
          variant="outline" 
          onClick={() => setShowDetails(!showDetails)}
          className="border-border hover:bg-muted/50 rounded-md h-9 text-xs font-semibold flex items-center justify-center gap-1.5 px-6"
        >
          <HelpCircle className="h-4 w-4 text-muted-foreground" /> 
          {showDetails ? "Hide Log Stack" : "Show Log Stack"}
        </Button>
      </div>

      <AnimatePresence>
        {showDetails && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="w-full text-left bg-muted/60 p-4 rounded-xl border border-border/80 font-mono text-[10px] text-muted-foreground overflow-x-auto space-y-1 max-h-48"
          >
            <p className="font-semibold text-foreground">Error Digest: {error.digest || "N/A"}</p>
            <p className="leading-relaxed whitespace-pre-wrap">{error.message || error.toString()}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Add AnimatePresence and motion wrappers if needed locally since next.js error boundary can be lightweight
import { motion, AnimatePresence } from "framer-motion"
