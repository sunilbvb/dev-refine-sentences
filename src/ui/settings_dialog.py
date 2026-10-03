"""Interactive Settings GUI dialog for managing API keys, whitelist, and snippets.

100% Python Standard Library Tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from config.settings import ConfigManager


class SettingsDialog:
    """Settings modal window for configuring API keys, dictionary whitelist, and snippets."""

    def __init__(self, parent: tk.Tk, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager

    def show(self) -> None:
        dialog = tk.Toplevel(self.parent)
        dialog.title("Settings & Configurations")
        dialog.geometry("540x500")
        dialog.minsize(480, 420)
        dialog.attributes("-topmost", True)
        dialog.configure(bg="#1E1E2E")

        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # ---------------- TAB 1: API Keys ----------------
        tab_keys = tk.Frame(notebook, bg="#1E1E2E", padx=16, pady=16)
        notebook.add(tab_keys, text="AI API Keys")

        tk.Label(
            tab_keys,
            text="Configure Cloud AI API Keys",
            font=("Sans", 11, "bold"),
            fg="#CDD6F4",
            bg="#1E1E2E",
        ).pack(anchor="w", pady=(0, 10))

        # Gemini
        tk.Label(tab_keys, text="Google Gemini Key:", font=("Sans", 9), fg="#BAC2DE", bg="#1E1E2E").pack(anchor="w")
        gemini_entry = tk.Entry(tab_keys, font=("Sans", 10), bg="#313244", fg="#CDD6F4", insertbackground="#CDD6F4", relief=tk.FLAT, bd=4, show="*")
        gemini_entry.pack(fill=tk.X, pady=(2, 8))
        curr_gem = self.config_manager.get_api_key("gemini")
        if curr_gem:
            gemini_entry.insert(0, curr_gem)

        # OpenAI
        tk.Label(tab_keys, text="OpenAI (ChatGPT) Key:", font=("Sans", 9), fg="#BAC2DE", bg="#1E1E2E").pack(anchor="w")
        openai_entry = tk.Entry(tab_keys, font=("Sans", 10), bg="#313244", fg="#CDD6F4", insertbackground="#CDD6F4", relief=tk.FLAT, bd=4, show="*")
        openai_entry.pack(fill=tk.X, pady=(2, 8))
        curr_oa = self.config_manager.get_api_key("openai")
        if curr_oa:
            openai_entry.insert(0, curr_oa)

        # Anthropic
        tk.Label(tab_keys, text="Anthropic (Claude) Key:", font=("Sans", 9), fg="#BAC2DE", bg="#1E1E2E").pack(anchor="w")
        anthropic_entry = tk.Entry(tab_keys, font=("Sans", 10), bg="#313244", fg="#CDD6F4", insertbackground="#CDD6F4", relief=tk.FLAT, bd=4, show="*")
        anthropic_entry.pack(fill=tk.X, pady=(2, 14))
        curr_ant = self.config_manager.get_api_key("anthropic")
        if curr_ant:
            anthropic_entry.insert(0, curr_ant)

        def save_keys():
            self.config_manager.set_api_key("gemini", gemini_entry.get().strip())
            self.config_manager.set_api_key("openai", openai_entry.get().strip())
            self.config_manager.set_api_key("anthropic", anthropic_entry.get().strip())
            messagebox.showinfo("Success", "API Keys saved successfully!", parent=dialog)

        tk.Button(
            tab_keys,
            text="Save API Keys",
            font=("Sans", 9, "bold"),
            bg="#A6E3A1",
            fg="#11111B",
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=save_keys,
        ).pack(anchor="w")

        # ---------------- TAB 2: Whitelist ----------------
        tab_wl = tk.Frame(notebook, bg="#1E1E2E", padx=16, pady=16)
        notebook.add(tab_wl, text="Whitelist Dictionary")

        tk.Label(
            tab_wl,
            text="Protected Terms (Never altered by rules/AI):",
            font=("Sans", 10, "bold"),
            fg="#CDD6F4",
            bg="#1E1E2E",
        ).pack(anchor="w", pady=(0, 6))

        wl_listbox = tk.Listbox(tab_wl, font=("Sans", 10), bg="#313244", fg="#CDD6F4", relief=tk.FLAT, bd=4, height=8)
        wl_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        def refresh_wl():
            wl_listbox.delete(0, tk.END)
            for w in self.config_manager.get_whitelist():
                wl_listbox.insert(tk.END, w)

        refresh_wl()

        wl_input_frame = tk.Frame(tab_wl, bg="#1E1E2E")
        wl_input_frame.pack(fill=tk.X)

        wl_entry = tk.Entry(wl_input_frame, font=("Sans", 10), bg="#313244", fg="#CDD6F4", insertbackground="#CDD6F4", relief=tk.FLAT, bd=4)
        wl_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        def add_wl():
            w = wl_entry.get().strip()
            if w:
                self.config_manager.add_whitelist_word(w)
                wl_entry.delete(0, tk.END)
                refresh_wl()

        def del_wl():
            sel = wl_listbox.curselection()
            if sel:
                word = wl_listbox.get(sel[0])
                cfg = self.config_manager.load_config()
                if word in cfg.get("whitelist", []):
                    cfg["whitelist"].remove(word)
                    self.config_manager._save_config(cfg)
                    refresh_wl()

        tk.Button(wl_input_frame, text="Add Term", font=("Sans", 9, "bold"), bg="#89B4FA", fg="#11111B", relief=tk.FLAT, bd=0, padx=10, pady=4, cursor="hand2", command=add_wl).pack(side=tk.LEFT, padx=2)
        tk.Button(wl_input_frame, text="Remove Selected", font=("Sans", 9), bg="#45475A", fg="#CDD6F4", relief=tk.FLAT, bd=0, padx=8, pady=4, cursor="hand2", command=del_wl).pack(side=tk.LEFT)

        # ---------------- TAB 3: Snippets ----------------
        tab_snip = tk.Frame(notebook, bg="#1E1E2E", padx=16, pady=16)
        notebook.add(tab_snip, text="Text Snippets")

        tk.Label(
            tab_snip,
            text="Custom Expansion Snippets (Supports {{date}}, {{time}}, {{year}}):",
            font=("Sans", 9, "bold"),
            fg="#CDD6F4",
            bg="#1E1E2E",
        ).pack(anchor="w", pady=(0, 6))

        snip_listbox = tk.Listbox(tab_snip, font=("Sans", 9), bg="#313244", fg="#CDD6F4", relief=tk.FLAT, bd=4, height=7)
        snip_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        def refresh_snips():
            snip_listbox.delete(0, tk.END)
            for k, v in self.config_manager.get_snippets().items():
                snip_listbox.insert(tk.END, f"{k}  →  {v}")

        refresh_snips()

        snip_form = tk.Frame(tab_snip, bg="#1E1E2E")
        snip_form.pack(fill=tk.X, pady=(0, 6))

        shortcut_entry = tk.Entry(snip_form, font=("Sans", 9), bg="#313244", fg="#CDD6F4", insertbackground="#CDD6F4", relief=tk.FLAT, bd=4, width=12)
        shortcut_entry.pack(side=tk.LEFT, padx=(0, 6))
        shortcut_entry.insert(0, "shortcut")

        expansion_entry = tk.Entry(snip_form, font=("Sans", 9), bg="#313244", fg="#CDD6F4", insertbackground="#CDD6F4", relief=tk.FLAT, bd=4)
        expansion_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        expansion_entry.insert(0, "Full expanded text")

        def add_snip():
            sc = shortcut_entry.get().strip()
            exp = expansion_entry.get().strip()
            if sc and exp:
                self.config_manager.add_snippet(sc, exp)
                refresh_snips()

        def del_snip():
            sel = snip_listbox.curselection()
            if sel:
                item = snip_listbox.get(sel[0])
                sc = item.split("  →  ")[0].strip()
                cfg = self.config_manager.load_config()
                if sc in cfg.get("snippets", {}):
                    del cfg["snippets"][sc]
                    self.config_manager._save_config(cfg)
                    refresh_snips()

        snip_btn_frame = tk.Frame(tab_snip, bg="#1E1E2E")
        snip_btn_frame.pack(fill=tk.X)
        tk.Button(snip_btn_frame, text="Add / Update Snippet", font=("Sans", 9, "bold"), bg="#89B4FA", fg="#11111B", relief=tk.FLAT, bd=0, padx=10, pady=4, cursor="hand2", command=add_snip).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(snip_btn_frame, text="Remove Selected", font=("Sans", 9), bg="#45475A", fg="#CDD6F4", relief=tk.FLAT, bd=0, padx=8, pady=4, cursor="hand2", command=del_snip).pack(side=tk.LEFT)

        dialog.transient(self.parent)
        dialog.grab_set()
