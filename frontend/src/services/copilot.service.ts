import { fetchAPI } from "./api"

export interface CopilotChatRequest {
  message: string
  session_id?: string
}

export interface CopilotChatResponse {
  response: string
  detected_intent: string
  intent_confidence: number
  suggested_questions: string[]
  executed_tools: string[]
}

export interface ChatMessage {
  role: string
  content: string
  timestamp: number
}

export interface ConversationHistoryResponse {
  session_id: string
  history: ChatMessage[]
}

export const copilotService = {
  async chat(req: CopilotChatRequest): Promise<CopilotChatResponse> {
    return fetchAPI<CopilotChatResponse>("/api/copilot/chat", {
      method: "POST",
      body: JSON.stringify({
        message: req.message,
        session_id: req.session_id || "default"
      })
    })
  },

  async getHistory(sessionId: string = "default"): Promise<ConversationHistoryResponse> {
    return fetchAPI<ConversationHistoryResponse>(`/api/copilot/history?session_id=${sessionId}`)
  }
}
