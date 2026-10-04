@echo off
REM setup_shortcuts_win.bat - Create native Windows global shortcut hooks for Sentence Refiner

echo ==> Setting up Windows Global Hotkey Shortcuts...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
  "$py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source; " ^
  "if (-not $py) { $py = 'python.exe' }; " ^
  "$proj = (Get-Item '%~dp0..').FullName; " ^
  "$s1 = $ws.CreateShortcut(\"$desktop\Refine Sentence (Popup).lnk\"); " ^
  "$s1.TargetPath = $py; " ^
  "$s1.Arguments = \"`\"$proj\main.py`\" --mode=popup --paste\"; " ^
  "$s1.Hotkey = 'CTRL+ALT+R'; " ^
  "$s1.WindowStyle = 7; " ^
  "$s1.Description = 'Universal Sentence Refiner (Popup Preview)'; " ^
  "$s1.Save(); " ^
  "$s2 = $ws.CreateShortcut(\"$desktop\Refine Sentence (Flash).lnk\"); " ^
  "$s2.TargetPath = $py; " ^
  "$s2.Arguments = \"`\"$proj\main.py`\" --mode=clipboard --paste\"; " ^
  "$s2.Hotkey = 'CTRL+SHIFT+R'; " ^
  "$s2.WindowStyle = 7; " ^
  "$s2.Description = 'Universal Sentence Refiner (Instant Flash)'; " ^
  "$s2.Save(); " ^
  "Write-Host '==> Created global shortcut links on Desktop:';" ^
  "Write-Host '    [Ctrl+Alt+R]   -> Sentence Refiner (Popup)'; " ^
  "Write-Host '    [Ctrl+Shift+R] -> Sentence Refiner (Flash)'; "

echo ==> Done! Shortcuts active globally in any Windows app.
pause
