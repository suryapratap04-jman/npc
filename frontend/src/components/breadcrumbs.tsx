"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronRight, Home } from "lucide-react"

export function Breadcrumbs() {
  const pathname = usePathname()
  const paths = pathname.split("/").filter((x) => x)

  return (
    <nav className="flex items-center gap-1.5 text-xs text-muted-foreground font-sans">
      <span className="text-muted-foreground/80 hover:text-foreground transition-all duration-150 cursor-pointer font-medium">
        Analytics
      </span>
      
      {paths.length > 0 && <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60" />}
      
      {paths.map((path, idx) => {
        const href = "/" + paths.slice(0, idx + 1).join("/")
        const isLast = idx === paths.length - 1
        const label = path
          .replace(/-/g, " ")
          .replace(/\b\w/g, (char) => char.toUpperCase())

        return (
          <React.Fragment key={href}>
            {isLast ? (
              <span className="font-semibold text-foreground">{label}</span>
            ) : (
              <>
                <Link href={href} className="hover:text-foreground transition-all duration-150">
                  {label}
                </Link>
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60" />
              </>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}
