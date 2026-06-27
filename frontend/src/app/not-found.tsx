"use client"

import React from "react"
import Link from "next/link"
import { AlertCircle, ArrowLeft, Search } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center font-sans space-y-6 max-w-md mx-auto px-4 text-foreground">
      <div className="h-16 w-16 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center shrink-0 border border-red-500/20 shadow-inner">
        <AlertCircle className="h-8 w-8" />
      </div>

      <div className="space-y-2">
        <h2 className="text-3xl font-extrabold tracking-tight">404 - Page Not Found</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          We couldn't find the page you are looking for. It may have been relocated, or the URL might contain a typo.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 w-full pt-2">
        <Link href="/dashboard" className="flex-1">
          <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-md h-9 text-xs font-semibold flex items-center justify-center gap-1.5 shadow-sm">
            <ArrowLeft className="h-4 w-4" /> Back to Dashboard
          </Button>
        </Link>
        <Link href="/search" className="flex-1">
          <Button variant="outline" className="w-full border-border hover:bg-muted/50 rounded-md h-9 text-xs font-semibold flex items-center justify-center gap-1.5">
            <Search className="h-4 w-4 text-muted-foreground" /> Search Platform
          </Button>
        </Link>
      </div>
    </div>
  )
}
