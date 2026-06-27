const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class APIError extends Error {
  status: number
  detail: any

  constructor(message: string, status: number, detail: any) {
    super(message)
    this.name = "APIError"
    this.status = status
    this.detail = detail
  }
}

interface CustomRequestOptions extends RequestInit {
  timeout?: number
  retries?: number
}

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function fetchAPI<T>(
  path: string,
  options: CustomRequestOptions = {}
): Promise<T> {
  const { timeout = 15000, retries = 2, ...initOptions } = options
  const url = `${BASE_URL}${path}`

  // Default headers
  const headers = new Headers(initOptions.headers || {})
  if (!headers.has("Content-Type") && !(initOptions.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }

  // Auth token placeholder (e.g., if we had a token session)
  const token = localStorage.getItem("token")
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  let attempt = 0
  while (attempt <= retries) {
    const controller = new AbortController()
    const id = setTimeout(() => controller.abort(), timeout)

    try {
      const response = await fetch(url, {
        ...initOptions,
        headers,
        signal: controller.signal,
      })

      clearTimeout(id)

      if (!response.ok) {
        let detail = "An error occurred on the API server."
        try {
          const errData = await response.json()
          detail = errData.detail || errData.message || detail
        } catch (_) {
          // Fallback to text if JSON parse fails
          try {
            detail = await response.text()
          } catch (_) { }
        }
        throw new APIError(
          `Request failed with status ${response.status}`,
          response.status,
          detail
        )
      }

      // Check content type before parsing JSON
      const contentType = response.headers.get("content-type")
      if (contentType && contentType.includes("application/json")) {
        return (await response.json()) as T
      }
      return (await response.text()) as unknown as T

    } catch (error: any) {
      clearTimeout(id)

      const isAbort = error.name === "AbortError"
      const isNetwork = error instanceof TypeError // network disconnect or CORS failure

      if ((isAbort || isNetwork) && attempt < retries) {
        attempt++
        loggerWarn(`Retry attempt ${attempt} for path: ${path} due to timeout/network error.`)
        await delay(1000 * attempt) // Exponential backoff
        continue
      }

      // If it is an API error, just throw it
      if (error instanceof APIError) {
        throw error
      }

      // Fallback generic error
      throw new APIError(
        isAbort ? "Request timed out" : error.message || "Network request failed",
        isAbort ? 408 : 500,
        null
      )
    }
  }

  throw new APIError("Request failed after max retries", 500, null)
}

function loggerWarn(msg: string) {
  console.warn(`[API Client Warning]: ${msg}`)
}
