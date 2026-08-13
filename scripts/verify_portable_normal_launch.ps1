param(
    [Parameter(Mandatory = $true)]
    [string]$PortableRoot,
    [Parameter(Mandatory = $true)]
    [string]$ScreenshotPath,
    [Parameter(Mandatory = $true)]
    [string]$ResultPath,
    [ValidateRange(10, 60)]
    [int]$TimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class FlatShotNativeWindow {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);

    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint message, IntPtr wParam, IntPtr lParam);
}
"@

function Get-NamedProcessSnapshot {
    param([string[]]$Names)
    $items = @()
    foreach ($name in $Names) {
        $items += @(Get-Process -Name $name -ErrorAction SilentlyContinue)
    }
    return @($items | Sort-Object Id -Unique)
}

function Get-VisibleWindows {
    param([int[]]$ProcessIds)
    $wanted = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($id in $ProcessIds) {
        [void]$wanted.Add($id)
    }
    $windows = [System.Collections.Generic.List[object]]::new()
    $callback = [FlatShotNativeWindow+EnumWindowsProc]{
        param([IntPtr]$handle, [IntPtr]$unused)
        $owner = [uint32]0
        [void][FlatShotNativeWindow]::GetWindowThreadProcessId($handle, [ref]$owner)
        if ($wanted.Contains([int]$owner) -and [FlatShotNativeWindow]::IsWindowVisible($handle)) {
            $titleBuffer = [System.Text.StringBuilder]::new(512)
            [void][FlatShotNativeWindow]::GetWindowText($handle, $titleBuffer, $titleBuffer.Capacity)
            $windows.Add([pscustomobject]@{
                Handle = $handle.ToInt64()
                ProcessId = [int]$owner
                Title = $titleBuffer.ToString()
            })
        }
        return $true
    }
    [void][FlatShotNativeWindow]::EnumWindows($callback, [IntPtr]::Zero)
    return @($windows)
}

function Get-OwnedListenerPorts {
    param([int[]]$ProcessIds)
    if (-not $ProcessIds) {
        return @()
    }
    $ports = foreach ($id in $ProcessIds) {
        Get-NetTCPConnection -State Listen -OwningProcess $id -ErrorAction SilentlyContinue |
            Where-Object { $_.LocalAddress -in @("127.0.0.1", "::1") } |
            Select-Object -ExpandProperty LocalPort
    }
    return @($ports | Sort-Object -Unique)
}

function Invoke-LocalHttp {
    param([string]$Uri)
    try {
        $response = Invoke-WebRequest -Uri $Uri -Method Get -TimeoutSec 2 -MaximumRedirection 0 -NoProxy
        return [pscustomobject]@{
            Status = [int]$response.StatusCode
            Content = [string]$response.Content
        }
    }
    catch {
        return $null
    }
}

function Find-LocalEndpoints {
    param([int[]]$Ports)
    $frontend = $null
    $bridge = $null
    foreach ($port in $Ports) {
        $healthUrl = "http://127.0.0.1:$port/health"
        $health = Invoke-LocalHttp -Uri $healthUrl
        if ($null -ne $health -and $health.Status -eq 200) {
            try {
                $payload = $health.Content | ConvertFrom-Json
                if ($payload.ok -eq $true) {
                    $bridge = [pscustomobject]@{ status = 200; url = $healthUrl }
                }
            }
            catch {
            }
        }

        $frontendUrl = "http://127.0.0.1:$port/"
        $root = Invoke-LocalHttp -Uri $frontendUrl
        if ($null -ne $root -and $root.Status -eq 200 -and $root.Content -match "(?i)<(?:!doctype|html)|FlatShot") {
            $frontend = [pscustomobject]@{ status = 200; url = $frontendUrl }
        }
    }
    return [pscustomobject]@{ Frontend = $frontend; Bridge = $bridge }
}

function Save-WindowScreenshot {
    param([long]$Handle, [string]$Path)
    $rect = [FlatShotNativeWindow+RECT]::new()
    if (-not [FlatShotNativeWindow]::GetWindowRect([IntPtr]$Handle, [ref]$rect)) {
        throw "GetWindowRect failed for handle $Handle."
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -lt 320 -or $height -lt 200) {
        throw "FlatShot window is unexpectedly small: ${width}x${height}."
    }

    $directory = Split-Path -Parent $Path
    if ($directory) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    $bitmap = [System.Drawing.Bitmap]::new($width, $height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $hdc = $graphics.GetHdc()
    try {
        if (-not [FlatShotNativeWindow]::PrintWindow([IntPtr]$Handle, $hdc, 2)) {
            throw "PrintWindow failed for FlatShot handle $Handle."
        }
    }
    finally {
        $graphics.ReleaseHdc($hdc)
        $graphics.Dispose()
    }

    try {
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
        $colors = [System.Collections.Generic.HashSet[int]]::new()
        $minimumBrightness = 1.0
        $maximumBrightness = 0.0
        $stepX = [Math]::Max(1, [int]($width / 24))
        $stepY = [Math]::Max(1, [int]($height / 18))
        for ($y = 0; $y -lt $height; $y += $stepY) {
            for ($x = 0; $x -lt $width; $x += $stepX) {
                $color = $bitmap.GetPixel($x, $y)
                [void]$colors.Add($color.ToArgb())
                $brightness = [double]$color.GetBrightness()
                $minimumBrightness = [Math]::Min($minimumBrightness, $brightness)
                $maximumBrightness = [Math]::Max($maximumBrightness, $brightness)
            }
        }
        return [pscustomobject]@{
            path = [IO.Path]::GetFullPath($Path)
            sizeBytes = (Get-Item -LiteralPath $Path).Length
            nonUniform = ($colors.Count -gt 8 -and ($maximumBrightness - $minimumBrightness) -gt 0.04)
            width = $width
            height = $height
            sampledColors = $colors.Count
        }
    }
    finally {
        $bitmap.Dispose()
    }
}

function Read-NewLogContent {
    param([string]$Path, [long]$OriginalLength)
    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }
    $content = [IO.File]::ReadAllText($Path)
    if ($OriginalLength -ge $content.Length) {
        return ""
    }
    return $content.Substring([int]$OriginalLength)
}

