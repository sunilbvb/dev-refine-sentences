# Frequently Asked Questions (FAQ)

### Q: Does this work in Antigravity, Google Chrome, ChatGPT, Claude web, and Slack?
A: **Yes, 100%!** It works in every text input field on your system. Whenever you highlight text in any application (browser, IDE, terminal, chat), Linux automatically puts it in the primary selection buffer, or the tool simulates a fast copy via `Atspi`. When you hit Enter on the suggestion, the tool replaces your selected text immediately with the refined version.

### Q: Do I need to press Ctrl+C before pressing the shortcut?
A: **No!** Just highlight the text (with mouse drag or `Shift+Arrows`) and press `Ctrl+Alt+R`. The tool automatically grabs the highlighted text.

### Q: What is Teach Mode ("Why Changed?")?
A: Teach Mode explains the exact grammatical, typographical, or stylistic reasons why text was altered. When using the built-in rule engine, the popup window displays notes such as:
- *"Grammar: Subject-verb agreement: third-person singular uses 'goes'."*
- *"Irregular verb: 'buy' past tense is 'bought'."*
- *"Conciseness: Removed filler word 'basically'."*

### Q: How does it automatically replace the text?
A: When you click **Apply & Copy** or press **Enter** in the suggestion popup, the popup closes, focuses back to your previous application, and uses native Linux `Atspi` to send a `Ctrl+V` keystroke. Because your rough text is already highlighted, the paste immediately replaces it.

### Q: How does Instant Flash Mode work?
A: If you don't want a popup dialog and just want instant in-place refinement, bind `refine_flash.sh` to a hotkey (like `Super+Shift+R`). It grabs selected text, refines it silently, and pastes it back in ~50ms!
