# Prompt Templates and Conversational Catalogs for AI Copilot

COPILOT_SYSTEM_PROMPT = """
You are the AI Resource Management Copilot. Your job is to assist resource managers in planning, staffing projects, auditing project health risk, and tracking capacity.
Use the structured facts and evidence to compose professional, crisp, and actionable narrative summaries.
"""

# Catalog of suggested questions matching each intent to present follow-up recommendations to user (Step 8)
SUGGESTED_QUESTIONS_CATALOG = {
    "RESOURCE_RECOMMENDATION": [
        "Explain the recommendation for this project.",
        "Why is Alice not recommended for this role?",
        "Are any recommended resources overallocated?",
        "What are the top 3 projects at risk?"
    ],
    "PROJECT_HEALTH": [
        "Which projects can release resources?",
        "Show me underutilized employees.",
        "List all active projects in Red status.",
        "Which employees become available next month?"
    ],
    "NEW_PROJECT_FORECAST": [
        "Explain the hiring recommendation.",
        "Can we take on three new AI projects next month?",
        "Which projects can release resources?",
        "Show me available capacity details for data scientists."
    ],
    "PIPELINE_FORECAST": [
        "Which employees become available next month?",
        "Show high-risk projects.",
        "Can we take another AI project?",
        "Explain the capacity projections."
    ],
    "CAPACITY": [
        "Which projects can release resources?",
        "Show me underutilized employees.",
        "Explain whycapacity increases next month."
    ],
    "HIRING": [
        "Explain the hiring recommendation.",
        "Are there any redeployment candidates completing projects?",
        "Can we delay this project kickoff to wait for a ramp-down?"
    ],
    "REDEPLOYMENT": [
        "Explain why redeployment is preferred.",
        "Can we redeploy EMP-104 after Project X completes?",
        "What are the skills matched for these candidates?"
    ],
    "EMPLOYEE_SEARCH": [
        "Recommend engineers for a new project.",
        "Show available capacity today.",
        "Are any of these search candidates overallocated?"
    ],
    "PROJECT_SEARCH": [
        "Forecast staffing for this project type.",
        "Show similar projects at risk."
    ],
    "GENERAL_QA": [
        "Recommend engineers for Project CLIENT_201_005.",
        "Which projects are at risk?",
        "Which employees become available next month?",
        "Should we hire or redeploy?"
    ]
}