$portable = [IO.Path]::GetFullPath($PortableRoot).TrimEnd("\")
$executable = Join-Path $portable "FlatShot.exe"
$runtimeLog = Join-Path $portable "data\logs\runtime.log"
$resultFile = [IO.Path]::GetFullPath($ResultPath)
$collectorErrors = [System.Collections.Generic.List[string]]::new()
$process = $null
$window = $null
$endpoints = [pscustomobject]@{ Frontend = $null; Bridge = $null }
$webViewProcesses = @()
$newPythonProcesses = @()
$screenshot = [pscustomobject]@{ path = [IO.Path]::GetFullPath($ScreenshotPath); sizeBytes = 0; nonUniform = $false; width = 0; height = 0 }
$stayedAlive = $false
$exitCodeBeforeCleanup = $null
$gracefulCloseRequested = $false
$forceKillUsed = $false
$listenerPorts = @()
$remainingPorts = @()
$remainingSession = @()
$systemRoot = [Environment]::GetEnvironmentVariable("SystemRoot", "Process").TrimEnd("\")
$cleanPath = @($systemRoot, "$systemRoot\System32", "$systemRoot\System32\Wbem") -join ";"
$logBeforeLength = if (Test-Path -LiteralPath $runtimeLog) { (Get-Item -LiteralPath $runtimeLog).Length } else { 0 }
$launchTime = Get-Date
$preexistingWebView = @(Get-NamedProcessSnapshot -Names @("msedgewebview2") | Select-Object -ExpandProperty Id)
$preexistingPython = @(Get-NamedProcessSnapshot -Names @("python", "pythonw", "py") | Select-Object -ExpandProperty Id)

try {
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw "FlatShot.exe is missing from extracted portable root: $executable"
    }

    $savedEnvironment = @{}
    foreach ($name in @("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "PATH")) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
    }
    try {
        foreach ($name in @("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV")) {
            [Environment]::SetEnvironmentVariable($name, $null, "Process")
        }
        [Environment]::SetEnvironmentVariable("PATH", $cleanPath, "Process")
        $process = Start-Process -FilePath $executable -WorkingDirectory $portable -PassThru
    }
    finally {
        foreach ($name in $savedEnvironment.Keys) {
            [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], "Process")
        }
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Milliseconds 400
        $process.Refresh()
        if ($process.HasExited) {
            $exitCodeBeforeCleanup = $process.ExitCode
            break
        }
        $sessionProcesses = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
        $sessionIds = @($sessionProcesses | Select-Object -ExpandProperty Id)
        if ($process.Id -notin $sessionIds) {
            $sessionIds += $process.Id
        }
        $listenerPorts = @(Get-OwnedListenerPorts -ProcessIds $sessionIds)
        $endpoints = Find-LocalEndpoints -Ports $listenerPorts
        $window = @(Get-VisibleWindows -ProcessIds $sessionIds | Where-Object { $_.Title -match "(?i)FlatShot" } | Select-Object -First 1)
        if ($window.Count -gt 0) {
            $window = $window[0]
        }
        else {
            $window = $null
        }
        $webViewProcesses = @(Get-NamedProcessSnapshot -Names @("msedgewebview2") | Where-Object {
            $_.Id -notin $preexistingWebView -and $_.StartTime -ge $launchTime.AddSeconds(-2)
        })
    } while ((Get-Date) -lt $deadline -and ($null -eq $endpoints.Frontend -or $null -eq $endpoints.Bridge -or $null -eq $window -or $webViewProcesses.Count -eq 0))

    $process.Refresh()
    $stayedAlive = -not $process.HasExited
    if (-not $stayedAlive) {
        $exitCodeBeforeCleanup = $process.ExitCode
    }
    $newPythonProcesses = @(Get-NamedProcessSnapshot -Names @("python", "pythonw", "py") | Where-Object {
        $_.Id -notin $preexistingPython -and $_.StartTime -ge $launchTime.AddSeconds(-2)
    })
    if ($null -ne $window) {
        Start-Sleep -Seconds 3
        $screenshot = Save-WindowScreenshot -Handle $window.Handle -Path $ScreenshotPath
    }
}
catch {
    $collectorErrors.Add($_.Exception.ToString())
}
finally {
    try {
        if ($null -ne $window) {
            $gracefulCloseRequested = [FlatShotNativeWindow]::PostMessage([IntPtr]$window.Handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        }
        if ($null -ne $process -and -not $process.HasExited) {
            if (-not $process.WaitForExit(10000)) {
                $forceKillUsed = $true
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
        $remainingSession = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
        if ($remainingSession.Count -gt 0) {
            $forceKillUsed = $true
            $remainingSession | Stop-Process -Force -ErrorAction SilentlyContinue
        }
        $cleanupDeadline = (Get-Date).AddSeconds(10)
        do {
            Start-Sleep -Milliseconds 250
            $remainingSession = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
            $remainingPorts = @(if ($null -ne $process) { Get-OwnedListenerPorts -ProcessIds @($process.Id) })
        } while ((Get-Date) -lt $cleanupDeadline -and ($remainingSession.Count -gt 0 -or $remainingPorts.Count -gt 0))
    }
    catch {
        $collectorErrors.Add("Cleanup: $($_.Exception)")
    }
}

$newLog = Read-NewLogContent -Path $runtimeLog -OriginalLength $logBeforeLength
$fallbackDetected = $newLog -match "(?m)^\[[^\]]+\] Native desktop window\s*$"
$startupErrors = @()
if ($newLog -match "(?m)^\[[^\]]+\] (Portable launcher|Portable smoke)\s*$") {
    $startupErrors = @($newLog.Trim())
}
$windowMode = if ($fallbackDetected) { "browser fallback" } elseif ($webViewProcesses.Count -gt 0 -and $null -ne $window) { "edgechromium native window" } else { "undetermined" }
$remainingSession = @(Get-NamedProcessSnapshot -Names @("FlatShot") | Where-Object { $_.StartTime -ge $launchTime.AddSeconds(-2) })
$remainingPorts = @(if ($null -ne $process) { Get-OwnedListenerPorts -ProcessIds @($process.Id) })
$resolvedExecutable = [IO.Path]::GetFullPath($executable)
$insidePortable = $resolvedExecutable.StartsWith($portable + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)

$result = [ordered]@{
    schemaVersion = 1
    executable = $resolvedExecutable
    portableRoot = $portable
    launchedAtUtc = $launchTime.ToUniversalTime().ToString("o")
    collectorErrors = @($collectorErrors)
    process = [ordered]@{
        started = ($null -ne $process)
        processId = if ($null -ne $process) { $process.Id } else { $null }
        stayedAlive = $stayedAlive
        exitCodeBeforeCleanup = $exitCodeBeforeCleanup
    }
    environment = [ordered]@{
        pythonHomeCleared = $true
        pythonPathCleared = $true
        virtualEnvCleared = $true
        pathSanitized = $true
        sanitizedPath = $cleanPath
        executableInPortableRoot = $insidePortable
        externalPythonProcesses = @($newPythonProcesses | ForEach-Object { [ordered]@{ name = $_.ProcessName; pid = $_.Id } })
    }
    http = [ordered]@{
        discoveredListenerPorts = @($listenerPorts)
        frontend = if ($null -ne $endpoints.Frontend) { $endpoints.Frontend } else { [ordered]@{ status = $null; url = $null } }
        bridge = if ($null -ne $endpoints.Bridge) { $endpoints.Bridge } else { [ordered]@{ status = $null; url = $null } }
    }
    window = if ($null -ne $window) {
        [ordered]@{ visible = $true; title = $window.Title; handle = $window.Handle; processId = $window.ProcessId }
    } else {
        [ordered]@{ visible = $false; title = ""; handle = 0; processId = $null }
    }
    webView2 = [ordered]@{
        detected = ($webViewProcesses.Count -gt 0)
        temporallyRelated = ($webViewProcesses.Count -gt 0)
        relation = if ($webViewProcesses.Count -gt 0) { "started during FlatShot session" } else { "not detected" }
        pids = @($webViewProcesses | Select-Object -ExpandProperty Id)
    }
    windowMode = $windowMode
    runtimeLog = [ordered]@{
        path = $runtimeLog
        fallbackDetected = $fallbackDetected
        startupErrors = $startupErrors
        newContent = $newLog
    }
    screenshot = $screenshot
    cleanup = [ordered]@{
        gracefulCloseRequested = $gracefulCloseRequested
        forceKillUsed = $forceKillUsed
        flatShotOrphans = @($remainingSession | Select-Object -ExpandProperty Id)
        listenerPortsRemaining = @($remainingPorts)
    }
}

$resultDirectory = Split-Path -Parent $resultFile
if ($resultDirectory) {
    New-Item -ItemType Directory -Path $resultDirectory -Force | Out-Null
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultFile -Encoding utf8
$result | ConvertTo-Json -Depth 8
