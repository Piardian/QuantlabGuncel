param(
    [string]$TaskName = "back tester paper trading",
    [datetime]$RunAt = (Get-Date "23:30")
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $projectRoot "run_paper_trading.bat"

if (-not (Test-Path $launcher)) {
    throw "Launcher not found: $launcher"
}

$action = New-ScheduledTaskAction `
    -Execute $env:ComSpec `
    -Argument ('/d /c ""{0}""' -f $launcher) `
    -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At $RunAt

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -WakeToRun `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force `
        -ErrorAction Stop | Out-Null

    Write-Host "Created '$TaskName' for Monday-Friday at $($RunAt.ToString('HH:mm'))."
}
catch {
    Write-Error "Could not update '$TaskName'. Run PowerShell as Administrator and try again. $($_.Exception.Message)"
    exit 1
}
