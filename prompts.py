import json
from typing import Dict, Any

FOSS_CATEGORIES = [
    "Git & Version Control",
    "Linux & Shell Scripting",
    "Open Source Licensing & Ethics",
    "Open Source Programs & GSoC",
    "Programming & Bug Debugging",
    "FOSS Alternatives & Tools",
    "DevOps, Docker & Self-Hosting",
    "General FOSS & Community"
]

SYSTEM_PROMPT_FOSS_MENTOR = """You are "Tuxie", the official AI Mentor for FOSS MBCCET (Free and Open Source Software Cell at Mar Baselios Christian College of Engineering & Technology).

Your Mission:
1. Educate engineering students on FOSS tools, Linux, Git, programming errors, open source licensing, and contribution programs (GSoC, Hacktoberfest).
2. Answer doubts with maximum precision, actionable clarity, and clean structure.

Response Rules:
• Keep direct_answer CONCISE, PRECISE, and DIRECT TO THE POINT (2 to 4 punchy sentences or clear bullets).
• Do NOT write long verbose essays, unnecessary introductory chatter, or generic fluff.
• ALWAYS provide runnable terminal commands or code in `terminal_commands_or_code`.
• Provide a single, crisp, high-value pro-tip in `foss_tip`.
• ONLY give detailed long explanations if the user explicitly asks for "more detail", "more info", "in-depth", or "explain thoroughly".
"""

CLASSIFICATION_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": FOSS_CATEGORIES
        },
        "subcategory": {
            "type": "string",
            "description": "Specific sub-topic, e.g., 'Merge Conflict', 'File Permissions (chmod)', 'Copyleft vs Permissive', 'GSoC Proposal', 'Memory Leak'"
        },
        "difficulty": {
            "type": "string",
            "enum": ["Beginner", "Intermediate", "Advanced"]
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-5 relevant keywords/tags (e.g. ['git', 'rebase', 'vcs'])"
        },
        "summary": {
            "type": "string",
            "description": "A crisp 1-line summary of what the student is asking"
        },
        "direct_answer": {
            "type": "string",
            "description": "Comprehensive, encouraging, step-by-step technical explanation and solution"
        },
        "terminal_commands_or_code": {
            "type": "string",
            "description": "Exact commands or code snippets the user can copy-paste, formatted in markdown"
        },
        "recommended_foss_tools": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of relevant open source tools, libraries, or projects"
        },
        "foss_tip": {
            "type": "string",
            "description": "A short, fun, educational FOSS trivia or command line pro-tip"
        }
    },
    "required": [
        "category", "subcategory", "difficulty", "tags",
        "summary", "direct_answer", "terminal_commands_or_code",
        "recommended_foss_tools", "foss_tip"
    ]
}

def get_text_query_prompt(user_query: str) -> str:
    return f"""A student from FOSS MBCCET has submitted the following doubt/inquiry:
\"\"\"{user_query}\"\"\"

Please analyze this inquiry, categorize it thoroughly, and provide a comprehensive pedagogical answer.
Respond in VALID JSON matching this exact structure:
{{
  "category": "One of: {', '.join(FOSS_CATEGORIES)}",
  "subcategory": "Specific topic",
  "difficulty": "Beginner | Intermediate | Advanced",
  "tags": ["tag1", "tag2", "tag3"],
  "summary": "1-sentence summary",
  "direct_answer": "Detailed solution and conceptual explanation",
  "terminal_commands_or_code": "Markdown code block of terminal commands or code fixes",
  "recommended_foss_tools": ["Tool1", "Tool2"],
  "foss_tip": "Quick hacker pro-tip related to this topic"
}}
"""

def get_vision_query_prompt(caption: str = "") -> str:
    caption_context = f"\nUser Caption/Context: {caption}" if caption else ""
    return f"""The student has shared a screenshot or photo of their computer screen, terminal, code editor, or build error.{caption_context}

Perform an OCR and technical diagnostic:
1. Identify the exact error message, stack trace, or terminal state shown in the image.
2. Determine the root cause of why this failure or situation occurred.
3. Classify the problem into the appropriate FOSS category.
4. Provide step-by-step terminal commands or code modifications to resolve it cleanly.

Respond in VALID JSON matching this exact structure:
{{
  "category": "One of: {', '.join(FOSS_CATEGORIES)}",
  "subcategory": "Specific topic",
  "difficulty": "Beginner | Intermediate | Advanced",
  "tags": ["tag1", "tag2", "tag3"],
  "summary": "1-sentence summary of the detected visual error",
  "direct_answer": "Diagnosis of the error from the screenshot and how to fix it",
  "terminal_commands_or_code": "Precise terminal commands or code to fix the issue",
  "recommended_foss_tools": ["Tool1", "Tool2"],
  "foss_tip": "Pro-tip on preventing or debugging this type of issue"
}}
"""
