# setup_task.ps1
# Registers Auto Sort Folder as a Windows logon task.
#
# HOW TO RUN:
#   1. Open PowerShell on Windows (not WSL) — no admin needed.
#   2. Navigate to this folder:
#        cd "\\wsl$\Ubuntu\home\sdocx\Auto-Sort-Folder"
#   3. Allow the script to run (one-time):
#        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   4. Run:
#        .\setup_task.ps1
#
# TO REMOVE THE TASK LATER:
#   Unregister-ScheduledTask -TaskName "AutoSortFolder" -Confirm:$false

$TaskName   = "AutoSortFolder"
$ScriptPath = "/home/sdocx/Auto-Sort-Folder/gui.py"
$WslUser    = "sdocx"

# ── Action: call wsl.exe which invokes Python inside your default distro ──
$action = New-ScheduledTaskAction `
    -Execute  "wsl.exe" `
    -Argument "python3 $ScriptPath"

# ── Trigger: fire when the current Windows user logs on ───────────────────
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# ── Settings ──────────────────────────────────────────────────────────────
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit      0 `
    -AllowStartIfOnBatteries   `
    -DontStopIfGoingOnBatteries

# ── Principal: run as the current user, no elevation required ─────────────
$principal = New-ScheduledTaskPrincipal `
    -UserId   "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel  Limited

# ── Register ──────────────────────────────────────────────────────────────
Register-ScheduledTask `
    -TaskName   $TaskName `
    -Action     $action `
    -Trigger    $trigger `
    -Settings   $settings `
    -Principal  $principal `
    -Description "Watches your Downloads folder and sorts files automatically." `
    -Force | Out-Null

Write-Host ""
Write-Host "  Task '$TaskName' registered successfully." -ForegroundColor Green
Write-Host "  Auto Sort Folder will launch automatically at your next logon." -ForegroundColor Green
Write-Host ""
Write-Host "  To remove it later, run:" -ForegroundColor Gray
Write-Host "    Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
