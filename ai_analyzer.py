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
            (NVIDIA_KIMI_MODEL, NVIDIA_KIMI_KEY)
        ]

        # Text Reasoning Models Pool (Ordered by priority)
        self.text_models: List[Tuple[str, str]] = [
            (NVIDIA_MUSE_MODEL, NVIDIA_MUSE_KEY),
            (NVIDIA_NEMOTRON_MODEL, NVIDIA_NEMOTRON_KEY),
            (NVIDIA_LAGUNA_MODEL, NVIDIA_LAGUNA_KEY),
            (NVIDIA_KIMI_MODEL, NVIDIA_KIMI_KEY)
        ]

    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        """Safely parses JSON even when surrounded by reasoning tokens or thoughts."""
        text = text.strip()

        # 1. Look for ```json ... ``` blocks
        matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        for m in reversed(matches):
            try:
                candidate = m.strip()
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and "category" in parsed:
                    return parsed
            except Exception:
                pass

        # 2. Look for outermost JSON brackets { ... }
        curly_matches = re.findall(r"(\{[\s\S]*\})", text)
        for c in reversed(curly_matches):
            try:
                parsed = json.loads(c)
                if isinstance(parsed, dict) and "category" in parsed:
                    return parsed
            except Exception:
                pass

        # 3. Direct parse
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "category" in parsed:
                return parsed
        except Exception:
            pass

        raise ValueError(f"Could not parse valid JSON from output: {text[:250]}...")

    def _call_nvidia_nim_model(
        self,
        model: str,
        api_key: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 2500,
        temperature: float = 0.2,
        timeout: float = 25.0
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
        """Offline Pedagogical Heuristic Engine for FOSS MBCCET."""
        q = (query + " " + caption).lower()

        if any(w in q for w in ["git", "branch", "merge", "rebase", "commit", "push", "pull", "stash", "checkout", "conflict", "head", "origin"]):
            category = "Git & Version Control"
            subcategory = "Branching & Collaboration"
            difficulty = "Beginner" if any(w in q for w in ["clone", "init", "add", "commit", "push"]) else "Intermediate"
            tags = ["git", "version-control", "github", "vcs"]
            summary = "Git workflow, version control, or conflict resolution inquiry"
            direct_answer = (
                "Git is the distributed version control system created by Linus Torvalds in 2005. "
                "For handling branches and collaboration:\n"
                "1. Always keep your local `main` branch synced with `git pull --rebase origin main`.\n"
                "2. Create dedicated feature branches (`feature/your-topic`) before editing code.\n"
                "3. In case of merge conflicts, open the files, locate conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`), choose the resolution, stage with `git add`, and continue the rebase/merge.\n"
                "4. Write clear commit messages following Conventional Commits format (`feat:`, `fix:`, `docs:`)."
            )
            code = "git checkout -b feature/awesome-feature\ngit add -A\ngit commit -m 'feat: add open source module'\ngit push -u origin feature/awesome-feature"
            tools = ["Git", "GitHub CLI (gh)", "LazyGit", "GitKraken / Ungit"]
            tip = "Use `git status` frequently and `git log --oneline --graph --decorate` to visualize branch topologies!"

        elif any(w in q for w in ["linux", "ubuntu", "debian", "arch", "bash", "chmod", "chown", "sudo", "terminal", "shell", "kernel", "systemd", "pacman", "apt"]):
            category = "Linux & Shell Scripting"
            subcategory = "System Administration & CLI"
            difficulty = "Intermediate" if "systemd" in q or "kernel" in q else "Beginner"
            tags = ["linux", "bash", "sysadmin", "cli", "posix"]
            summary = "Linux terminal navigation, file permissions, or package management doubt"
            direct_answer = (
                "GNU/Linux provides robust multi-user permission models and modular command-line utilities:\n"
                "1. **Permissions**: Format is `rwxrwxrwx` (User, Group, Others). `chmod 755 script.sh` gives owner write permissions and all others read+execute.\n"
                "2. **Pipes & Streams**: Combine UNIX tools with pipes (`|`), standard output redirection (`>`), and append (`>>`).\n"
                "3. **Services**: Manage system daemons cleanly with `systemctl start|stop|status <service>`."
            )
            code = "# Update packages & check service status\nsudo apt update && sudo apt upgrade -y\nsudo systemctl status ssh\n# Find text inside files recursively\ngrep -rnw './' -e 'FOSS'"
            tools = ["GNU Coreutils", "bash / zsh / fish", "btop", "ripgrep", "tmux"]
            tip = "Remember the UNIX philosophy: Write programs that do one thing and do it well, and work together through plain text streams."

        elif any(w in q for w in ["license", "gpl", "mit", "apache", "bsd", "copyleft", "agpl", "proprietary", "copyright"]):
            category = "Open Source Licensing & Ethics"
            subcategory = "License Selection & Copyleft"
            difficulty = "Beginner"
            tags = ["licenses", "copyleft", "open-source", "ethics", "gpl"]
            summary = "FOSS licensing distinction and ethical software distribution"
            direct_answer = (
                "Open Source licenses define how others can use, modify, and distribute your code:\n"
                "1. **Permissive Licenses** (MIT, Apache 2.0, BSD): Grants users maximum freedom to reuse code in any project, including proprietary software, with minimal attribution requirements.\n"
                "2. **Strong Copyleft** (GNU GPLv3, AGPLv3): Ensures the software and any modified derivative works remain free and open source forever. If someone distributes modifications, they MUST release their source under the GPL.\n"
                "3. **Patent Grants**: Apache 2.0 explicitly grants patent rights, which is great for commercial open source libraries."
            )
            code = "# Check existing licenses in your project\nnpx license-checker --summary"
            tools = ["ChooseALicense.com", "REUSE Software Tool", "FOSSA", "SPDX License List"]
            tip = "If you want anyone to use your library without friction, choose MIT or Apache 2.0. If you want to protect software freedom and prevent closed-source forks, choose GNU GPLv3!"

        elif any(w in q for w in ["gsoc", "hacktoberfest", "outreachy", "first pr", "good first issue", "contribute", "open source program"]):
            category = "Open Source Programs & GSoC"
            subcategory = "Student Contribution Pathways"
            difficulty = "Intermediate"
            tags = ["gsoc", "hacktoberfest", "mentorship", "contributions", "students"]
            summary = "Guidance on participating in open source mentorship programs"
            direct_answer = (
                "Getting started with major open source programs like GSoC, Hacktoberfest, and Outreachy:\n"
                "1. **Find Projects Early**: Explore past participating organizations on the GSoC archives (e.g., Linux Foundation, Python Software Foundation, VideoLAN, KDE, Apache).\n"
                "2. **Good First Issues**: Search GitHub with `is:issue is:open label:\"good first issue\"` or `label:\"help wanted\"`.\n"
                "3. **Engage with Community**: Join their Zulip, Matrix, Discord, or IRC channel. Introduce yourself politely and start by testing documentation or reproducing bugs.\n"
                "4. **Write Quality PRs**: Link the issue (`Fixes #123`), explain your solution, and verify unit tests pass before asking for review."
            )
            code = "# Clone the target repo and create your fork branch\ngit clone https://github.com/fossmbccet/project.git\ncd project\ngit remote add upstream https://github.com/original-org/project.git"
            tools = ["GoodFirstIssue.dev", "Up-For-Grabs.net", "GitHub Discussions", "Matrix / IRC"]
            tip = "Open source maintainers value consistency and clear communication over huge, unrequested PRs. Start small and build trust!"

        elif any(w in q for w in ["docker", "container", "devops", "self-host", "kubernetes", "compose"]):
            category = "DevOps, Docker & Self-Hosting"
            subcategory = "Containerization & Deployment"
            difficulty = "Intermediate"
            tags = ["docker", "containers", "self-hosting", "devops"]
            summary = "Docker containerization and reproducible FOSS deployment"
            direct_answer = (
                "Docker packages applications into standardized units with all dependencies:\n"
                "1. Write a minimal multi-stage `Dockerfile` to keep production image sizes tiny.\n"
                "2. Use `docker-compose.yml` for multi-container stacks (e.g., app + database).\n"
                "3. Isolate persistent state with Docker named volumes."
            )
            code = "docker build -t fossmbccet-bot .\ndocker run -d -p 8000:8000 --name fossbot fossmbccet-bot\ndocker logs -f fossbot"
            tools = ["Docker", "Podman (Rootless FOSS alternative)", "Docker Compose", "Portainer"]
            tip = "Check out Podman as a daemonless, rootless drop-in FOSS alternative to Docker (`alias docker=podman`)!"

        elif any(w in q for w in ["error", "bug", "exception", "failed", "segfault", "segmentation fault", "core dumped", "crash", "undefined", "syntaxerror", "traceback", "leak", "valgrind", "compiler"]):
            category = "Programming & Bug Debugging"
            subcategory = "Error Diagnosis & Debugging"
            difficulty = "Intermediate"
            tags = ["debugging", "troubleshooting", "compiler-error", "bug-fix"]
            summary = "Code debugging, stack trace analysis, and resolution"
            direct_answer = (
                "Debugging systematically saves hours of guesswork:\n"
                "1. **Read the traceback from bottom to top**: The bottom line indicates the exact exception and file/line number.\n"
                "2. **Inspect variable state**: Use interactive debuggers (`pdb` in Python, `gdb` in C/C++, `debugger` in JS) rather than random print statements.\n"
                "3. **Reproduce with minimal test case**: Strip extraneous code until only the failing logic remains."
            )
            code = "# Run interactive python debugger on unhandled exception\npython -m pdb your_script.py"
            tools = ["GDB", "Valgrind", "PDB", "Sentry (Self-hosted)", "Ghidra"]
            tip = "Rubber duck debugging actually works! Explaining the problem line-by-line forces your brain to re-examine hidden assumptions."

        elif any(w in q for w in ["alternative", "photoshop", "office", "windows", "replace", "vs code", "notion"]):
            category = "FOSS Alternatives & Tools"
            subcategory = "Open Source Replacements"
            difficulty = "Beginner"
            tags = ["foss-alternatives", "free-software", "productivity", "privacy"]
            summary = "FOSS alternatives to proprietary commercial software"
            direct_answer = (
                "High quality FOSS alternatives to popular proprietary tools:\n"
                "• **Photoshop / Illustrator** -> GIMP / Inkscape / Krita\n"
                "• **Microsoft Office** -> LibreOffice / OnlyOffice\n"
                "• **Notion / Evernote** -> Obsidian / Joplin / Logseq\n"
                "• **Premiere Pro** -> Kdenlive / DaVinci Resolve / Shotcut\n"
                "• **Postman** -> Bruno / Hoppscotch / Insomnia\n"
                "• **VS Code Builds** -> VSCodium (100% open telemetry-free)"
            )
            code = "# Install open-source alternatives via package manager\nsudo apt install gimp inkscape libreoffice vscodium"
            tools = ["LibreOffice", "GIMP", "Inkscape", "Kdenlive", "VSCodium", "Hoppscotch"]
            tip = "Check out AlternativeTo.net with the 'Open Source' filter checked whenever you need a tool!"

        else:
            category = "General FOSS & Community"
            subcategory = "FOSS Philosophy & Best Practices"
            difficulty = "Beginner"
            tags = ["foss", "community", "freedom", "open-source"]
            summary = f"FOSS community query: {query[:60]}"
            direct_answer = (
                f"Welcome to FOSS MBCCET! Regarding your query on '{query}':\n\n"
                "Free and Open Source Software (FOSS) stands on the four essential software freedoms defined by the Free Software Foundation:\n"
                "• Freedom 0: Run the program for any purpose.\n"
                "• Freedom 1: Study how the program works and modify it.\n"
                "• Freedom 2: Redistribute copies to help your neighbor.\n"
                "• Freedom 3: Distribute modified copies to benefit the community.\n\n"
                "Feel free to ask specific technical questions about Linux commands, Git workflows, compiler errors, or open-source licenses!"
            )
            code = "# Join the FOSS MBCCET community\ngit clone https://github.com/fossmbccet/welcome.git"
            tools = ["GitHub", "GitLab", "Linux Foundation", "FSF"]
            tip = "The best way to learn software engineering is by reading real, high-quality open source code on GitHub/GitLab!"

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
        Executes query through the multi-model cascade to get the best pedagogical response:
        Meta Muse -> NVIDIA Nemotron -> Poolside Laguna -> Moonshot Kimi -> Gemini -> Offline Heuristic.
        """
        prompt = get_text_query_prompt(user_query)
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT_FOSS_MENTOR + "\n\nCRITICAL: You MUST respond ONLY with a single valid JSON object matching the requested schema. Do not write introductory chatter."
            },
            {"role": "user", "content": prompt}
        ]

        # 1. Iterate through NVIDIA NIM Text Models
        for model_name, api_key in self.text_models:
            if not api_key:
                continue
            try:
                raw_text = self._call_nvidia_nim_model(
                    model=model_name,
                    api_key=api_key,
                    messages=messages,
                    timeout=20.0
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
        DiffusionGemma 26b -> Moonshot Kimi-k3 -> Gemini Vision -> Offline Heuristic.
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

            # 1. Try NVIDIA NIM Vision Models (DiffusionGemma 26b & Kimi-k3)
            for model_name, api_key in self.vision_models:
                if not api_key:
                    continue
                try:
                    raw_text = self._call_nvidia_nim_model(
                        model=model_name,
                        api_key=api_key,
                        messages=messages,
                        timeout=30.0
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
