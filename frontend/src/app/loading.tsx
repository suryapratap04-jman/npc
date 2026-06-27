import React from "react"

export default function Loading() {
  return (
    <div className="space-y-6 pb-12 font-sans animate-pulse">
      
      {/* Header Skeleton */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center justify-between">
        <div className="space-y-2">
          <div className="h-7 w-56 bg-muted rounded-md" />
          <div className="h-4 w-96 bg-muted rounded-sm" />
        </div>
        <div className="h-8 w-28 bg-muted rounded-md" />
      </div>

      {/* AI Summary Block Skeleton */}
      <div className="rounded-xl border border-border bg-card/40 p-5 space-y-2.5">
        <div className="h-5 w-32 bg-muted rounded" />
        <div className="h-4 w-full bg-muted rounded" />
        <div className="h-4 w-5/6 bg-muted rounded" />
      </div>

      {/* KPI Cards Skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-5 space-y-4">
            <div className="flex justify-between">
              <div className="h-3.5 w-24 bg-muted rounded" />
              <div className="h-4 w-4 bg-muted rounded" />
            </div>
            <div className="h-7 w-20 bg-muted rounded" />
            <div className="flex justify-between">
              <div className="h-3 w-16 bg-muted rounded" />
              <div className="h-3 w-20 bg-muted rounded" />
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid Skeleton */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5 space-y-4 min-h-[300px]">
          <div className="flex justify-between border-b border-border pb-3">
            <div className="space-y-1">
              <div className="h-4.5 w-36 bg-muted rounded" />
              <div className="h-3 w-48 bg-muted rounded" />
            </div>
            <div className="h-4.5 w-24 bg-muted rounded" />
          </div>
          <div className="h-[200px] w-full bg-muted/40 rounded-lg" />
        </div>

        <div className="rounded-xl border border-border bg-card p-5 space-y-4 min-h-[300px]">
          <div className="h-5 w-40 bg-muted rounded border-b border-border pb-3" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 w-full bg-muted/30 rounded-lg" />
            ))}
          </div>
        </div>
      </div>

    </div>
  )
}
