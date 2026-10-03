"""Interactive floating preview popup for sentence refinement.

Features:
- Word-level Visual Diff (Red strikethrough deletions, Green bold additions)
- Multi-tone switcher (Standard, Concise, Professional, Friendly, Bullets, Email)
- Refinement History & Undo Buffer
- Live Flesch-Kincaid Readability & Ease metrics
- Teach / Explanation Mode ("Why Changed?")
- Built-in Settings Dialog (API Keys, Whitelist, Snippets)
- 100% Python Standard Library Tkinter.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Dict, Any
from .diff_highlighter import compute_word_diff
from .settings_dialog import SettingsDialog
from metrics.readability import analyze_readability
from config.settings import ConfigManager


class RefinePopup:
    """Floating modal window showing original text, diff preview, teach explanations, and tones."""

    def __init__(
        self,
        original_text: str,
        initial_refined_text: str,
        engine_name: str,
        on_tone_change: Callable[[str], str],
        on_apply: Callable[[str], None],
        history_items: Optional[List[Dict[str, Any]]] = None,
        available_engines: Optional[List[str]] = None,
        on_engine_change: Optional[Callable[[str], str]] = None,
        config_manager: Optional[ConfigManager] = None,
        get_explanations: Optional[Callable[[], List[str]]] = None,
    ):
        self.original_text = original_text
        self.current_refined = initial_refined_text
        self.engine_name = engine_name
        self.on_tone_change = on_tone_change
        self.on_apply = on_apply
        self.history_items = history_items or []
        self.available_engines = available_engines or []
        self.on_engine_change = on_engine_change
        self.config_manager = config_manager or ConfigManager()
        self.get_explanations = get_explanations
        self.selected_tone = "standard"
        self.view_mode = "diff"  # 'diff' or 'edit'

    def show(self) -> None:
        """Launch the preview dialog."""
        root = tk.Tk()
        root.title("Sentence Refiner")
        root.geometry("640x620")
        root.minsize(560, 520)
        root.attributes("-topmost", True)
        root.configure(bg="#1E1E2E")

        # Top Header Frame
        header_frame = tk.Frame(root, bg="#1E1E2E", pady=8, padx=16)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="✨ Sentence Refiner",
            font=("Sans", 14, "bold"),
            fg="#CDD6F4",
            bg="#1E1E2E",
        )
        title_lbl.pack(side=tk.LEFT)

        # Settings Button
        settings_btn = tk.Button(
            header_frame,
            text="⚙️ Settings",
            font=("Sans", 8, "bold"),
            bg="#313244",
            fg="#CDD6F4",
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=lambda: SettingsDialog(root, self.config_manager).show(),
        )
        settings_btn.pack(side=tk.RIGHT, padx=(6, 0))

        if self.available_engines and self.on_engine_change:
            engine_var = tk.StringVar(value=self.engine_name)
            engine_combo = ttk.Combobox(
                header_frame,
                textvariable=engine_var,
                values=self.available_engines,
                state="readonly",
                width=20,
                font=("Sans", 8),
            )
            engine_combo.pack(side=tk.RIGHT)

            def on_engine_selected(e=None):
                new_engine = engine_var.get()
                self.engine_name = new_engine
                updated = self.on_engine_change(new_engine)
                self.current_refined = updated
                render_preview()
                update_metrics_display()
                update_teach_display()

            engine_combo.bind("<<ComboboxSelected>>", on_engine_selected)
        else:
            engine_lbl = tk.Label(
                header_frame,
                text=f"Engine: {self.engine_name}",
                font=("Sans", 8),
                fg="#A6ADC8",
                bg="#313244",
                padx=8,
                pady=3,
            )
            engine_lbl.pack(side=tk.RIGHT)

        # Tone Selector Bar
        tone_frame = tk.Frame(root, bg="#1E1E2E", padx=16, pady=4)
        tone_frame.pack(fill=tk.X)

        tk.Label(
            tone_frame,
            text="Tone:",
            font=("Sans", 9, "bold"),
            fg="#BAC2DE",
            bg="#1E1E2E",
        ).pack(side=tk.LEFT, padx=(0, 6))

        tone_buttons: Dict[str, tk.Button] = {}

        tones = [
            ("Standard", "standard"),
            ("Concise", "concise"),
            ("Professional", "professional"),
            ("Friendly", "friendly"),
            ("Bullets", "bullet_points"),
            ("Email", "email_formal"),
        ]

        def update_metrics_display():
            orig_words = len(self.original_text.split())
            ref_words = len(self.current_refined.split())
            diff = ref_words - orig_words
            diff_str = f"+{diff}" if diff > 0 else f"{diff}"
            pct = round((diff / orig_words * 100)) if orig_words > 0 else 0
            pct_str = f"+{pct}%" if pct > 0 else f"{pct}%"

            # Linguistic & Readability analysis
            analysis = analyze_readability(self.current_refined)
            metrics_lbl.configure(
                text=f"Words: {orig_words} → {ref_words} ({diff_str}, {pct_str}) | Ease: {analysis['reading_ease']} ({analysis['label']}) | Grade: {analysis['grade_level']}"
            )

        def update_teach_display():
            if not self.get_explanations:
                teach_frame.pack_forget()
                return

            explanations = self.get_explanations()
            if explanations:
                teach_text.configure(state=tk.NORMAL)
                teach_text.delete("1.0", tk.END)
                for exp in explanations[:4]:
                    teach_text.insert(tk.END, f"• {exp}\n")
                teach_text.configure(state=tk.DISABLED)
                teach_frame.pack(fill=tk.X, padx=16, pady=(0, 4), before=actions_frame)
            else:
                teach_frame.pack_forget()

        def set_tone(tone: str):
            self.selected_tone = tone
            for t_key, btn in tone_buttons.items():
                if t_key == tone:
                    btn.configure(bg="#89B4FA", fg="#11111B")
                else:
                    btn.configure(bg="#45475A", fg="#CDD6F4")

            updated = self.on_tone_change(tone)
            self.current_refined = updated
            render_preview()
            update_metrics_display()
            update_teach_display()

        for label, key in tones:
            btn = tk.Button(
                tone_frame,
                text=label,
                font=("Sans", 8, "bold"),
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=3,
                cursor="hand2",
                command=lambda k=key: set_tone(k),
            )
            btn.pack(side=tk.LEFT, padx=2)
            tone_buttons[key] = btn

        tone_buttons["standard"].configure(bg="#89B4FA", fg="#11111B")
        for k in ["concise", "professional", "friendly", "bullet_points", "email_formal"]:
            tone_buttons[k].configure(bg="#45475A", fg="#CDD6F4")

        # View Mode & Metrics Bar
        subbar_frame = tk.Frame(root, bg="#1E1E2E", padx=16, pady=4)
        subbar_frame.pack(fill=tk.X)

        view_toggle_btn = tk.Button(
            subbar_frame,
            text="👁 Diff View (Active)",
            font=("Sans", 8, "bold"),
            bg="#A6E3A1",
            fg="#11111B",
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
        )
        view_toggle_btn.pack(side=tk.LEFT)

        metrics_lbl = tk.Label(
            subbar_frame,
            text="",
            font=("Sans", 8),
            fg="#A6ADC8",
            bg="#1E1E2E",
        )
        metrics_lbl.pack(side=tk.RIGHT)

        # Content Box
        content_frame = tk.Frame(root, bg="#1E1E2E", padx=16, pady=4)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Original Input
        tk.Label(
            content_frame,
            text="Original Input:",
            font=("Sans", 9, "bold"),
            fg="#A6ADC8",
            bg="#1E1E2E",
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 2))

        input_box = tk.Text(
            content_frame,
            height=3,
            wrap=tk.WORD,
            font=("Sans", 10),
            bg="#313244",
            fg="#BAC2DE",
            insertbackground="#CDD6F4",
            relief=tk.FLAT,
            bd=4,
        )
        input_box.pack(fill=tk.X, pady=(0, 6))
        input_box.insert("1.0", self.original_text)

        # Preview / Edit Box
        preview_label = tk.Label(
            content_frame,
            text="Refined Output (Visual Diff):",
            font=("Sans", 9, "bold"),
            fg="#A6ADC8",
            bg="#1E1E2E",
            anchor="w",
        )
        preview_label.pack(fill=tk.X, pady=(0, 2))

        output_box = tk.Text(
            content_frame,
            height=5,
            wrap=tk.WORD,
            font=("Sans", 11),
            bg="#181825",
            fg="#CDD6F4",
            insertbackground="#A6E3A1",
            relief=tk.FLAT,
            bd=6,
        )
        output_box.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # Setup Tag Configurations for Visual Word Diff
        output_box.tag_configure("diff_del", foreground="#F38BA8", overstrike=True, background="#31202A")
        output_box.tag_configure("diff_add", foreground="#A6E3A1", font=("Sans", 11, "bold"), background="#1E3A2B")
        output_box.tag_configure("diff_eq", foreground="#CDD6F4")

        def render_preview():
            output_box.delete("1.0", tk.END)
            if self.view_mode == "diff":
                preview_label.configure(text="Refined Output (Visual Diff - Changes Highlighted):")
                tokens = compute_word_diff(self.original_text, self.current_refined)
                for tag, text in tokens:
                    if tag == "del":
                        output_box.insert(tk.END, text, "diff_del")
                    elif tag == "add":
                        output_box.insert(tk.END, text, "diff_add")
                    else:
                        output_box.insert(tk.END, text, "diff_eq")
            else:
                preview_label.configure(text="Refined Output (Direct Editor):")
                output_box.insert("1.0", self.current_refined)

        def toggle_view():
            if self.view_mode == "diff":
                self.view_mode = "edit"
                view_toggle_btn.configure(text="✏️ Edit View (Active)", bg="#89B4FA", fg="#11111B")
            else:
                self.current_refined = output_box.get("1.0", tk.END).strip()
                self.view_mode = "diff"
                view_toggle_btn.configure(text="👁 Diff View (Active)", bg="#A6E3A1", fg="#11111B")
            render_preview()

        view_toggle_btn.configure(command=toggle_view)

        # History Frame
        history_frame = tk.Frame(root, bg="#1E1E2E", padx=16, pady=2)
        history_frame.pack(fill=tk.X)

        history_var = tk.StringVar(value="Recent History (Click to restore)")
        if self.history_items:
            history_options = [
                f"[{item.get('tone', 'std')}] {item.get('original', '')[:45]}..."
                for item in self.history_items[:8]
            ]

            def on_history_selected(choice: str):
                for item in self.history_items:
                    snippet = f"[{item.get('tone', 'std')}] {item.get('original', '')[:45]}..."
                    if snippet == choice:
                        self.original_text = item.get("original", "")
                        self.current_refined = item.get("refined", "")
                        input_box.delete("1.0", tk.END)
                        input_box.insert("1.0", self.original_text)
                        render_preview()
                        update_metrics_display()
                        update_teach_display()
                        break

            history_dropdown = ttk.Combobox(
                history_frame,
                textvariable=history_var,
                values=history_options,
                state="readonly",
                font=("Sans", 8),
            )
            history_dropdown.pack(fill=tk.X, pady=(0, 2))
            history_dropdown.bind("<<ComboboxSelected>>", lambda e: on_history_selected(history_var.get()))

        # Teach / Explanation Frame
        teach_frame = tk.Frame(root, bg="#2A2B3C", padx=10, pady=4, relief=tk.FLAT)
        tk.Label(
            teach_frame,
            text="💡 Teach Mode (Why Changed):",
            font=("Sans", 8, "bold"),
            fg="#F9E2AF",
            bg="#2A2B3C",
            anchor="w",
        ).pack(fill=tk.X)

        teach_text = tk.Text(
            teach_frame,
            height=2,
            wrap=tk.WORD,
            font=("Sans", 8),
            bg="#2A2B3C",
            fg="#BAC2DE",
            relief=tk.FLAT,
            bd=0,
        )
        teach_text.pack(fill=tk.X)

        # Bottom Actions Bar
        actions_frame = tk.Frame(root, bg="#1E1E2E", padx=16, pady=8)
        actions_frame.pack(fill=tk.X)

        hint_label = tk.Label(
            actions_frame,
            text="[Enter] Apply & Copy    [Esc] Cancel    [Alt+D] Toggle Diff",
            font=("Sans", 8),
            fg="#6C7086",
            bg="#1E1E2E",
        )
        hint_label.pack(side=tk.LEFT)

        def apply_action(event=None):
            if self.view_mode == "edit":
                final_text = output_box.get("1.0", tk.END).strip()
            else:
                final_text = self.current_refined.strip()
            root.destroy()
            self.on_apply(final_text)

        def cancel_action(event=None):
            root.destroy()

        cancel_btn = tk.Button(
            actions_frame,
            text="Cancel",
            font=("Sans", 10),
            bg="#45475A",
            fg="#CDD6F4",
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=cancel_action,
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(6, 0))

        apply_btn = tk.Button(
            actions_frame,
            text="Apply & Copy",
            font=("Sans", 10, "bold"),
            bg="#A6E3A1",
            fg="#11111B",
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=apply_action,
        )
        apply_btn.pack(side=tk.RIGHT)

        root.bind("<Return>", lambda e: apply_action())
        root.bind("<Escape>", lambda e: cancel_action())
        root.bind("<Alt-d>", lambda e: toggle_view())

        # Initial Render
        render_preview()
        update_metrics_display()
        update_teach_display()

        # Center on screen
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"+{x}+{y}")

        root.mainloop()
