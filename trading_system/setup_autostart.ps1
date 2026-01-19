# PowerShell script to set up Windows Task Scheduler for auto-start
# Run this script as Administrator to set up auto-start

$taskName = "TradingSystem_StrategyB"
$scriptPath = "C:\Development\Agent\trading_system\start_trading_system.bat"
$workingDir = "C:\Development\Agent\trading_system"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the scheduled task
Write-Host "Creating scheduled task..." -ForegroundColor Green

$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Automated Trading System - Strategy B (XM/MT5)"

Write-Host "Task created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "The trading system will now start automatically when you log in." -ForegroundColor Cyan
Write-Host "To disable: Open Task Scheduler and disable/delete the task '$taskName'" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: Make sure MetaTrader 5 is set to auto-start as well!" -ForegroundColor Yellow
pause















