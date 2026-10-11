document.addEventListener("DOMContentLoaded", () => {
    // State
    let currentMode = "ask"; // 'ask' or 'classify'
    const cachedResources = {};

    // DOM Elements
    const statStudents = document.getElementById("stat-students");
    const statDoubts = document.getElementById("stat-doubts");
    const statPhotos = document.getElementById("stat-photos");
    const statTopTopic = document.getElementById("stat-top-topic");
    const categoryBarsContainer = document.getElementById("category-bars-container");
    const recentQueriesContainer = document.getElementById("recent-queries-container");
    const daemonStatus = document.getElementById("daemon-status");

    const btnModeAsk = document.getElementById("btn-mode-ask");
    const btnModeClassify = document.getElementById("btn-mode-classify");
    const queryInput = document.getElementById("query-input");
    const btnSubmit = document.getElementById("btn-submit");
    const submitText = document.getElementById("submit-text");
    const submitSpinner = document.getElementById("submit-spinner");

    const resultBox = document.getElementById("result-box");
    const resCategory = document.getElementById("res-category");
    const resSubcategory = document.getElementById("res-subcategory");
    const resDifficulty = document.getElementById("res-difficulty");
    const resSummary = document.getElementById("res-summary");
    const resExplanation = document.getElementById("res-explanation");
    const resCode = document.getElementById("res-code");
    const resTools = document.getElementById("res-tools");
    const resTip = document.getElementById("res-tip");
    const resTags = document.getElementById("res-tags");
    const btnCopyCode = document.getElementById("btn-copy-code");

    const quickrefCode = document.getElementById("quickref-code");
    const tabBtns = document.querySelectorAll(".tab-btn");
    const promptChips = document.querySelectorAll(".chip");

    // Mode Toggle
    btnModeAsk.addEventListener("click", () => {
        currentMode = "ask";
        btnModeAsk.classList.add("active");
        btnModeClassify.classList.remove("active");
        submitText.textContent = "Resolve Doubt";
        queryInput.placeholder = "Type your coding doubt, Linux error, Git issue, or open-source licensing question...";
    });

    btnModeClassify.addEventListener("click", () => {
        currentMode = "classify";
        btnModeClassify.classList.add("active");
        btnModeAsk.classList.remove("active");
        submitText.textContent = "Classify Topic";
        queryInput.placeholder = "Enter any topic or question to classify its FOSS taxonomy & difficulty...";
    });

    // Preset Chips
    promptChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const query = chip.getAttribute("data-query");
            queryInput.value = query;
            submitQuery();
        });
    });

    // Keyboard Shortcut (Ctrl+Enter)
    queryInput.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            submitQuery();
        }
    });

    // Submit Button
    btnSubmit.addEventListener("click", submitQuery);

    async function submitQuery() {
        const query = queryInput.value.trim();
        if (!query) return;

        // UI Loading State
        btnSubmit.disabled = true;
        submitSpinner.classList.remove("hidden");
        submitText.textContent = currentMode === "ask" ? "Thinking..." : "Classifying...";

        try {
            const endpoint = currentMode === "ask" ? "/api/ask" : "/api/classify";
            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });

            if (!res.ok) throw new Error("API request failed with status " + res.status);

            const data = await res.json();
            const analysis = currentMode === "ask" ? data.analysis : data;

            // Render Output
            renderAnalysis(analysis);
            
            // Refresh stats & stream if in ask mode
            if (currentMode === "ask") {
                fetchStats();
                fetchRecentQueries();
            }
        } catch (err) {
            console.error("Submission error:", err);
            alert("Error: " + err.message);
        } finally {
            btnSubmit.disabled = false;
            submitSpinner.classList.add("hidden");
            submitText.textContent = currentMode === "ask" ? "Resolve Doubt" : "Classify Topic";
        }
    }

    function renderAnalysis(analysis) {
        resultBox.classList.remove("hidden");
        resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });

        resCategory.textContent = analysis.category || "General FOSS";
        resSubcategory.textContent = analysis.subcategory || "General";
        resDifficulty.textContent = analysis.difficulty || "Beginner";
        resSummary.textContent = analysis.summary || "Inquiry Analysis";

        if (currentMode === "ask") {
            resExplanation.textContent = analysis.direct_answer || "";
            resCode.textContent = analysis.terminal_commands_or_code || "# No commands needed for this topic";
            resTools.textContent = (analysis.recommended_foss_tools || []).join(", ") || "Git, Linux";
            resTip.textContent = analysis.foss_tip || "Embrace open standards and read the docs!";
        } else {
            resExplanation.textContent = "Query successfully classified into FOSS community taxonomy.";
            resCode.textContent = `# Taxonomy Output:\nCategory: ${analysis.category}\nSubcategory: ${analysis.subcategory}\nLevel: ${analysis.difficulty}`;
            resTools.textContent = (analysis.foss_tools || []).join(", ") || "FOSS Tools";
            resTip.textContent = "Use classification to route tickets or explore targeted roadmaps.";
        }

        // Tags
        const tags = analysis.tags || [];
        resTags.innerHTML = tags.map(t => `<span class="tag-pill">#${t}</span>`).join("");
    }

    // Copy Code Button
    btnCopyCode.addEventListener("click", () => {
        const text = resCode.textContent;
        navigator.clipboard.writeText(text).then(() => {
            btnCopyCode.textContent = "Copied!";
            setTimeout(() => { btnCopyCode.textContent = "Copy Code"; }, 2000);
        });
    });

    // Fetch Stats
    async function fetchStats() {
        try {
            const res = await fetch("/api/stats");
            if (!res.ok) return;
            const data = await res.json();

            statStudents.textContent = data.total_students || 0;
            statDoubts.textContent = data.total_doubts_resolved || 0;
            statPhotos.textContent = data.code_screenshots_analyzed || 0;

            if (data.categories && data.categories.length > 0) {
                statTopTopic.textContent = data.categories[0].category.split("&")[0].trim();
                renderCategoryBars(data.categories, data.total_doubts_resolved || 1);
            } else {
                categoryBarsContainer.innerHTML = "<div class='loading-placeholder'>No queries recorded yet. Be the first to ask!</div>";
            }
        } catch (err) {
            console.error("Failed to fetch stats:", err);
        }
    }

    function renderCategoryBars(categories, total) {
        categoryBarsContainer.innerHTML = "";
        categories.slice(0, 5).forEach(cat => {
            const percentage = Math.min(100, Math.round((cat.count / Math.max(total, 1)) * 100));
            const row = document.createElement("div");
            row.className = "bar-row";
            row.innerHTML = `
                <div class="bar-labels">
                    <span>${cat.category}</span>
                    <span>${cat.count} (${percentage}%)</span>
                </div>
                <div class="bar-track">
                    <div class="bar-fill" style="width: ${percentage}%"></div>
                </div>
            `;
            categoryBarsContainer.appendChild(row);
        });
    }

    // Fetch Recent Queries
    async function fetchRecentQueries() {
        try {
            const res = await fetch("/api/queries?limit=8");
            if (!res.ok) return;
            const data = await res.json();
            const queries = data.queries || [];

            recentQueriesContainer.innerHTML = "";
            if (queries.length === 0) {
                recentQueriesContainer.innerHTML = "<div class='loading-placeholder'>No community doubts yet.</div>";
                return;
            }

            queries.forEach(q => {
                const item = document.createElement("div");
                item.className = "stream-item";
                const typeIcon = q.query_type === "photo" ? "📸" : "💬";
                item.innerHTML = `
                    <div class="stream-item-top">
                        <span>${typeIcon} ${q.category}</span>
                        <span>${q.difficulty}</span>
                    </div>
                    <div class="stream-item-text">${escapeHtml(q.query_text.substring(0, 80))}${q.query_text.length > 80 ? '...' : ''}</div>
                `;
                item.addEventListener("click", () => {
                    queryInput.value = q.query_text;
                    submitQuery();
                });
                recentQueriesContainer.appendChild(item);
            });
        } catch (err) {
            console.error("Failed to fetch queries:", err);
        }
    }

    // Quickref Tabs
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const topic = btn.getAttribute("data-topic");
            loadQuickref(topic);
        });
    });

    async function loadQuickref(topic) {
        if (cachedResources[topic]) {
            quickrefCode.textContent = cachedResources[topic];
            return;
        }

        try {
            quickrefCode.textContent = "Loading cheat sheet...";
            const res = await fetch(`/api/resources/${topic}`);
            if (!res.ok) throw new Error("Not found");
            const data = await res.json();
            cachedResources[topic] = data.content;
            quickrefCode.textContent = data.content;
        } catch (err) {
            quickrefCode.textContent = "Error loading resource.";
        }
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // Initial Load
    fetchStats();
    fetchRecentQueries();
    loadQuickref("git");
});
