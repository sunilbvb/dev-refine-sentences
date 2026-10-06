/**
 * Settings Module - view and edit tone, engine, local model and hotkey via /api/config.
 * Values from the server are written with textContent/value only (never innerHTML).
 */

window.SettingsPanel = {
  init: async function() {
    const root = document.getElementById("settings-panel");
    if (!root) return;
    const base = window.ApiClient.getBaseUrl();
    const els = {
      tone: document.getElementById("set-tone"),
      engine: document.getElementById("set-engine"),
      model: document.getElementById("set-model"),
      hotkey: document.getElementById("set-hotkey"),
      save: document.getElementById("btn-save-settings"),
      status: document.getElementById("settings-status"),
      modelHint: document.getElementById("set-model-hint"),
      keys: document.getElementById("set-keys"),
    };

    const say = (msg, ok) => {
      els.status.textContent = msg;
      els.status.className = "settings-status " + (ok ? "ok" : "err");
    };
    const fill = (select, values, current) => {
      select.replaceChildren(...values.map(v => {
        const o = document.createElement("option");
        o.value = v; o.textContent = v; o.selected = v === current;
        return o;
      }));
    };

    let cfg;
    try {
      cfg = await (await fetch(`${base}/api/config`)).json();
    } catch (e) {
      say("Start the web server (scripts/start.sh) to edit settings.", false);
      els.save.disabled = true;
      return;
    }
    fill(els.tone, cfg.options.tones, cfg.preferred_tone);
    fill(els.engine, cfg.options.engines, cfg.preferred_engine);
    els.hotkey.value = cfg.hotkey;
    els.keys.textContent = Object.entries(cfg.api_keys_configured)
      .map(([k, v]) => `${k}: ${v ? "configured" : "not set"}`).join("  |  ");

    // Model dropdown from the models actually installed in Ollama
    const models = await (await fetch(`${base}/api/ollama/models`)).json();
    if (models.available && models.models.length) {
      const names = models.models.map(m => m.name);
      if (!names.includes(cfg.ollama_model)) names.unshift(cfg.ollama_model);
      els.model.replaceChildren(...names.map(n => {
        const o = document.createElement("option");
        const info = models.models.find(m => m.name === n);
        o.value = n; o.textContent = info ? `${n} (${info.size_gb} GB)` : `${n} (not installed)`;
        o.selected = n === cfg.ollama_model;
        return o;
      }));
      els.modelHint.textContent = "Smaller models (1-3 GB) are much faster on 16 GB Macs.";
    } else {
      const o = document.createElement("option");
      o.value = cfg.ollama_model; o.textContent = cfg.ollama_model;
      els.model.replaceChildren(o);
      els.modelHint.textContent = "Ollama is not running (brew services start ollama).";
    }

    els.save.addEventListener("click", async () => {
      try {
        const resp = await fetch(`${base}/api/config`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            preferred_tone: els.tone.value,
            preferred_engine: els.engine.value,
            ollama_model: els.model.value,
            hotkey: els.hotkey.value,
          }),
        });
        const data = await resp.json();
        if (!resp.ok) return say(data.error || "Save failed", false);
        els.hotkey.value = data.hotkey;
        say("Saved. Applies instantly - no restart needed.", true);
      } catch (e) {
        say("Could not reach the server.", false);
      }
    });
  },
};
