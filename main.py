#!/usr/bin/env python3
"""Sentence Refiner Entry Point.

100% Python Standard Library. Zero external pip dependencies.
"""

import sys
import argparse
from typing import Optional, List

from refiner import RefinerManager
from clipboard import ClipboardManager
from injector import KeyInjector
from ui import RefinePopup
from config import ConfigManager
from history import HistoryManager


def main() -> None:
    config_mgr = ConfigManager()
    history_mgr = HistoryManager()

    parser = argparse.ArgumentParser(
        description="Universal Sentence Refiner - Polish sentences in any app."
    )
    parser.add_argument(
        "--mode",
        choices=["popup", "clipboard", "cli"],
        default="popup",
        help="Execution mode: 'popup' (GUI preview), 'clipboard' (in-place background replace), 'cli' (stdin/stdout).",
    )
    parser.add_argument(
        "--tone",
        choices=["standard", "concise", "professional", "friendly", "bullet_points", "email_formal"],
        default="standard",
        help="Refinement tone style.",
    )
    parser.add_argument(
        "--engine",
        choices=["auto", "rules", "gemini", "openai", "chatgpt", "claude", "anthropic", "ollama", "languagetool"],
        default="auto",
        help="Refinement engine backend.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Custom model name override for chosen engine (e.g. gemini-1.5-pro, gpt-4o, claude-3-5-sonnet).",
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Direct input string (bypasses clipboard in CLI mode).",
    )
    parser.add_argument(
        "--paste",
        action="store_true",
        help="Attempt virtual keystroke paste after writing refined text to clipboard.",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Print recent refinement history and exit.",
    )
    parser.add_argument(
        "--add-whitelist",
        metavar="WORD",
        help="Add a technical word to the dictionary whitelist.",
    )
    parser.add_argument(
        "--add-snippet",
        nargs=2,
        metavar=("SHORTCUT", "EXPANSION"),
        help="Add a custom shortcut snippet (e.g. --add-snippet brb 'be right back').",
    )
    parser.add_argument(
        "--set-key",
        nargs=2,
        metavar=("PROVIDER", "KEY"),
        help="Save API key for gemini, openai, or anthropic/claude into config.",
    )
    parser.add_argument(
        "--show-keys",
        action="store_true",
        help="Display configured API keys status and exit.",
    )

    args = parser.parse_args()

    # Handle API key configuration
    if args.set_key:
        provider, key = args.set_key
        config_mgr.set_api_key(provider, key)
        print(f"Successfully configured API key for '{provider}'.")
        return

    # Handle show keys status
    if args.show_keys:
        print("--- Configured AI API Keys ---")
        for prov in ["gemini", "openai", "anthropic"]:
            key = config_mgr.get_api_key(prov)
            if key:
                masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
                print(f"  {prov.capitalize():<10}: Configured ({masked})")
            else:
                print(f"  {prov.capitalize():<10}: Not configured")
        return

    # Handle whitelist addition
    if args.add_whitelist:
        config_mgr.add_whitelist_word(args.add_whitelist)
        print(f"Added '{args.add_whitelist}' to dictionary whitelist.")
        return

    # Handle snippet addition
    if args.add_snippet:
        config_mgr.add_snippet(args.add_snippet[0], args.add_snippet[1])
        print(f"Added snippet: '{args.add_snippet[0]}' -> '{args.add_snippet[1]}'")
        return

    # Handle history dump
    if args.history:
        entries = history_mgr.get_history(limit=15)
        if not entries:
            print("No history recorded yet.")
            return
        print(f"--- Recent Refinements ({len(entries)}) ---")
        for i, e in enumerate(entries, 1):
            print(f"{i}. [{e['timestamp']}] ({e['tone']}) via {e.get('engine', 'Unknown')}")
            print(f"   Orig: {e['original']}")
            print(f"   Ref : {e['refined']}\n")
        return

    refiner_manager = RefinerManager(
        preferred_engine=args.engine,
        model=args.model,
        config_manager=config_mgr,
    )
    clipboard = ClipboardManager()
    injector = KeyInjector()

    # Mode 1: CLI mode
    if args.mode == "cli":
        input_text = args.text if args.text is not None else sys.stdin.read()
        refined = refiner_manager.refine(input_text, tone=args.tone)
        history_mgr.record(
            original=input_text,
            refined=refined,
            tone=args.tone,
            engine=refiner_manager.get_active_engine().name,
        )
        sys.stdout.write(refined)
        if not refined.endswith("\n"):
            sys.stdout.write("\n")
        return

    # For GUI or Clipboard mode, read highlighted text or clipboard
    if args.text:
        raw_text = args.text
    else:
        # Try primary selection first (text highlighted by user anywhere)
        raw_text = clipboard.get_primary_selection()
        if not raw_text or not raw_text.strip():
            # If not in primary buffer, simulate Ctrl+C to copy highlighted text
            injector.simulate_copy()
            raw_text = clipboard.get_text()

    if not raw_text or not raw_text.strip():
        injector.notify("Sentence Refiner", "No text highlighted or clipboard is empty!")
        return

    raw_text = raw_text.strip()
    active_engine = refiner_manager.get_active_engine()

    # Mode 2: In-place Clipboard Mode (Instant replace without modal)
    if args.mode == "clipboard":
        refined_text = refiner_manager.refine(raw_text, tone=args.tone)
        clipboard.set_text(refined_text)
        history_mgr.record(
            original=raw_text,
            refined=refined_text,
            tone=args.tone,
            engine=active_engine.name,
        )

        pasted = False
        if args.paste:
            pasted = injector.simulate_paste()

        if pasted:
            injector.notify("Sentence Refiner", f"Refined & Pasted ({args.tone}): {refined_text[:40]}...")
        else:
            injector.notify("Sentence Refiner", f"Copied to clipboard ({args.tone}). Press Ctrl+V to paste!")
        return

    # Mode 3: Popup Mode (Google Chat-style interactive preview with Visual Diff)
    initial_refined = refiner_manager.refine(raw_text, tone=args.tone)
    history_items = history_mgr.get_history(limit=10)

    # Determine unique available engines for switcher dropdown
    seen_names = set()
    available_engine_names: List[str] = []
    engine_name_to_key = {}
    for key, engine in refiner_manager.engines.items():
        if key in ["chatgpt", "anthropic"]:
            continue  # skip duplicate aliases
        if engine.is_available() and engine.name not in seen_names:
            seen_names.add(engine.name)
            available_engine_names.append(engine.name)
            engine_name_to_key[engine.name] = key

    current_engine = active_engine

    def on_tone_change(tone: str) -> str:
        return current_engine.refine(raw_text, tone=tone)

    def on_engine_change(engine_display_name: str) -> str:
        nonlocal current_engine
        key = engine_name_to_key.get(engine_display_name)
        if key and key in refiner_manager.engines:
            current_engine = refiner_manager.engines[key]
        return current_engine.refine(raw_text, tone=popup.selected_tone)

    def on_apply(final_text: str) -> None:
        clipboard.set_text(final_text)
        history_mgr.record(
            original=raw_text,
            refined=final_text,
            tone=popup.selected_tone,
            engine=current_engine.name,
        )
        pasted = False
        if args.paste:
            pasted = injector.simulate_paste()
        if not pasted:
            injector.notify("Sentence Refiner", "Refined sentence ready in clipboard! Press Ctrl+V.")

    popup = RefinePopup(
        original_text=raw_text,
        initial_refined_text=initial_refined,
        engine_name=active_engine.name,
        on_tone_change=on_tone_change,
        on_apply=on_apply,
        history_items=history_items,
        available_engines=available_engine_names,
        on_engine_change=on_engine_change,
        config_manager=config_mgr,
        get_explanations=refiner_manager.get_last_explanations,
    )
    popup.show()


if __name__ == "__main__":
    main()
