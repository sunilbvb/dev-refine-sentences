/**
 * API Client Module
 * Connects to Python Web Server or falls back to BrowserRefiner.
 */

window.ApiClient = {
  isServerConnected: false,
  serverInfo: null,

  getBaseUrl: function() {
    if (window.location.protocol === "file:") {
      return "http://localhost:8080";
    }
    return "";
  },

  checkStatus: async function() {
    const base = this.getBaseUrl();
    try {
      const resp = await fetch(`${base}/api/server/status`, { signal: AbortSignal.timeout(1000) });
      if (resp.ok) {
        const data = await resp.json();
        this.isServerConnected = true;
        this.serverInfo = data;
        return data;
      }
    } catch (e) {
      this.isServerConnected = false;
      this.serverInfo = null;
    }
    return { status: "offline", daemon_active: false, mode: "browser_local" };
  },

  refineText: async function(text, tone = "standard") {
    if (this.isServerConnected) {
      const base = this.getBaseUrl();
      try {
        const resp = await fetch(`${base}/api/refine`, {
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
  },

  stopServer: async function() {
    if (!this.isServerConnected) return false;
    const base = this.getBaseUrl();
    try {
      const resp = await fetch(`${base}/api/server/stop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      this.isServerConnected = false;
      return resp.ok;
    } catch (e) {
      this.isServerConnected = false;
      return true;
    }
  }
};

