/**
 * Main Web Portal Orchestrator
 */

document.addEventListener("DOMContentLoaded", async () => {
  // Initialize UI navigation
  window.TabManager.init();

  const inputBox = document.getElementById("playground-input");
  const diffDisplay = document.getElementById("diff-display");
  const teachList = document.getElementById("teach-list");
  const metricWords = document.getElementById("metric-words");
  const metricEase = document.getElementById("metric-ease");
  const metricGrade = document.getElementById("metric-grade");
  const metricTime = document.getElementById("metric-time");
  const daemonDot = document.getElementById("daemon-status-dot");
  const daemonLabel = document.getElementById("daemon-status-text");

  let currentTone = "standard";

  // Check daemon/server connection
  const status = await window.ApiClient.checkStatus();
  if (status.status === "online") {
    daemonDot.classList.remove("offline");
    daemonLabel.innerText = status.daemon_active ? "Daemon Active (RAM)" : "Web Server Online";
  } else {
    daemonDot.classList.add("offline");
    daemonLabel.innerText = "Offline Browser Mode";
  }

  // Refinement update function
  async function updateRefinement() {
    const text = inputBox.value;
    if (!text.trim()) {
      diffDisplay.innerHTML = `<span style="color: var(--text-muted); font-style: italic;">Refined visual diff will appear here...</span>`;
      teachList.innerHTML = `<li><em>No edits made yet.</em></li>`;
      metricWords.innerText = "0";
      metricEase.innerText = "100";
      metricGrade.innerText = "0";
      metricTime.innerText = "0s";
      return;
    }

    const res = await window.ApiClient.refineText(text, currentTone);
    const refined = res.refined || text;
    const explanations = res.explanations || [];

    // Render word diff
    const diffHtml = window.DiffHighlighter.computeWordDiff(text, refined);
    diffDisplay.innerHTML = diffHtml || refined;

    // Render Teach mode
    if (explanations.length > 0) {
      teachList.innerHTML = explanations.map(e => `<li>💡 ${window.DiffHighlighter.escape(e)}</li>`).join("");
    } else {
      teachList.innerHTML = `<li>✨ <em>No grammar or stylistic alterations required. Sentence is clean.</em></li>`;
    }

    // Render Metrics
    const m = window.MetricsCalculator.analyze(refined);
    metricWords.innerText = m.words;
    metricEase.innerText = m.readingEase;
    metricGrade.innerText = m.gradeLevel;
    metricTime.innerText = `${m.readingTimeSec}s`;
  }

  // Input event listener (debounced)
  let debounceTimer;
  inputBox.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(updateRefinement, 120);
  });

  // Tone selector buttons
  const toneBtns = document.querySelectorAll(".tone-btn");
  toneBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      toneBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentTone = btn.getAttribute("data-tone");
      updateRefinement();
    });
  });

  // Sample chips
  const sampleChips = document.querySelectorAll(".chip-btn");
  sampleChips.forEach(chip => {
    chip.addEventListener("click", () => {
      inputBox.value = chip.getAttribute("data-sample");
      updateRefinement();
    });
  });

  // Initial trigger
  updateRefinement();
});
