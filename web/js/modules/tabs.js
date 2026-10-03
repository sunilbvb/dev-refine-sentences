/**
 * Tabs and Interactive UI Navigation Module
 */

window.TabManager = {
  init: function() {
    // Tab switching
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetTab = btn.getAttribute("data-tab");

        tabBtns.forEach(b => b.classList.remove("active"));
        tabContents.forEach(c => c.classList.remove("active"));

        btn.classList.add("active");
        const activeContent = document.getElementById(`tab-${targetTab}`);
        if (activeContent) {
          activeContent.classList.add("active");
        }
      });
    });

    // Copy buttons on code blocks
    document.querySelectorAll("pre").forEach(pre => {
      const code = pre.querySelector("code");
      if (!code) return;

      const btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.innerText = "Copy";
      btn.addEventListener("click", () => {
        navigator.clipboard.writeText(code.innerText.trim()).then(() => {
          btn.innerText = "Copied!";
          setTimeout(() => (btn.innerText = "Copy"), 2000);
        });
      });
      pre.appendChild(btn);
    });
  }
};
