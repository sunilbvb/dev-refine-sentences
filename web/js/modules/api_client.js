/**
 * API Client Module
 * Connects to Python Web Server or falls back to BrowserRefiner.
 */

window.ApiClient = {
  isServerConnected: false,

  checkStatus: async function() {
    try {
      const resp = await fetch("/api/status", { signal: AbortSignal.timeout(1000) });
      if (resp.ok) {
        const data = await resp.json();
        this.isServerConnected = true;
        return data;
      }
    } catch (e) {
      this.isServerConnected = false;
    }
    return { status: "offline", daemon_active: false, mode: "browser_local" };
  },

  refineText: async function(text, tone = "standard") {
    if (this.isServerConnected) {
      try {
        const resp = await fetch("/api/refine", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text, tone: tone }),
          signal: AbortSignal.timeout(2000)
        });
        if (resp.ok) {
          return await resp.json();
        }
      } catch (e) {
        console.warn("Server call failed, falling back to local browser engine:", e);
      }
    }

    // Client-side fallback
    return window.BrowserRefiner.refine(text, tone);
  }
};
