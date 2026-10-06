/**
 * Main Web Portal Orchestrator
 */

document.addEventListener("DOMContentLoaded", async () => {
  // Initialize UI navigation
  window.TabManager.init();
  if (window.SettingsPanel) window.SettingsPanel.init();

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
  const serverBanner = document.getElementById("server-control-banner");

  function renderServerBanner(status) {
    if (!serverBanner) return;

    if (status.status === "online") {
      serverBanner.className = "server-banner online";
      serverBanner.innerHTML = `
        <div class="server-banner-left">
          <span class="server-status-icon">🟢</span>
          <div>
            <div class="server-banner-title">Documentation & Refiner Web Server Online</div>
            <div class="server-banner-desc">Port: ${status.port || 8080} &bull; PID: ${status.pid || 'Active'} &bull; Resident Daemon: ${status.daemon_active ? 'Active in RAM (Sub-2ms)' : 'Offline'}</div>
          </div>
        </div>
        <div class="server-banner-right">
          <button class="btn-server stop" id="btn-stop-server">⏹ Stop Server</button>
        </div>
      `;

      document.getElementById("btn-stop-server")?.addEventListener("click", async () => {
        await window.ApiClient.stopServer();
        renderServerBanner({ status: "offline" });
        daemonDot.classList.add("offline");
        daemonLabel.innerText = "Offline Browser Mode";
      });
    } else {
      serverBanner.className = "server-banner offline";
      serverBanner.innerHTML = `
        <div class="server-banner-left">
          <span class="server-status-icon">🔴</span>
          <div>
            <div class="server-banner-title">Local Web Server is Offline (Static Browser Mode)</div>
            <div class="server-banner-desc">
              Web browser security sandboxing prevents static pages from directly spawning OS bash commands. Use <code>./launch_portal.sh</code> or copy the start command below:
            </div>
          </div>
        </div>
        <div class="server-banner-right">
          <button class="btn-server primary" id="btn-copy-cmd">📋 Copy: python3 main.py --serve</button>
          <button class="btn-server" id="btn-check-server">🔄 Check Status</button>
        </div>
      `;

      document.getElementById("btn-copy-cmd")?.addEventListener("click", (e) => {
        navigator.clipboard.writeText("python3 main.py --serve 8080");
        const btn = e.target;
        btn.innerText = "Copied to Clipboard!";
        setTimeout(() => { btn.innerText = "📋 Copy: python3 main.py --serve"; }, 2000);
      });

      document.getElementById("btn-check-server")?.addEventListener("click", async (e) => {
        const btn = e.target;
        btn.innerText = "Checking...";
        const newStatus = await window.ApiClient.checkStatus();
        renderServerBanner(newStatus);
        if (newStatus.status === "online") {
          daemonDot.classList.remove("offline");
          daemonLabel.innerText = newStatus.daemon_active ? "Daemon Active (RAM)" : "Web Server Online";
        }
      });
    }
  }

  // Check daemon/server connection
  const status = await window.ApiClient.checkStatus();
  renderServerBanner(status);

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
