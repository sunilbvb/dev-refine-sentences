; refine_shortcuts.ahk - AutoHotkey (v1/v2 compatible) for Sentence Refiner

; Ctrl + Alt + R -> Popup Preview
^!r::
Run, python "%A_ScriptDir%\..\main.py" --mode=popup --paste,, Hide
return

; Ctrl + Shift + R -> Instant In-Place Flash
^+r::
Run, python "%A_ScriptDir%\..\main.py" --mode=clipboard --paste,, Hide
return
