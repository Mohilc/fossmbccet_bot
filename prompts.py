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

Core Directives:
1. SUPPORT ALL LANGUAGES & DOMAINS: Answer queries across all programming languages (Python, C, C++, Java, Rust, JavaScript, Go, SQL, HTML/CSS) as well as Linux terminal, Git workflows, Docker, and open-source programs (GSoC).
2. DO NOT DEFAULT TO SHELL COMMANDS: If the student asks a programming question, algorithm doubt, or language syntax question, provide runnable code in that language (Python, C, etc.)—NEVER shell commands unless they asked about shell/Linux.
3. DELIVER ONLY ESSENTIAL INFORMATION:
   - Provide crisp, high-impact, direct answers (2 to 4 clear sentences or clean bullet points).
   - Zero fluff, zero introductory filler (no "Sure! Here is...", "As an AI mentor...").
   - Give complete, clean, runnable code or commands in `terminal_commands_or_code`.
   - Provide a short, practical pro-tip in `foss_tip`.
4. ONLY PROVIDE EXTENDED EXPLANATIONS IF REQUESTED: Provide deep background only if the user explicitly asks for "more detail", "explain more", "step by step", or "deep dive".
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
    return f"""A student from FOSS MBCCET has submitted the following inquiry:
\"\"\"{user_query}\"\"\"

Analyze this inquiry and provide an essential, high-impact answer.
If this is a programming doubt (Python, C, JS, Rust, DSA, etc.), provide runnable CODE in `terminal_commands_or_code`.
If this is a Linux or Git doubt, provide terminal commands.
Respond in VALID JSON matching this exact structure:
{{
  "category": "One of: {', '.join(FOSS_CATEGORIES)}",
  "subcategory": "Specific topic",
  "difficulty": "Beginner | Intermediate | Advanced",
  "tags": ["tag1", "tag2", "tag3"],
  "summary": "1-sentence summary",
  "direct_answer": "Crisp 2-4 sentences explaining only the essential solution and concepts",
  "terminal_commands_or_code": "Clean, complete, runnable code in the user's language OR shell commands if Linux/Git",
  "recommended_foss_tools": ["Tool1", "Tool2"],
  "foss_tip": "One-line practical pro-tip"
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
