# Stock Analysis System - PowerShell Launcher
param(
    [switch]$Background,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Log,
    [int]$Port = 9000,
    [string]$Mode = ""
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Header {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Stock Analysis System" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Port {
    param([int]$PortNum)
    $result = netstat -an | Select-String ":$PortNum\s.*LISTENING"
    return $result -ne $null
}

function Get-PortProcess {
    param([int]$PortNum)
    $connection = Get-NetTCPConnection -LocalPort $PortNum -ErrorAction SilentlyContinue |
                  Where-Object { $_.State -eq "Listen" }
    if ($connection) {
        $procId = $connection.OwningProcess
        return Get-Process -Id $procId -ErrorAction SilentlyContinue
    }
    return $null
}

function Stop-PortProcess {
    param([int]$PortNum)
    $process = Get-PortProcess -PortNum $PortNum
    if ($process) {
        Write-Host "[INFO] Port $PortNum used by $($process.Name) (PID: $($process.Id))" -ForegroundColor Yellow
        $confirm = Read-Host "Stop this process? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Stop-Process -Id $process.Id -Force
            Start-Sleep -Seconds 1
            Write-Host "[OK] Process stopped" -ForegroundColor Green
            return $true
        }
        return $false
    }
    return $true
}

function Find-AvailablePort {
    param([int]$StartPort = 9000)
    $port = $StartPort
    while (Test-Port -PortNum $port) {
        $port++
        if ($port -gt 9100) {
            Write-Host "[ERROR] No available port found" -ForegroundColor Red
            exit 1
        }
    }
    return $port
}

# Stop service
if ($Stop) {
    Write-Header
    Write-Host "[STOP] Stopping services..." -ForegroundColor Yellow
    
    $process = Get-PortProcess -PortNum $Port
    if ($process) {
        Stop-Process -Id $process.Id -Force
        Write-Host "[OK] Stopped process on port $Port" -ForegroundColor Green
    } else {
        Write-Host "[INFO] No service running on port $Port" -ForegroundColor Yellow
    }
    
    Write-Host "[DONE]" -ForegroundColor Green
    exit 0
}

# Check status
if ($Status) {
    Write-Header
    Write-Host "[STATUS] Checking..." -ForegroundColor Cyan
    
    if (Test-Port -PortNum $Port) {
        $process = Get-PortProcess -PortNum $Port
        if ($process) {
            Write-Host "[RUNNING] Port $Port - $($process.Name) (PID: $($process.Id))" -ForegroundColor Green
            Write-Host "[URL] http://127.0.0.1:$Port" -ForegroundColor Cyan
        }
    } else {
        Write-Host "[STOPPED] No service on port $Port" -ForegroundColor Yellow
    }
    
    exit 0
}

# View logs
if ($Log) {
    Write-Header
    $logDir = Join-Path $ProjectDir "logs"
    if (Test-Path $logDir) {
        $latestLog = Get-ChildItem -Path $logDir -Filter "stock_analysis_*.log" |
                     Sort-Object LastWriteTime -Descending |
                     Select-Object -First 1
        if ($latestLog) {
            Write-Host "[LOG] $($latestLog.Name)" -ForegroundColor Cyan
            Write-Host ("-" * 50)
            Get-Content $latestLog.FullName -Tail 50
        } else {
            Write-Host "[INFO] No log files found" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[INFO] Log directory not found" -ForegroundColor Yellow
    }
    
    exit 0
}

# Main startup
Write-Header

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found" -ForegroundColor Red
    exit 1
}

# Interactive mode selection
if ([string]::IsNullOrEmpty($Mode)) {
    Write-Host "Select mode:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. WebUI Dashboard" -ForegroundColor White
    Write-Host "  2. Single Analysis" -ForegroundColor White
    Write-Host "  3. Scheduled Task" -ForegroundColor White
    Write-Host "  4. Debug Mode" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Enter choice (1-4)"
    
    switch ($choice) {
        "1" { $Mode = "webui" }
        "2" { $Mode = "analyze" }
        "3" { $Mode = "schedule" }
        "4" { $Mode = "debug" }
        default { $Mode = "webui" }
    }
}

# Handle port conflict
if ($Mode -eq "webui" -or $Mode -eq "schedule") {
    if (Test-Port -PortNum $Port) {
        Write-Host "[WARN] Port $Port is in use" -ForegroundColor Yellow
        $freed = Stop-PortProcess -PortNum $Port
        if (-not $freed) {
            $Port = Find-AvailablePort -StartPort 9001
            Write-Host "[SWITCH] Using port $Port" -ForegroundColor Cyan
        }
    }
}

# Build command
$mainScript = Join-Path $ProjectDir "main.py"
$pythonArgs = @($mainScript)

switch ($Mode) {
    "webui" {
        $pythonArgs += @("--webui", "--host", "0.0.0.0", "--port", $Port.ToString())
        Write-Host "[START] WebUI mode" -ForegroundColor Green
        Write-Host "[URL] http://192.168.222.226:$Port" -ForegroundColor Cyan
    }
    "analyze" {
        Write-Host "[START] Single analysis" -ForegroundColor Green
    }
    "schedule" {
        $pythonArgs += @("--schedule")
        Write-Host "[START] Scheduled mode" -ForegroundColor Green
    }
    "debug" {
        $pythonArgs += @("--debug", "--stocks", "600519,300750,601899")
        Write-Host "[START] Debug mode" -ForegroundColor Green
    }
}

Write-Host ""

# Background mode
if ($Background) {
    Write-Host "[BG] Starting background process..." -ForegroundColor Cyan
    
    $processArgs = @{
        FilePath = "python"
        ArgumentList = $pythonArgs
        WindowStyle = "Minimized"
        PassThru = $true
    }
    
    $process = Start-Process @processArgs
    Write-Host "[OK] Background process started (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "[LOG] View logs: .\start.ps1 -Log" -ForegroundColor Yellow
    Write-Host "[STOP] Stop service: .\start.ps1 -Stop" -ForegroundColor Yellow
} else {
    Write-Host "[RUNNING] Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    & python @pythonArgs
}

Write-Host ""
Write-Host "[DONE]" -ForegroundColor Green
