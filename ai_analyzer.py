import os
import re
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import httpx

from config import (
    GEMINI_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_VISION_KEY,
    NVIDIA_VISION_MODEL,
    NVIDIA_NEMOTRON_KEY,
    NVIDIA_NEMOTRON_MODEL,
    NVIDIA_MUSE_KEY,
    NVIDIA_MUSE_MODEL,
    NVIDIA_LAGUNA_KEY,
    NVIDIA_LAGUNA_MODEL,
    NVIDIA_KIMI_KEY,
    NVIDIA_KIMI_MODEL
)
from prompts import (
    SYSTEM_PROMPT_FOSS_MENTOR,
    FOSS_CATEGORIES,
    get_text_query_prompt,
    get_vision_query_prompt
)

class AIAnalyzer:
    """
    Multi-Engine Ensemble & Reasoning System for FOSS MBCCET.
    Orchestrates multiple AI engines and keys provided by the community:
      • Google DiffusionGemma 26b (Multimodal Visual OCR & Error Analysis)
      • Meta Muse Glimmer 30b (High-speed FOSS reasoning)
      • NVIDIA Nemotron 3.5 Lightning 30b (Deep Hacker logic & SysAdmin analysis)
      • Poolside Laguna XS (Developer Code analysis)
      • Moonshot Kimi-k3 (Deep Reasoning)
      • Google Gemini 1.5 Flash (Secondary Cloud Engine)
      • Local Pedagogical Heuristics (Zero-Downtime Fallback)
    """

    def __init__(self):
        self.nvidia_base_url = (NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.gemini_api_key = GEMINI_API_KEY
        self.gemini_model = "gemini-1.5-flash"

        # Vision Models Pool (Ordered by priority)
        self.vision_models: List[Tuple[str, str]] = [
            (NVIDIA_VISION_MODEL, NVIDIA_VISION_KEY),
        ]

        # Text Reasoning Models Pool (Ordered by priority & speed)
        self.text_models: List[Tuple[str, str]] = [
            (NVIDIA_NEMOTRON_MODEL, NVIDIA_NEMOTRON_KEY)
        ]

    @staticmethod
    def is_greeting(query: str) -> bool:
        """Determines if a query is a general greeting, intro, or onboarding prompt."""
        if not query:
            return True
            
        clean = re.sub(r"[^\w\s]", "", query).strip().lower()
        if not clean:
            return True

        greeting_set = {
            "hi", "hello", "hey", "hii", "hiii", "heyy", "heyyy", "hlo", "hlw",
            "hola", "yo", "sup", "howdy", "vanakkam", "namaste", "namaskaram",
            "hai", "haai", "good morning", "good afternoon", "good evening",
            "good day", "greetings", "start", "get started", "intro", "welcome",
            "who are you", "what can you do", "help me", "hi tuxie", "hello tuxie",
            "hey tuxie", "hi bot", "hello bot", "hey bot", "tuxie"
        }

        if clean in greeting_set:
            return True

        # Check if technical keywords are absent
        tech_words = [
            "git", "linux", "ubuntu", "bash", "code", "python", "docker", "error",
            "bug", "license", "gsoc", "hacktoberfest", "terminal", "c++", "java",
            "html", "css", "js", "react", "npm", "pip", "sudo", "chmod", "push",
            "pull", "commit", "merge", "rebase", "branch", "repo", "clone"
        ]
        has_tech = any(tw in clean for tw in tech_words)

        if not has_tech:
            words = clean.split()
            if words and words[0] in {"hi", "hello", "hey", "hola", "yo", "hai", "hlo", "welcome"} and len(words) <= 4:
                return True

        return False

    @staticmethod
    def get_greeting_analysis() -> Dict[str, Any]:
        """Returns clean, welcoming FOSS MBCCET onboarding response."""
        return {
            "category": "FOSS Community",
            "subcategory": "Welcome",
            "difficulty": "Beginner",
            "tags": ["foss", "community", "welcome"],
            "summary": "FOSS MBCCET Welcome",
            "direct_answer": (
                "👋 <b>Welcome to FOSS MBCCET!</b>\n\n"
                "I'm Tuxie, your open-source mentor. Ask me anything about:\n"
                "• 🌿 <b>Git & GitHub:</b> Branches, commits, merge conflicts\n"
                "• 🐧 <b>Linux & CLI:</b> Terminal commands, chmod, bash\n"
                "• 🐛 <b>Debugging:</b> Errors, stack traces, compiler issues\n"
                "• 🌟 <b>Open Source:</b> GSoC, Hacktoberfest, licensing\n\n"
                "Type your question or send a screenshot to get started!"
            ),
            "terminal_commands_or_code": (
                "# Quick starter commands\n"
                "git --version\n"
                "whoami\n"
                "uname -a"
            ),
            "recommended_foss_tools": ["Git", "Linux", "Bash"],
            "foss_tip": "Ask any doubt directly, or type /help for commands!"
        }

    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        """Safely parses JSON even when surrounded by reasoning tokens or thoughts."""
        text = text.strip()

        def _validate_and_normalize(parsed: Any) -> Optional[Dict[str, Any]]:
            if isinstance(parsed, dict) and ("category" in parsed or "direct_answer" in parsed):
                if "category" not in parsed:
                    parsed["category"] = "General FOSS & Community"
                if "subcategory" not in parsed:
                    parsed["subcategory"] = "General"
                if "difficulty" not in parsed:
                    parsed["difficulty"] = "Beginner"
                if "tags" not in parsed or not isinstance(parsed["tags"], list):
                    parsed["tags"] = ["foss", "mbccet"]
                if "direct_answer" not in parsed:
                    parsed["direct_answer"] = parsed.get("summary", "")
                return parsed
            return None

        # 1. Look for ```json ... ``` blocks
        matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        for m in reversed(matches):
            try:
                candidate = m.strip()
                parsed = json.loads(candidate)
                valid = _validate_and_normalize(parsed)
                if valid:
                    return valid
            except Exception:
                pass

        # 2. Look for outermost JSON brackets { ... }
        curly_matches = re.findall(r"(\{[\s\S]*\})", text)
        for c in reversed(curly_matches):
            try:
                parsed = json.loads(c)
                valid = _validate_and_normalize(parsed)
                if valid:
                    return valid
            except Exception:
                pass

        # 3. Direct parse
        try:
            parsed = json.loads(text)
            valid = _validate_and_normalize(parsed)
            if valid:
                return valid
        except Exception:
            pass

        raise ValueError(f"Could not parse valid JSON from output: {text[:250]}...")

    def _call_nvidia_nim_model(
        self,
        model: str,
        api_key: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 1200,
        temperature: float = 0.2,
        timeout: float = 3.0
    ) -> str:
        """Calls a specific model on NVIDIA NIM with streaming/polling support."""
        if not api_key:
            raise ValueError(f"API key missing for model {model}")

        invoke_url = f"{self.nvidia_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        with httpx.Client(timeout=timeout) as client:
            res = client.post(invoke_url, headers=headers, json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"NIM Error {res.status_code}: {res.text}")

            data = res.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("No choices in NIM response")

            msg = choices[0].get("message", {})
            # Some models put thoughts in reasoning_content and answer in content
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning_content") or ""

            # If content contains the JSON, use it; otherwise check reasoning
            if content and "{" in content:
                return content
            elif reasoning and "{" in reasoning:
                return reasoning
            return content or reasoning

    def _call_gemini_rest(self, contents: list, system_instruction: str = "") -> str:
        """Calls Google Gemini REST API."""
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=25) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini.")
            part = candidates[0].get("content", {}).get("parts", [{}])[0]
            return part.get("text", "")

    def _offline_fallback_analyzer(self, query: str, is_image: bool = False, caption: str = "") -> Dict[str, Any]:
        """Offline Pedagogical Heuristic Engine for FOSS MBCCET - Simple, precise structure."""
        if not is_image and self.is_greeting(query):
            return self.get_greeting_analysis()

        q = (query + " " + caption).lower()
        is_detail = any(w in q for w in ["more detail", "more info", "in detail", "explain more", "detailed", "step by step", "deep dive", "elaborate"])

        if any(w in q for w in ["git", "branch", "merge", "rebase", "commit", "push", "pull", "stash", "checkout", "conflict", "head", "origin"]):
            category = "Git & Version Control"
            subcategory = "Branching & Workflow"
            difficulty = "Beginner" if any(w in q for w in ["clone", "init", "add", "commit", "push"]) else "Intermediate"
            tags = ["git", "vcs", "github"]
            summary = "Git workflow inquiry"
            if is_detail:
                direct_answer = (
                    "Git is a distributed version control system for tracking changes.\n"
                    "• <b>Syncing:</b> Always run <code>git pull --rebase origin main</code> before branching to avoid divergent histories.\n"
                    "• <b>Branching:</b> Keep isolated feature branches for each task (<code>feature/task-name</code>).\n"
                    "• <b>Conflicts:</b> Look for conflict markers (<code>&lt;&lt;&lt;&lt;&lt;&lt;&lt;</code>, <code>=======</code>, <code>&gt;&gt;&gt;&gt;&gt;&gt;&gt;</code>), choose the correct code, stage with <code>git add</code>, and commit.\n"
                    "• <b>Commits:</b> Use conventional commit prefixes like <code>feat:</code>, <code>fix:</code>, <code>docs:</code>."
                )
            else:
                direct_answer = (
                    "To work with Git cleanly:\n"
                    "1. <b>Branch:</b> <code>git checkout -b feature/name</code>\n"
                    "2. <b>Commit:</b> <code>git add -A && git commit -m 'feat: description'</code>\n"
                    "3. <b>Sync:</b> <code>git pull --rebase origin main</code> before pushing.\n"
                    "For merge conflicts: open conflicting files, pick your resolution, stage with <code>git add</code>, and commit."
                )
            code = "git checkout -b feature/my-feature\ngit add -A\ngit commit -m 'feat: add feature'\ngit push -u origin feature/my-feature"
            tools = ["Git", "GitHub CLI", "LazyGit"]
            tip = "Run `git status` frequently to verify what is staged before committing!"

        elif any(w in q for w in ["linux", "ubuntu", "debian", "arch", "bash", "chmod", "chown", "sudo", "terminal", "shell", "kernel", "systemd", "pacman", "apt"]):
            category = "Linux & Shell"
            subcategory = "CLI & Permissions"
            difficulty = "Intermediate" if "systemd" in q or "kernel" in q else "Beginner"
            tags = ["linux", "bash", "cli"]
            summary = "Linux command inquiry"
            if is_detail:
                direct_answer = (
                    "Linux permission and service management breakdown:\n"
                    "• <b>Permissions:</b> Format <code>rwxrwxrwx</code> (User, Group, Others). <code>chmod 755 file</code> grants owner write, all others read+execute.\n"
                    "• <b>Redirection & Pipes:</b> Use <code>|</code> to pipe output to input, <code>&gt;</code> to overwrite, and <code>&gt;&gt;</code> to append.\n"
                    "• <b>Services:</b> Manage daemons with <code>systemctl start|stop|status &lt;service&gt;</code>."
                )
            else:
                direct_answer = (
                    "Essential Linux commands & permissions:\n"
                    "• <b>Permissions:</b> <code>chmod 755 script.sh</code> (makes executable)\n"
                    "• <b>Search files:</b> <code>grep -rnw './' -e 'keyword'</code>\n"
                    "• <b>Services:</b> <code>sudo systemctl status service_name</code>"
                )
            code = "sudo apt update && sudo apt upgrade -y\nchmod +x script.sh\n./script.sh"
            tools = ["GNU Coreutils", "Bash", "btop", "ripgrep"]
            tip = "Use `Ctrl + R` in terminal to search through your command history instantly!"

        elif any(w in q for w in ["license", "gpl", "mit", "apache", "bsd", "copyleft", "agpl", "proprietary", "copyright"]):
            category = "Open Source Licensing"
            subcategory = "License Choice"
            difficulty = "Beginner"
            tags = ["licenses", "copyleft", "gpl", "mit"]
            summary = "FOSS licensing distinction"
            direct_answer = (
                "Open source license quick guide:\n"
                "• <b>MIT / Apache 2.0:</b> Permissive (anyone can use and modify, even in proprietary code).\n"
                "• <b>GNU GPLv3:</b> Strong Copyleft (derivative works MUST also remain open source under GPL).\n"
                "• <b>AGPLv3:</b> Copyleft triggered over network/web services."
            )
            code = "# Check licenses in project\nnpx license-checker --summary"
            tools = ["ChooseALicense.com", "REUSE Tool", "SPDX"]
            tip = "Use MIT for maximum adoption; use GPLv3 to keep software free forever!"

        elif any(w in q for w in ["gsoc", "hacktoberfest", "outreachy", "first pr", "good first issue", "contribute", "open source program"]):
            category = "Open Source Programs"
            subcategory = "GSoC & Mentorship"
            difficulty = "Intermediate"
            tags = ["gsoc", "hacktoberfest", "contributions"]
            summary = "Open source program guidance"
            direct_answer = (
                "Getting started with GSoC / Hacktoberfest / Outreachy:\n"
                "1. Pick an organization early from past GSoC archives (e.g. Linux, Python, KDE).\n"
                "2. Search GitHub for issues labeled <code>good first issue</code>.\n"
                "3. Introduce yourself politely in community channels and send small, quality PRs."
            )
            code = "git clone <repo-url>\ncd <repo>\ngit remote add upstream <original-url>"
            tools = ["GoodFirstIssue.dev", "Up-For-Grabs.net", "GitHub Discussions"]
            tip = "Small, well-tested PRs build trust much faster than large unrequested rewrites!"

        elif any(w in q for w in ["docker", "container", "devops", "self-host", "kubernetes", "compose"]):
            category = "DevOps & Docker"
            subcategory = "Containers"
            difficulty = "Intermediate"
            tags = ["docker", "containers", "devops"]
            summary = "Docker containerization"
            direct_answer = (
                "Docker container essentials:\n"
                "• <b>Build image:</b> <code>docker build -t app-name .</code>\n"
                "• <b>Run container:</b> <code>docker run -d -p 8000:8000 app-name</code>\n"
                "• <b>View logs:</b> <code>docker logs -f container_id</code>"
            )
            code = "docker build -t foss-app .\ndocker run -d -p 8000:8000 --name myapp foss-app\ndocker ps"
            tools = ["Docker", "Podman", "Docker Compose"]
            tip = "Try Podman (`alias docker=podman`) as a rootless daemonless open-source alternative!"

        elif any(w in q for w in ["error", "bug", "exception", "failed", "segfault", "segmentation fault", "core dumped", "crash", "undefined", "syntaxerror", "traceback", "leak", "valgrind", "compiler"]):
            category = "Programming & Debugging"
            subcategory = "Error Diagnostics"
            difficulty = "Intermediate"
            tags = ["debugging", "troubleshooting", "bug-fix"]
            summary = "Code debugging inquiry"
            direct_answer = (
                "How to debug code errors quickly:\n"
                "1. Read the traceback from <b>bottom to top</b> to find the exact line and error type.\n"
                "2. Inspect variables using interactive debuggers (<code>pdb</code> for Python, <code>gdb</code> for C/C++).\n"
                "3. Isolate the failure into a minimal reproducible test case."
            )
            code = "# Run interactive python debugger\npython -m pdb your_script.py"
            tools = ["GDB", "Valgrind", "PDB", "ripgrep"]
            tip = "Rubber-duck debugging: explain the code out loud line-by-line to find logic flaws!"

        elif any(w in q for w in ["alternative", "photoshop", "office", "windows", "replace", "vs code", "notion"]):
            category = "FOSS Alternatives"
            subcategory = "Open Source Tools"
            difficulty = "Beginner"
            tags = ["foss-alternatives", "productivity"]
            summary = "FOSS software alternatives"
            direct_answer = (
                "Top FOSS alternatives to proprietary tools:\n"
                "• Photoshop -> <b>GIMP / Krita</b>\n"
                "• MS Office -> <b>LibreOffice / OnlyOffice</b>\n"
                "• Notion -> <b>Obsidian / Joplin</b>\n"
                "• VS Code -> <b>VSCodium</b> (telemetry-free)"
            )
            code = "sudo apt install gimp libreoffice vscodium"
            tools = ["LibreOffice", "GIMP", "Inkscape", "VSCodium"]
            tip = "Filter by 'Open Source' on AlternativeTo.net to find community alternatives!"

        else:
            category = "FOSS Community"
            subcategory = "Q&A"
            difficulty = "Beginner"
            tags = ["foss", "community", "open-source"]
            summary = f"Query: {query[:50]}"
            direct_answer = (
                f"Regarding your query on '{query}':\n\n"
                "FOSS MBCCET is here to help! Ask specific questions about Linux commands, "
                "Git workflows, compiler errors, or open-source licenses for an instant step-by-step fix."
            )
            code = "# Quick starter check\ngit --version\nwhoami"
            tools = ["Git", "Linux", "GitHub"]
            tip = "Include your OS and error message for the most precise solution!"

        return {
            "category": category,
            "subcategory": subcategory,
            "difficulty": difficulty,
            "tags": tags,
            "summary": summary,
            "direct_answer": direct_answer,
            "terminal_commands_or_code": code,
            "recommended_foss_tools": tools,
            "foss_tip": tip
        }

    def analyze_text_query(self, user_query: str) -> Dict[str, Any]:
        """
        Executes query through the multi-model cascade to get the best pedagogical response.
        Greetings and onboarding prompts are handled instantly.
        """
        if self.is_greeting(user_query):
            return self.get_greeting_analysis()

        prompt = get_text_query_prompt(user_query)
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_FOSS_MENTOR + "\n\nCRITICAL: You MUST respond ONLY with a single valid JSON object matching the requested schema. Do not write introductory chatter."
            },
            {"role": "user", "content": prompt}
        ]

        # 1. Iterate through NVIDIA NIM Text Models (Fast 3s timeout)
        for model_name, api_key in self.text_models:
            if not api_key:
                continue
            try:
                raw_text = self._call_nvidia_nim_model(
                    model=model_name,
                    api_key=api_key,
                    messages=messages,
                    timeout=3.0
                )
                if raw_text:
                    parsed = self._clean_json_response(raw_text)
                    return parsed
            except Exception:
                continue

        # 2. Try Google Gemini
        if self.gemini_api_key:
            try:
                contents = [{"role": "user", "parts": [{"text": prompt}]}]
                raw_text = self._call_gemini_rest(contents, system_instruction=SYSTEM_PROMPT_FOSS_MENTOR)
                if raw_text:
                    return self._clean_json_response(raw_text)
            except Exception:
                pass

        # 3. Fallback to Offline Heuristics
        return self._offline_fallback_analyzer(user_query)

    def analyze_image_query(self, image_path: str, caption: str = "") -> Dict[str, Any]:
        """
        Visual OCR & diagnostic pipeline for terminal/compiler screenshots:
        DiffusionGemma 26b -> Gemini Vision -> Offline Heuristic.
        """
        if not os.path.exists(image_path):
            return self._offline_fallback_analyzer("Code screenshot diagnostic", is_image=True, caption=caption)

        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()

            b64_image = base64.b64encode(img_bytes).decode("utf-8")
            ext = Path(image_path).suffix.lower()
            mime_type = "image/png" if ext == ".png" else "image/jpeg"
            data_uri = f"data:{mime_type};base64,{b64_image}"
            prompt = get_vision_query_prompt(caption)

            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_FOSS_MENTOR + "\n\nCRITICAL: Respond ONLY with a valid JSON object."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}}
                    ]
                }
            ]

            # 1. Try NVIDIA NIM Vision Models
            for model_name, api_key in self.vision_models:
                if not api_key:
                    continue
                try:
                    raw_text = self._call_nvidia_nim_model(
                        model=model_name,
                        api_key=api_key,
                        messages=messages,
                        timeout=8.0
                    )
                    if raw_text:
                        return self._clean_json_response(raw_text)
                except Exception:
                    continue

            # 2. Try Gemini Vision
            if self.gemini_api_key:
                try:
                    contents = [
                        {
                            "role": "user",
                            "parts": [
                                {"text": prompt},
                                {
                                    "inlineData": {
                                        "mimeType": mime_type,
                                        "data": b64_image
                                    }
                                }
                            ]
                        }
                    ]
                    raw_text = self._call_gemini_rest(contents, system_instruction=SYSTEM_PROMPT_FOSS_MENTOR)
                    if raw_text:
                        return self._clean_json_response(raw_text)
                except Exception:
                    pass

        except Exception:
            pass

        # 3. Fallback
        return self._offline_fallback_analyzer(
            query="Code/Terminal Screenshot Diagnostic",
            is_image=True,
            caption=caption
        )

    def classify_query(self, user_query: str) -> Dict[str, Any]:
        """Classifies an inquiry into structured community taxonomies."""
        analysis = self.analyze_text_query(user_query)
        return {
            "category": analysis.get("category", "General FOSS & Community"),
            "subcategory": analysis.get("subcategory", "General"),
            "difficulty": analysis.get("difficulty", "Beginner"),
            "tags": analysis.get("tags", []),
            "summary": analysis.get("summary", ""),
            "foss_tools": analysis.get("recommended_foss_tools", [])
        }
